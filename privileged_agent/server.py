"""特权代理服务端 V2

V1 (当前): 动作白名单 + 路径白名单 + 速率限制  — 安全判断在 root 进程内
V2 (新增): SO_PEERCRED + Ed25519 验签 + 命令注册表 + SAFE_ENV — 双因子验证

两种协议并存:
  V1: PrivilegedRequest (无 signature 字段) — 向后兼容, 记录警告
  V2: PrivilegedV2Request (有 signature 字段) — 强制验签 + 注册表验证
"""

import grp
import json
import logging
import os
import re
import signal
import socket
import struct
import subprocess
import threading
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any

from privileged_agent.crypto import hash_payload, load_public_key_pem, verify
from privileged_agent.firewall_adapter import (
    PrivilegedAgentActionError,
    add_port_rule,
    get_firewall_status,
    list_firewall_rules,
    list_ssh_logs,
    remove_port_rule,
    set_firewall_enabled,
)
from privileged_agent.models import (
    PrivilegedAction,
    PrivilegedErrorCode,
    PrivilegedRequest,
    PrivilegedResponse,
    PrivilegedV2Request,
)
from privileged_agent.validator import (
    ArgumentValidationError,
    CommandNotRegisteredError,
    CommandRegistry,
    PathNotAllowedError,
)

# ── 最小化安全执行环境 ──
SAFE_ENV: dict[str, str] = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "HOME": "/root",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
}


class RateLimiter:
    """速率限制器 — 防止短时间内同一操作被过度调用。"""

    def __init__(self, max_per_minute: int = 10):
        self._max_per_minute = max_per_minute
        self._lock = threading.Lock()
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def check(self, action: str) -> bool:
        now = time()
        window_start = now - 60
        with self._lock:
            self._buckets[action] = [
                ts for ts in self._buckets[action] if ts > window_start
            ]
            if len(self._buckets[action]) >= self._max_per_minute:
                return False
            self._buckets[action].append(now)
            return True


class PrivilegedAgentServer:
    def __init__(self):
        self.socket_path = os.getenv(
            "NDLM_PRIVILEGED_AGENT_SOCKET",
            "/run/ndlmpanel/privileged-agent.sock",
        )
        self.socket_group = os.getenv("NDLM_PRIVILEGED_AGENT_SOCKET_GROUP", "")
        self.socket_mode = int(os.getenv("NDLM_PRIVILEGED_AGENT_SOCKET_MODE", "660"), 8)

        # Ed25519 公钥路径
        self.public_key_path = os.getenv(
            "NDLM_PRIVILEGED_AGENT_PUBKEY",
            "/etc/nereus/ed25519_pub.pem",
        )

        # 允许连接的 UID 列表（默认: nobody=65534）
        uid_str = os.getenv("NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS", "65534")
        self._allowed_uids = {int(u.strip()) for u in uid_str.split(",") if u.strip()}

        # nonce 过期时间（秒）
        self._nonce_ttl = int(os.getenv("NDLM_PRIVILEGED_AGENT_NONCE_TTL", "300"))

        # 签名时间戳允许偏差（秒）
        self._timestamp_tolerance = int(
            os.getenv("NDLM_PRIVILEGED_AGENT_TIMESTAMP_TOLERANCE", "30")
        )

        self.logger = logging.getLogger("privileged_agent")
        self._server_socket: socket.socket | None = None
        self._running = True

        # ── V1 遗留配置 ──
        self.allowed_service_actions = {"start", "stop", "restart", "enable", "disable"}
        self.allowed_service_names = {"ssh", "sshd", "firewalld", "nginx", "docker"}
        self._allowed_write_paths: list[str] = [
            "/etc/nginx/sites-enabled/",
            "/etc/nginx/conf.d/",
            "/etc/nginx/html/",
            "/var/www/",
            "/var/log/nginx/",
            "/etc/mysql/conf.d/",
            "/etc/docker/",
            "/opt/ndlmpanel/",
        ]
        self._rate_limiter = RateLimiter(max_per_minute=10)

        # ── V2 安全组件 ──
        self._pub_key = self._load_public_key()
        self._registry = CommandRegistry()
        self._nonce_set: dict[str, float] = {}  # nonce_key → expiry_time
        self._nonce_lock = threading.Lock()

    # ════════════════════════════════════════════════════════════
    #  V2: 密钥加载
    # ════════════════════════════════════════════════════════════

    def _load_public_key(self):
        """加载 Ed25519 公钥。文件不存在时发出警告但继续（开发模式）。"""
        path = Path(self.public_key_path)
        if not path.exists():
            self.logger.warning(
                "Ed25519 公钥文件不存在: %s — V2 签名验证将跳过（开发模式）",
                self.public_key_path,
            )
            return None
        try:
            with open(path, "rb") as f:
                key = load_public_key_pem(f.read())
            self.logger.info("Ed25519 公钥已加载: %s", self.public_key_path)
            return key
        except Exception as exc:
            self.logger.error("Ed25519 公钥加载失败: %s", exc)
            return None

    # ════════════════════════════════════════════════════════════
    #  V2: SO_PEERCRED 内核凭证验证
    # ════════════════════════════════════════════════════════════

    def _verify_peercred(self, conn: socket.socket) -> tuple[int, int, int]:
        """通过 SO_PEERCRED 获取连接方的 PID/UID/GID。

        Returns:
            (pid, uid, gid)

        Raises:
            PermissionError: 如果无法获取凭证或 UID 不被允许
        """
        try:
            cred = conn.getsockopt(
                socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
            )
            pid, uid, gid = struct.unpack("3i", cred)
        except OSError as exc:
            raise PermissionError(f"无法获取对端凭证: {exc}")

        if uid not in self._allowed_uids:
            raise PermissionError(
                f"对端 UID={uid} 不在允许列表 {self._allowed_uids} 中"
            )

        return pid, uid, gid

    # ════════════════════════════════════════════════════════════
    #  V2: Nonce 去重与清理
    # ════════════════════════════════════════════════════════════

    def _check_nonce(self, nonce: str) -> bool:
        """检查 nonce 是否已被使用。

        Returns:
            True: nonce 有效（首次出现）
            False: nonce 重复（已被使用过）
        """
        key = f"nonce:{nonce}"
        now = time()
        with self._nonce_lock:
            # 清理过期 nonce
            expired = [k for k, t in self._nonce_set.items() if t < now]
            for k in expired:
                del self._nonce_set[k]

            if key in self._nonce_set:
                return False
            self._nonce_set[key] = now + self._nonce_ttl
            return True

    # ════════════════════════════════════════════════════════════
    #  V2: 签名验证
    # ════════════════════════════════════════════════════════════

    def _verify_signature(self, req: PrivilegedV2Request) -> bool:
        """验证 Ed25519 签名。

        签名内容 = canonical_json({
            "requestId", "command", "args", "args_hash",
            "token_id", "session_id", "timestamp", "nonce",
            "cmd_hash", "script_path", "script_hash"
        })

        Returns:
            True: 验签通过
            False: 验签失败或公钥未配置
        """
        if self._pub_key is None:
            # 开发模式：跳过验签
            self.logger.warning("V2 签名验证跳过（公钥未配置）")
            return True

        sig_payload = {
            "requestId": req.requestId,
            "command": req.command,
            "args": req.args,
            "args_hash": req.args_hash,
            "token_id": req.token_id,
            "session_id": req.session_id,
            "timestamp": req.timestamp,
            "nonce": req.nonce,
            "cmd_hash": req.cmd_hash,
            "script_path": req.script_path,
            "script_hash": req.script_hash,
        }
        return verify(sig_payload, req.signature, self._pub_key)

    def _check_timestamp_freshness(self, timestamp_str: str) -> bool:
        """检查时间戳是否在允许偏差范围内。"""
        try:
            ts = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)
            diff = abs((ts.replace(tzinfo=timezone.utc) - now).total_seconds())
            return diff <= self._timestamp_tolerance
        except (ValueError, TypeError):
            return False

    # ════════════════════════════════════════════════════════════
    #  V2: 命令执行
    # ════════════════════════════════════════════════════════════

    def _dispatch_v2_command(self, command: str, args: list[str]) -> dict[str, Any]:
        """根据命令注册表执行命令。

        V2 通道命令映射到实际 shell 命令执行。
        复杂操作（Nginx SSL, MySQL 等）仍委托 V1 dispatch。
        """
        rule = self._registry.lookup(command)

        # 固定命令行的命令
        if rule.command_line:
            result = self._run_command(rule.command_line.split())
            return {
                "command": command,
                "stdout": (result.stdout or "").strip(),
                "stderr": (result.stderr or "").strip(),
                "returnCode": result.returncode,
            }

        # ── mkdir ──
        if command == "mkdir":
            result = self._run_command(["mkdir"] + args)
            return {"command": command, "args": args, "isCreated": True}

        # ── write_file ──
        if command == "write_file":
            path_str = args[0] if args else ""
            content = args[1] if len(args) > 1 else ""
            path = Path(path_str)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            os.chmod(str(path), 0o644)
            return {"targetPath": str(path), "isSaved": True, "fileSize": len(content)}

        # ── chmod ──
        if command == "chmod":
            self._run_command(["chmod"] + args)
            return {"command": command, "args": args, "isSet": True}

        # ── touch ──
        if command == "touch":
            self._run_command(["touch"] + args)
            return {"command": command, "args": args, "isCreated": True}

        # ── rm ──
        if command == "rm":
            self._run_command(["rm"] + args)
            return {"command": command, "args": args, "isDeleted": True}

        # ── nginx_test / nginx_reload / nginx_restart ──
        if command == "nginx_test":
            result = self._run_command(["nginx", "-t"])
            return {"isValid": True, "stdout": (result.stdout or "").strip()}

        if command == "nginx_reload":
            self._run_command(["systemctl", "reload", "nginx"])
            return {"serviceName": "nginx", "action": "reload", "isReloaded": True}

        if command == "nginx_restart":
            self._run_command(["systemctl", "restart", "nginx"])
            return {"serviceName": "nginx", "action": "restart", "isRestarted": True}

        # ── systemctl ──
        if command == "systemctl":
            self._run_command(["systemctl"] + args)
            return {"command": "systemctl", "args": args, "isExecuted": True}

        # ── firewall_cmd ──
        if command == "firewall_cmd":
            self._run_command(["firewall-cmd"] + args)
            return {"command": "firewall_cmd", "args": args, "isExecuted": True}

        # ── cat / ls ──
        if command == "cat":
            result = self._run_command(["cat"] + args)
            return {"content": result.stdout}

        if command == "ls":
            result = self._run_command(["ls"] + args)
            return {"output": result.stdout}

        # ── certbot ──
        if command == "certbot":
            self._run_command(["certbot"] + args)
            return {"command": "certbot", "args": args, "isExecuted": True}

        # ── mysql_exec ──
        if command == "mysql_exec":
            result = self._run_command(["mysql", "-e", " ".join(args)])
            return {"stdout": (result.stdout or "").strip()}

        # ── docker_daemon ──
        if command == "docker_daemon":
            self._run_command(["systemctl", "restart", "docker"])
            return {"serviceName": "docker", "action": "restart", "isRestarted": True}

                # ── 双通道 Channel 1: 任意命令执行 ──
        if command == "exec_arbitrary_cmd":
            inline_cmd_line = " ".join(args) if args else ""
            self.logger.info("Channel 1 执行任意命令: %s", inline_cmd_line[:120])
            result = self._run_command(["/bin/bash", "-c", inline_cmd_line])
            return {
                "command": command,
                "stdout": (result.stdout or "").strip(),
                "stderr": (result.stderr or "").strip(),
                "returnCode": result.returncode,
            }

        # ── 双通道 Channel 2: 脚本执行 + Trojan Horse 预检 ──
        if command == "exec_arbitrary_script":
            script_path = args[0] if args else ""
            self.logger.info("Channel 2 执行脚本: %s", script_path)
            return self._run_script(script_path)

        # 不支持的 V2 命令
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.UNKNOWN_ACTION,
            f"V2 命令 '{command}' 未实现执行逻辑",
            command,
        )

    # ── Trojan Horse 黑名单正则（脚本内容静态预检用） ──

    _SCRIPT_BLACKLIST: list[tuple[re.Pattern, str]] = [
        (re.compile(r'\beval\b'), "eval 动态执行"),
        (re.compile(r'\bexec\s+\S'), "exec 替换进程"),
        (re.compile(r'\bsource\s+\S'), "source 加载外部脚本"),
        (re.compile(r'\.\s+[a-zA-Z0-9_/]'), ". 点号加载脚本"),
        (re.compile(r'\bcurl\b.*\|\s*(ba|z|k)?sh\b', re.IGNORECASE), "curl 管道执行"),
        (re.compile(r'\bwget\b.*\|\s*(ba|z|k)?sh\b', re.IGNORECASE), "wget 管道执行"),
        (re.compile(r'\|\s*ba[sz]h\b'), "管道传给 bash"),
        (re.compile(r'\|\s*sh\b'), "管道传给 sh"),
        (re.compile(r'\bnc\b\s+.*\-e\b', re.IGNORECASE), "netcat 反弹 shell"),
        (re.compile(r'\bnetcat\b.*\-e\b', re.IGNORECASE), "netcat 反弹 shell"),
    ]

    def _scan_script_content(self, content: str) -> list[dict]:
        """对脚本内容进行静态 Trojan Horse 黑名单扫描。

        Returns:
            命中列表: [{"pattern": "eval 动态执行", "line": 5, "snippet": "eval $cmd"}, ...]
            空列表: 全部通过
        """
        hits = []
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            for pattern, desc in self._SCRIPT_BLACKLIST:
                if pattern.search(line):
                    hits.append({
                        "pattern": desc,
                        "line": i,
                        "snippet": line.strip()[:80],
                    })
                    break  # 每行只报告第一个命中
        return hits

    def _run_script(self, script_path: str) -> dict[str, Any]:
        """执行 Channel 2 脚本，含 Trojan Horse 预检。

        流程:
          1. 确认文件存在
          2. 读取文件，进行 Trojan Horse 正则扫描
          3. 如果命中黑名单，记录日志并拒绝执行
          4. 用 SAFE_ENV 最小环境 + /bin/bash 执行

        Args:
            script_path: 脚本文件的绝对路径

        Returns:
            执行结果 dict

        Raises:
            PrivilegedAgentActionError: 文件不存在 / 黑名单命中 / 执行失败
        """
        path = Path(script_path)
        if not path.exists():
            raise PrivilegedAgentActionError(
                PrivilegedErrorCode.SCRIPT_NOT_FOUND,
                "脚本文件不存在",
                script_path,
            )

        content = path.read_text(encoding="utf-8", errors="ignore")

        # ── Trojan Horse 静态预检 ──
        hits = self._scan_script_content(content)
        if hits:
            hit_details = "; ".join(
                f"L{h['line']}: {h['pattern']} → 「{h['snippet']}」"
                for h in hits
            )
            self.logger.warning(
                "脚本 Trojan Horse 检测命中: %s [%s]", script_path, hit_details
            )
            raise PrivilegedAgentActionError(
                PrivilegedErrorCode.SCRIPT_BLACKLIST_HIT,
                "脚本包含可疑/恶意指令，已拒绝执行",
                hit_details,
            )

        self.logger.info("脚本 Trojan Horse 扫描通过: %s (%d lines)", script_path, len(content.splitlines()))

        # ── 用 SAFE_ENV 最小化环境执行 ──
        result = subprocess.run(
            ["/bin/bash", script_path],
            capture_output=True,
            text=True,
            check=False,
            env=SAFE_ENV,
        )
        return {
            "command": "exec_arbitrary_script",
            "script_path": script_path,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "returnCode": result.returncode,
        }

    # ════════════════════════════════════════════════════════════
    #  V1: 安全的命令执行（SAFE_ENV）
    # ════════════════════════════════════════════════════════════

    def _run_command(
        self,
        command: list[str],
        timeout: int = 10,
    ) -> subprocess.CompletedProcess:
        """使用最小化安全环境执行命令，禁止继承父进程环境变量。"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
                env=SAFE_ENV,  # 不继承父进程环境
            )
        except subprocess.TimeoutExpired as exc:
            raise PrivilegedAgentActionError(
                PrivilegedErrorCode.SERVICE_UNAVAILABLE,
                "系统命令执行超时",
                f"timeout={timeout}s command={' '.join(command)}",
            ) from exc
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()
            raise PrivilegedAgentActionError(
                PrivilegedErrorCode.COMMAND_FAILED,
                "系统命令执行失败",
                details or f"command failed: {' '.join(command)}",
            )
        return result

    def _prepare_socket_path(self):
        socket_file = Path(self.socket_path)
        socket_file.parent.mkdir(parents=True, exist_ok=True)
        if socket_file.exists() or socket_file.is_socket():
            socket_file.unlink()

    def _apply_socket_permissions(self):
        os.chmod(self.socket_path, self.socket_mode)
        if self.socket_group:
            group = grp.getgrnam(self.socket_group)
            os.chown(self.socket_path, 0, group.gr_gid)

    def _handle_signal(self, signum, _frame):
        self.logger.info("received signal %s, shutting down", signum)
        self._running = False
        if self._server_socket is not None:
            self._server_socket.close()

    def _check_path_allowed(self, target_path: str) -> bool:
        """验证目标路径是否在白名单内。"""
        path = Path(target_path).resolve()
        for allowed in self._allowed_write_paths:
            allowed_path = Path(allowed).resolve()
            try:
                path.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        return False

    def _build_error_response(
        self,
        audit_id: str,
        code: PrivilegedErrorCode,
        message: str,
        details: str | None = None,
    ) -> PrivilegedResponse:
        return PrivilegedResponse(
            success=False,
            auditId=audit_id,
            errorCode=code.value,
            errorMessage=message,
            errorDetails=details,
        )

    # ── Nginx 写文件辅助 ──
    def _nginx_save_config(self, target_path: str, content: str) -> dict:
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        os.chmod(str(path), 0o644)
        return {"targetPath": str(path), "isSaved": True}

    def _ensure_symlink(self, target_path: str, site_name: str, layout_type: str):
        if layout_type == "sites-enabled":
            enabled_link = Path("/etc/nginx/sites-enabled") / f"{site_name}.conf"
            if not enabled_link.exists():
                enabled_link.symlink_to(Path(target_path))

    # ── MySQL 辅助 ──
    def _mysql_exec(self, sql: str) -> subprocess.CompletedProcess:
        return self._run_command(["mysql", "-e", sql], timeout=4)

    # ════════════════════════════════════════════════════════════
    #  V1: 原有 dispatch（向后兼容）
    # ════════════════════════════════════════════════════════════

    def _dispatch(self, request: PrivilegedRequest) -> object:
        action = request.action
        payload = request.payload

        if action == PrivilegedAction.FIREWALL_GET_STATUS.value:
            return get_firewall_status()
        if action == PrivilegedAction.FIREWALL_LIST_RULES.value:
            return list_firewall_rules()
        if action == PrivilegedAction.FIREWALL_ADD_PORT_RULE.value:
            return add_port_rule(
                port=int(payload["port"]),
                protocol=str(payload["protocol"]),
                ip_version=int(payload.get("ipVersion", 4)),
                source_ip=payload.get("sourceIp"),
                destination_ip=payload.get("destinationIp"),
                action=int(payload.get("action", 1)),
            )
        if action == PrivilegedAction.FIREWALL_REMOVE_PORT_RULE.value:
            return remove_port_rule(
                port=int(payload["port"]),
                protocol=str(payload["protocol"]),
                ip_version=int(payload.get("ipVersion", 4)),
                source_ip=payload.get("sourceIp"),
                destination_ip=payload.get("destinationIp"),
            )
        if action == PrivilegedAction.FIREWALL_SET_ENABLED.value:
            return set_firewall_enabled(bool(payload["enabled"]))

        if action == PrivilegedAction.NGINX_SAVE_CONFIG_ATOMIC.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            layout_type = str(payload.get("layoutType", ""))
            site_name = str(payload.get("siteName", ""))
            path = Path(target_path)
            backup_content = None
            if path.exists():
                backup_content = path.read_text(encoding="utf-8")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            os.chmod(str(path), 0o644)
            self._ensure_symlink(target_path, site_name, layout_type)
            test_result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True, text=True, check=False,
            )
            if test_result.returncode != 0:
                error_detail = (test_result.stderr or test_result.stdout or "").strip()
                if backup_content is not None:
                    path.write_text(backup_content, encoding="utf-8")
                    self._ensure_symlink(target_path, site_name, layout_type)
                raise PrivilegedAgentActionError(
                    PrivilegedErrorCode.COMMAND_FAILED,
                    "Nginx 配置测试失败，已回滚",
                    error_detail,
                )
            self._run_command(["systemctl", "reload", "nginx"])
            return {"targetPath": str(path), "isSaved": True, "isReloaded": True}

        if action == PrivilegedAction.NGINX_TEST_CONFIG.value:
            result = self._run_command(["nginx", "-t"])
            return {"isValid": True, "stdout": (result.stdout or "").strip(), "stderr": (result.stderr or "").strip()}
        if action == PrivilegedAction.NGINX_RELOAD.value:
            self._run_command(["systemctl", "reload", "nginx"])
            return {"serviceName": "nginx", "action": "reload", "isReloaded": True}
        if action == PrivilegedAction.NGINX_RESTART.value:
            self._run_command(["systemctl", "restart", "nginx"])
            status_result = subprocess.run(
                ["systemctl", "is-active", "nginx"],
                capture_output=True, text=True, check=False,
            )
            return {"serviceName": "nginx", "action": "restart", "isRestarted": True, "currentStatus": (status_result.stdout or "").strip()}

        if action == PrivilegedAction.NGINX_SAVE_CONFIG.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            layout_type = str(payload.get("layoutType", ""))
            site_name = str(payload.get("siteName", ""))
            result_data = self._nginx_save_config(target_path, content)
            self._ensure_symlink(target_path, site_name, layout_type)
            self._run_command(["nginx", "-t"])
            return result_data

        if action == PrivilegedAction.NGINX_DELETE_SITE.value:
            config_path = str(payload["configPath"])
            layout_type = str(payload.get("layoutType", ""))
            site_name = str(payload.get("siteName", ""))
            path = Path(config_path)
            if path.exists():
                path.unlink()
            if layout_type == "sites-enabled":
                enabled_link = Path("/etc/nginx/sites-enabled") / f"{site_name}.conf"
                if enabled_link.exists() or enabled_link.is_symlink():
                    enabled_link.unlink()
            self._run_command(["nginx", "-t"])
            self._run_command(["systemctl", "reload", "nginx"])
            return {"configPath": config_path, "isDeleted": True, "isReloaded": True}

        if action == PrivilegedAction.NGINX_READ_FILE.value:
            file_path = str(payload["filePath"])
            path = Path(file_path)
            if not path.exists():
                raise PrivilegedAgentActionError(PrivilegedErrorCode.SERVICE_UNAVAILABLE, "文件不存在", file_path)
            content = path.read_text(encoding="utf-8", errors="ignore")
            return {"filePath": file_path, "content": content}

        if action == PrivilegedAction.NGINX_LIST_DIR.value:
            dir_path = str(payload["dirPath"])
            path = Path(dir_path)
            if not path.exists():
                return {"dirPath": dir_path, "files": []}
            files = []
            for f in sorted(path.iterdir()):
                if f.is_file() and f.suffix == ".conf":
                    files.append({"name": f.name, "path": str(f), "size": f.stat().st_size})
            return {"dirPath": dir_path, "files": files}

        if action == PrivilegedAction.NGINX_APPLY_SSL.value:
            domain = str(payload["domain"])
            email = str(payload["email"])
            webroot = str(payload["webroot"])
            result = subprocess.run(["which", "certbot"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                result = subprocess.run(["python3", "-m", "certbot", "--version"], capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    raise PrivilegedAgentActionError(PrivilegedErrorCode.SERVICE_UNAVAILABLE, "certbot 未安装", "请先安装 certbot")
            command = ["certbot", "certonly", "--webroot", "-w", webroot, "-d", domain, "--email", email, "--agree-tos", "--non-interactive"]
            self._run_command(command)
            live_dir = Path(f"/etc/letsencrypt/live/{domain}")
            return {"domain": domain, "webroot": webroot, "certPath": str(live_dir / "fullchain.pem"), "keyPath": str(live_dir / "privkey.pem")}

        if action == PrivilegedAction.NGINX_RENEW_SSL.value:
            domain = str(payload["domain"])
            self._run_command(["certbot", "renew", "--cert-name", domain, "--non-interactive"])
            self._run_command(["nginx", "-t"])
            self._run_command(["systemctl", "reload", "nginx"])
            return {"domain": domain, "isRenewed": True, "isReloaded": True}

        if action == PrivilegedAction.NGINX_CONFIG_SSL.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            self._nginx_save_config(target_path, content)
            self._run_command(["nginx", "-t"])
            self._run_command(["systemctl", "reload", "nginx"])
            return {"targetPath": target_path, "isSslConfigured": True, "isReloaded": True}

        if action == PrivilegedAction.SSH_LIST_LOGS.value:
            return list_ssh_logs(int(payload.get("maxLines", 500)))

        if action == PrivilegedAction.SERVICE_SET_STATE.value:
            service_name = str(payload["serviceName"])
            service_action = str(payload["action"])
            if service_action not in self.allowed_service_actions:
                raise PrivilegedAgentActionError(PrivilegedErrorCode.INVALID_REQUEST, "不支持的服务动作", service_action)
            if service_name not in self.allowed_service_names:
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "当前不允许操作该系统服务", service_name)
            subprocess.run(["systemctl", service_action, service_name], capture_output=True, text=True, check=True)
            status_result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True, check=False)
            return {"serviceName": service_name, "action": service_action, "currentStatus": (status_result.stdout or "").strip()}

        if action == PrivilegedAction.DOCKER_SET_DAEMON_CONFIG.value:
            target_path = str(payload.get("daemonJsonPath", "/etc/docker/daemon.json"))
            content = str(payload.get("content", "{}"))
            path = Path(target_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            os.chmod(str(path), 0o644)
            self._run_command(["systemctl", "restart", "docker"])
            return {"daemonJsonPath": str(path), "isSet": True, "isRestarted": True}

        if action == PrivilegedAction.MYSQL_CREATE_DATABASE.value:
            db_name = str(payload["dbName"])
            sql = f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
            self._mysql_exec(sql)
            return {"dbName": db_name, "charset": "utf8mb4", "isCreated": True}

        if action == PrivilegedAction.MYSQL_CREATE_USER.value:
            db_name = str(payload["dbName"])
            username = str(payload["username"])
            password = str(payload["password"])
            escaped_password = password.replace("\\", "\\\\").replace("'", "\\'")
            sql = (
                f"CREATE USER IF NOT EXISTS '{username}'@'localhost' "
                f"IDENTIFIED BY '{escaped_password}'; "
                f"ALTER USER '{username}'@'localhost' IDENTIFIED BY '{escaped_password}'; "
                f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{username}'@'localhost'; "
                "FLUSH PRIVILEGES;"
            )
            self._mysql_exec(sql)
            return {"dbName": db_name, "username": username, "host": "localhost", "privileges": "ALL PRIVILEGES", "isGranted": True, "isCreated": True}

        if action == PrivilegedAction.MYSQL_GET_DATABASE_LIST.value:
            result = self._mysql_exec("SHOW DATABASES;")
            dbs = [line.strip() for line in result.stdout.strip().splitlines() if line.strip() and not line.strip().startswith("Database")]
            return {"databases": dbs}

        if action == PrivilegedAction.MYSQL_EXEC.value:
            sql = str(payload["sql"])
            result = self._mysql_exec(sql)
            return {"stdout": (result.stdout or "").strip(), "stderr": (result.stderr or "").strip()}

        if action == PrivilegedAction.FILE_WRITE_TO_ALLOWED.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            mode = int(payload.get("mode", 0o644))
            if not self._rate_limiter.check(action):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "操作过于频繁，请稍后再试", f"action={action}")
            if not self._check_path_allowed(target_path):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "路径不在允许写入的白名单中", target_path)
            path = Path(target_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            os.chmod(str(path), mode)
            return {"targetPath": str(path), "isSaved": True}

        if action == PrivilegedAction.FILE_CREATE_DIRECTORY.value:
            target_path = str(payload["targetPath"])
            mode = int(payload.get("mode", 0o755))
            if not self._rate_limiter.check(action):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "操作过于频繁，请稍后再试", f"action={action}")
            if not self._check_path_allowed(target_path):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "路径不在允许写入的白名单中", target_path)
            path = Path(target_path)
            path.mkdir(parents=True, exist_ok=True)
            os.chmod(str(path), mode)
            return {"targetPath": str(path), "isCreated": True}

        if action == PrivilegedAction.FILE_SET_PERMISSIONS.value:
            target_path = str(payload["targetPath"])
            mode = int(payload["mode"])
            if not self._rate_limiter.check(action):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "操作过于频繁，请稍后再试", f"action={action}")
            if not self._check_path_allowed(target_path):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "路径不在允许写入的白名单中", target_path)
            os.chmod(target_path, mode)
            return {"targetPath": target_path, "mode": mode, "isSet": True}

        if action == PrivilegedAction.NGINX_WRITE_STATIC_FILE.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            if not self._rate_limiter.check(action):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "操作过于频繁，请稍后再试", f"action={action}")
            nginx_html = Path("/etc/nginx/html/").resolve()
            var_www = Path("/var/www/").resolve()
            target = Path(target_path).resolve()
            allowed = False
            try:
                target.relative_to(nginx_html)
                allowed = True
            except ValueError:
                pass
            if not allowed:
                try:
                    target.relative_to(var_www)
                    allowed = True
                except ValueError:
                    pass
            if not allowed:
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, f"nginx 静态文件只能写入 {nginx_html} 或 {var_www}", target_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            os.chmod(str(target), 0o644)
            return {"targetPath": str(target), "isSaved": True, "fileSize": len(content)}

        if action == PrivilegedAction.EXEC_SCRIPT.value:
            script_path = str(payload["scriptPath"])
            script_args = payload.get("args", [])
            timeout_sec = int(payload.get("timeout", 60))
            if not self._rate_limiter.check(action):
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, "操作过于频繁，请稍后再试", f"action={action}")
            # 统一新旧入口的脚本目录，禁止旧版 /opt/ndlmpanel/scripts/。
            allowed_script_dirs = ["/opt/ndlmpanel/tmp_scripts/"]
            script = Path(script_path).resolve()
            allowed = False
            for script_dir in allowed_script_dirs:
                try:
                    script.relative_to(Path(script_dir).resolve())
                    allowed = True
                    break
                except ValueError:
                    continue
            if not allowed:
                raise PrivilegedAgentActionError(PrivilegedErrorCode.PERMISSION_DENIED, f"只允许执行 {allowed_script_dirs} 下的预定义脚本", script_path)
            if not script.exists() or not script.is_file():
                raise PrivilegedAgentActionError(PrivilegedErrorCode.SERVICE_UNAVAILABLE, "脚本文件不存在", script_path)
            result = subprocess.run(
                [script_path] + list(script_args),
                capture_output=True, text=True, check=False,
                timeout=timeout_sec,
                env=SAFE_ENV,
            )
            return {"scriptPath": script_path, "returnCode": result.returncode, "stdout": (result.stdout or "").strip(), "stderr": (result.stderr or "").strip()}

        raise PrivilegedAgentActionError(PrivilegedErrorCode.UNKNOWN_ACTION, "不支持的特权动作", action)

    # ════════════════════════════════════════════════════════════
    #  V2: 客户端处理（SO_PEERCRED + 签名验证 + 注册表 + 执行）
    # ════════════════════════════════════════════════════════════

    def _handle_v2(self, raw_data: dict, conn: socket.socket, audit_id: str) -> PrivilegedResponse:
        """处理 V2 签名请求。

        完整安全链: peercred → 签名 → 新鲜度 → nonce → 注册表 → args_hash → 执行
        """
        # 1. SO_PEERCRED 内核级身份验证
        try:
            pid, uid, gid = self._verify_peercred(conn)
        except PermissionError as exc:
            self.logger.warning("audit_id=%s peercred_denied: %s", audit_id, exc)
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.PEER_UID_DENIED,
                "连接方不在允许的 UID 列表中", str(exc),
            )

        # 2. 解析 V2 请求
        try:
            req = PrivilegedV2Request(**raw_data)
        except Exception as exc:
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.INVALID_REQUEST,
                "V2 请求格式非法", str(exc),
            )

        # 3. 验证 Ed25519 签名
        if not self._verify_signature(req):
            self.logger.warning(
                "audit_id=%s uid=%d command=%s signature_invalid",
                audit_id, uid, req.command,
            )
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.SIGNATURE_INVALID,
                "Ed25519 签名验证失败",
            )

        # 4. 验证时间戳新鲜度
        if not self._check_timestamp_freshness(req.timestamp):
            self.logger.warning(
                "audit_id=%s uid=%d command=%s timestamp_expired ts=%s",
                audit_id, uid, req.command, req.timestamp,
            )
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.SIGNATURE_EXPIRED,
                "请求时间戳已过期或偏差过大",
            )

        # 5. Nonce 去重
        if not self._check_nonce(req.nonce):
            self.logger.warning(
                "audit_id=%s uid=%d command=%s nonce_replay nonce=%s",
                audit_id, uid, req.command, req.nonce,
            )
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.NONCE_REPLAY,
                "Nonce 重复（可能的重放攻击）",
            )

        # 6. 命令注册表验证
        try:
            rule = self._registry.lookup(req.command)
            rule.validate(req.args)
        except CommandNotRegisteredError as exc:
            self.logger.warning("audit_id=%s uid=%d command=%s not_registered", audit_id, uid, req.command)
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.COMMAND_NOT_REGISTERED,
                f"命令 '{req.command}' 不在注册表中", str(exc),
            )
        except (ArgumentValidationError, PathNotAllowedError) as exc:
            self.logger.warning("audit_id=%s uid=%d command=%s args_invalid: %s", audit_id, uid, req.command, exc)
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.ARGS_INVALID,
                f"命令参数校验失败", str(exc),
            )

        # 7. Hash 验证（根据命令类型选择验证方式）
        if req.token_id:
            if req.command == "exec_arbitrary_cmd":
                # Channel 1: 验证 cmd_hash — 命令字符串的完整 Hash
                cmd_line = " ".join(req.args)
                computed_cmd_hash = hash_payload({"cmd": cmd_line})
                if not req.cmd_hash or computed_cmd_hash != req.cmd_hash:
                    self.logger.warning(
                        "audit_id=%s uid=%d command=exec_arbitrary_cmd cmd_hash_mismatch "
                        "expected=%s computed=%s",
                        audit_id, uid, req.cmd_hash, computed_cmd_hash,
                    )
                    return self._build_error_response(
                        audit_id, PrivilegedErrorCode.CMD_HASH_MISMATCH,
                        "命令 Hash 不匹配（执行命令与审批时不一致）",
                    )
            elif req.command == "exec_arbitrary_script":
                # Channel 2: 验证 script_hash — 脚本文件内容的 Hash
                try:
                    script_content = Path(req.script_path).read_text(
                        encoding="utf-8", errors="ignore"
                    )
                    computed_script_hash = hash_payload({"content": script_content})
                except (OSError, FileNotFoundError):
                    return self._build_error_response(
                        audit_id, PrivilegedErrorCode.SCRIPT_NOT_FOUND,
                        "脚本文件不存在",
                        req.script_path,
                    )
                if req.script_hash and computed_script_hash != req.script_hash:
                    self.logger.warning(
                        "audit_id=%s uid=%d command=exec_arbitrary_script script_hash_mismatch "
                        "expected=%s computed=%s",
                        audit_id, uid, req.script_hash, computed_script_hash,
                    )
                    return self._build_error_response(
                        audit_id, PrivilegedErrorCode.SCRIPT_HASH_MISMATCH,
                        "脚本 Hash 不匹配（执行脚本与审批时不一致）",
                    )
            else:
                # 标准 V2 命令: 验证 args_hash
                if req.args_hash:
                    computed_hash = hash_payload({"args": req.args})
                    if computed_hash != req.args_hash:
                        self.logger.warning(
                            "audit_id=%s uid=%d command=%s args_hash_mismatch "
                            "expected=%s computed=%s",
                            audit_id, uid, req.command, req.args_hash, computed_hash,
                        )
                        return self._build_error_response(
                            audit_id, PrivilegedErrorCode.ARGS_HASH_MISMATCH,
                            "参数 Hash 不匹配（请求参数与审批时不一致）",
                        )

        # 8. 执行命令
        try:
            data = self._dispatch_v2_command(req.command, req.args)
            response = PrivilegedResponse(success=True, auditId=audit_id, data=data)
            self.logger.info(
                "audit_id=%s uid=%d command=%s args=%s success=true",
                audit_id, uid, req.command, req.args,
            )
            return response
        except PrivilegedAgentActionError as exc:
            self.logger.warning(
                "audit_id=%s uid=%d command=%s code=%s message=%s",
                audit_id, uid, req.command, exc.code.value, exc.message,
            )
            return self._build_error_response(audit_id, exc.code, exc.message, exc.details)
        except Exception as exc:
            self.logger.exception("audit_id=%s uid=%d command=%s exec_error", audit_id, uid, req.command)
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.INTERNAL_ERROR,
                "命令执行内部错误", str(exc),
            )

    def _handle_v1(self, raw_data: dict, audit_id: str) -> PrivilegedResponse:
        """处理 V1 遗留请求（向后兼容）。"""
        self.logger.warning(
            "audit_id=%s V1 协议请求（无签名）— 建议迁移到 V2",
            audit_id,
        )
        try:
            request = PrivilegedRequest(**raw_data)
            data = self._dispatch(request)
            response = PrivilegedResponse(success=True, auditId=audit_id, data=data)
            self.logger.info(
                "audit_id=%s source=%s action=%s success=true (V1 legacy)",
                audit_id,
                request.caller.source if request.caller else "?",
                request.action,
            )
            return response
        except PrivilegedAgentActionError as exc:
            self.logger.warning(
                "audit_id=%s success=false code=%s message=%s (V1)",
                audit_id, exc.code.value, exc.message,
            )
            return self._build_error_response(audit_id, exc.code, exc.message, exc.details)
        except Exception as exc:
            self.logger.exception("audit_id=%s V1 unhandled_error", audit_id)
            return self._build_error_response(
                audit_id, PrivilegedErrorCode.INTERNAL_ERROR,
                "特权代理内部错误", str(exc),
            )

    def _serve_client(self, conn: socket.socket):
        with conn:
            raw = b""
            while not raw.endswith(b"\n"):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                raw += chunk

            audit_id = str(uuid.uuid4())
            if not raw:
                response = self._build_error_response(
                    audit_id, PrivilegedErrorCode.INVALID_REQUEST, "空请求",
                )
                conn.sendall((response.model_dump_json() + "\n").encode("utf-8"))
                return

            try:
                raw_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                response = self._build_error_response(
                    audit_id, PrivilegedErrorCode.INVALID_REQUEST,
                    "JSON 解析失败", str(exc),
                )
                conn.sendall((response.model_dump_json() + "\n").encode("utf-8"))
                return

            # debug: 看服务端收到了什么
            self.logger.warning(
                "serve_client: raw_keys=%s has_signature=%s",
                list(raw_data.keys()) if isinstance(raw_data, dict) else "not_dict",
                "signature" in raw_data if isinstance(raw_data, dict) else False,
            )

            # 自动识别协议版本
            if isinstance(raw_data, dict) and "signature" in raw_data:
                # V2: 带签名的请求 → 完整安全验证
                response = self._handle_v2(raw_data, conn, audit_id)
            else:
                # V1: 向后兼容
                response = self._handle_v1(raw_data, audit_id)

            conn.sendall((response.model_dump_json() + "\n").encode("utf-8"))

    def serve_forever(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        if os.geteuid() != 0:
            raise RuntimeError("privileged agent must run as root")

        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        self._prepare_socket_path()
        server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_socket = server_socket
        server_socket.bind(self.socket_path)
        self._apply_socket_permissions()
        server_socket.listen(32)
        self.logger.info(
            "privileged agent V2 listening on %s (allowed_uids=%s, pubkey=%s)",
            self.socket_path,
            self._allowed_uids,
            "loaded" if self._pub_key else "none (dev mode)",
        )

        try:
            while self._running:
                try:
                    conn, _ = server_socket.accept()
                except OSError:
                    if self._running:
                        raise
                    break
                self._serve_client(conn)
        finally:
            server_socket.close()
            try:
                Path(self.socket_path).unlink(missing_ok=True)
            except Exception:
                pass


def main():
    server = PrivilegedAgentServer()
    server.serve_forever()


if __name__ == "__main__":
    main()
