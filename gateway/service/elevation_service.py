"""特权码（Elevation Code）生命周期管理。

纯内存状态机：code → pending → approved → token issued → consumed/expired
Hash 和 token 坚决不落盘，TTL 后自动销毁。
"""

import json
import logging
import os
import secrets
import threading
import uuid
from datetime import datetime, timezone
from time import time
from typing import Any, Optional

from gateway.Singleton import Singleton, singletonInit
from privileged_agent.crypto import (
    dump_private_key_pem,
    generate_keypair,
    hash_payload,
    load_private_key_pem,
    sign,
)

logger = logging.getLogger("elevation_service")

# ── 状态常量 ──
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_EXPIRED = "expired"
STATUS_CONSUMED = "consumed"


class ElevationCodeEntry:
    """一个特权码的完整生命周期状态。"""

    def __init__(
        self,
        code: str,
        session_id: str,
        commands: list[dict[str, Any]],
        reason: str,
        ttl_seconds: int = 3600,
        max_ops: int = 10,
        inline_cmd: str | None = None,
        inline_cmd_hash: str | None = None,
        script_path: str | None = None,
        script_hash: str | None = None,
        request_type: str = "privileged",
        task_id: int | None = None,
        approval_policy: dict[str, Any] | None = None,
    ):
        self.code = code
        self.session_id = session_id
        self.commands = commands  # [{"command": "mkdir", "args": [...]}, ...]
        self.reason = reason
        self.request_type = request_type
        self.task_id = task_id
        self.approval_policy = approval_policy or {}
        self.status = STATUS_PENDING
        self.ttl_seconds = ttl_seconds
        self.max_ops = max_ops
        self.ops_used = 0
        self.requested_at = time()
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[float] = None
        self.token_id: Optional[str] = None
        self.reject_reason: Optional[str] = None
        # 双通道（Channel 1）: 自由命令字符串 + Hash
        self.inline_cmd: str | None = inline_cmd
        self.inline_cmd_hash: str | None = inline_cmd_hash
        # 双通道（Channel 2）: 脚本文件路径 + Hash
        self.script_path: str | None = script_path
        self.script_hash: str | None = script_hash

    @property
    def is_expired(self) -> bool:
        return time() > self.requested_at + self.ttl_seconds

    @property
    def is_exhausted(self) -> bool:
        return self.ops_used >= self.max_ops

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "session_id": self.session_id,
            "request_type": self.request_type,
            "task_id": self.task_id,
            "approval_policy": self.approval_policy,
            "commands": self.commands,
            "reason": self.reason,
            "status": self.status,
            "ttl_seconds": self.ttl_seconds,
            "max_ops": self.max_ops,
            "ops_used": self.ops_used,
            "requested_at": datetime.fromtimestamp(self.requested_at, tz=timezone.utc).isoformat(),
            "approved_by": self.approved_by,
            "approved_at": datetime.fromtimestamp(self.approved_at, tz=timezone.utc).isoformat()
            if self.approved_at else None,
            "token_id": self.token_id,
            "expired": self.is_expired,
            "exhausted": self.is_exhausted,
            "inline_cmd": self.inline_cmd,
            "inline_cmd_hash": self.inline_cmd_hash,
            "script_path": self.script_path,
            "script_hash": self.script_hash,
        }


class JITToken:
    """JIT (Just-In-Time) token — 绑定 session + 命令列表 + TTL + 次数。"""

    def __init__(
        self,
        token_id: str,
        code_entry: ElevationCodeEntry,
    ):
        self.token_id = token_id
        self.code = code_entry.code
        self.session_id = code_entry.session_id
        # 绑定命令及其 args_hash
        self.allowed_commands: list[dict[str, Any]] = []
        for cmd in code_entry.commands:
            self.allowed_commands.append({
                "command": cmd["command"],
                "args_hash": hash_payload({"args": cmd.get("args", [])}),
            })
        self.max_ops = code_entry.max_ops
        self.ops_used = 0
        self.issued_at = code_entry.approved_at or time()
        self.ttl_seconds = code_entry.ttl_seconds
        # 双通道
        self.inline_cmd: str | None = code_entry.inline_cmd
        self.inline_cmd_hash: str | None = code_entry.inline_cmd_hash
        self.script_path: str | None = code_entry.script_path
        self.script_hash: str | None = code_entry.script_hash

    @property
    def is_expired(self) -> bool:
        return time() > self.issued_at + self.ttl_seconds

    @property
    def is_exhausted(self) -> bool:
        return self.ops_used >= self.max_ops

    def to_dict(self) -> dict:
        return {
            "token_id": self.token_id,
            "session_id": self.session_id,
            "allowed_commands": self.allowed_commands,
            "max_ops": self.max_ops,
            "ops_used": self.ops_used,
            "issued_at": datetime.fromtimestamp(self.issued_at, tz=timezone.utc).isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "expired": self.is_expired,
            "exhausted": self.is_exhausted,
        }


class ElevationService(Singleton):
    """特权码生命周期管理。

    所有状态纯内存，不写数据库。TTL 到期自动清理。
    """

    @singletonInit
    def __init__(self, priv_key_path: Optional[str] = None):
        self._priv_key_path = priv_key_path or os.getenv(
            "NDLM_ELEVATION_PRIVKEY",
            "/etc/nereus/ed25519_priv.pem",
        )
        self._priv_key = self._load_priv_key()
        self._lock = threading.Lock()
        self._codes: dict[str, ElevationCodeEntry] = {}  # code → entry
        self._tokens: dict[str, JITToken] = {}  # token_id → token
        self._sessions: dict[str, str] = {}  # session_id → latest code

        # 启动后台清理协程（TTL 过期）
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        logger.info("ElevationService 已初始化 (privkey=%s)", self._priv_key_path)

    def _load_priv_key(self):
        path = os.path.expanduser(self._priv_key_path)
        if not os.path.exists(path):
            logger.warning("Ed25519 私钥不存在: %s — 自动生成开发密钥", path)
            kp = generate_keypair()
            priv_pem = dump_private_key_pem(kp.priv)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(priv_pem)
            os.chmod(path, 0o400)
            logger.info("开发密钥已生成: %s", path)
            return kp.priv
        with open(path, "rb") as f:
            return load_private_key_pem(f.read())

    # ── Code 生成 ──

    def generate_code(
        self,
        session_id: str,
        commands: list[dict[str, Any]],
        reason: str,
        ttl_seconds: int = 3600,
        max_ops: int = 10,
        code: str | None = None,
        inline_cmd: str | None = None,
        inline_cmd_hash: str | None = None,
        script_path: str | None = None,
        script_hash: str | None = None,
        request_type: str = "privileged",
        task_id: int | None = None,
        approval_policy: dict[str, Any] | None = None,
    ) -> ElevationCodeEntry:
        """生成一个新的特权码。

        Args:
            session_id: Agent session ID
            commands: [{"command": "mkdir", "args": ["-p", "/var/www/test"]}, ...]
            reason: 申请原因说明
            ttl_seconds: 有效期（秒），默认 1 小时
            max_ops: 最大执行次数，默认 10
            code: 外部传入的 code 字符串（默认 None，自动生成）
            inline_cmd: Channel 1 — 自由命令字符串
            inline_cmd_hash: Channel 1 — SHA256(inline_cmd)
            script_path: Channel 2 — 脚本文件路径
            script_hash: Channel 2 — SHA256(script_content)
            request_type: privileged 或 scheduled_task_policy

        Returns:
            ElevationCodeEntry (status=pending)
        """
        # 支持外部传入 code（用于 _handleElevationResult 同步 MCP 子进程生成的 code）
        # 如果不传则自动生成
        if code is None:
            code = self._generate_code_string()
        entry = ElevationCodeEntry(
            code=code,
            session_id=session_id,
            commands=commands,
            reason=reason,
            ttl_seconds=ttl_seconds,
            max_ops=max_ops,
            inline_cmd=inline_cmd,
            inline_cmd_hash=inline_cmd_hash,
            script_path=script_path,
            script_hash=script_hash,
            request_type=request_type,
            task_id=task_id,
            approval_policy=approval_policy,
        )
        with self._lock:
            # 如果该 session 已有 pending code，标记为过期
            old_code = self._sessions.get(session_id)
            if old_code and old_code in self._codes:
                old_entry = self._codes[old_code]
                if old_entry.status == STATUS_PENDING:
                    old_entry.status = STATUS_EXPIRED
                    logger.info(
                        "session=%s 旧 code=%s 已过期（新码生成）",
                        session_id, old_code,
                    )
            self._codes[code] = entry
            self._sessions[session_id] = code

        logger.info(
            "code=%s type=%s session=%s task=%s commands=%d reason=%s ttl=%d max_ops=%d",
            code, request_type, session_id, task_id, len(commands), reason[:50], ttl_seconds, max_ops,
        )
        return entry

    def _generate_code_string(self) -> str:
        """生成 8 位字母数字 code，格式: NGA7-K3X9"""
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去掉易混淆的 0/O/1/I
        part1 = "".join(secrets.choice(chars) for _ in range(4))
        part2 = "".join(secrets.choice(chars) for _ in range(4))
        return f"{part1}-{part2}"

    # ── Code 查询 ──

    def get_code(self, code: str) -> Optional[ElevationCodeEntry]:
        """查询 code 信息。"""
        entry = self._codes.get(code)
        if entry is None:
            return None
        # 检查是否过期
        if entry.is_expired and entry.status in (STATUS_PENDING, STATUS_APPROVED):
            entry.status = STATUS_EXPIRED
        return entry

    def list_pending(self) -> list[dict]:
        """列出所有待审批的 code。"""
        result = []
        with self._lock:
            for code, entry in self._codes.items():
                if entry.status == STATUS_PENDING and not entry.is_expired:
                    result.append(entry.to_dict())
        return result

    def list_history(self, limit: int = 50) -> list[dict]:
        """列出最近的审批历史。"""
        entries = list(self._codes.values())
        # 过滤掉 pending + expired 的，只显示被处理过的
        processed = [e for e in entries if e.status != STATUS_PENDING or e.is_expired]
        processed.sort(key=lambda e: e.requested_at, reverse=True)
        return [e.to_dict() for e in processed[:limit]]

    # ── Code 审批 ──

    def approve_code(self, code: str, approved_by: str) -> Optional[JITToken]:
        """批准一个 pending 的 code，签发 JIT token。

        Returns:
            JITToken 签发成功
            None     code 不存在或状态不是 pending
        """
        with self._lock:
            entry = self._codes.get(code)
            if entry is None:
                logger.warning("approve failed: code=%s not found", code)
                return None
            if entry.status != STATUS_PENDING:
                logger.warning(
                    "approve failed: code=%s status=%s (expected pending)",
                    code, entry.status,
                )
                return None
            if entry.is_expired:
                entry.status = STATUS_EXPIRED
                logger.warning("approve failed: code=%s expired", code)
                return None

            # 签发 token
            token_id = str(uuid.uuid4())
            entry.status = STATUS_APPROVED
            entry.approved_by = approved_by
            entry.approved_at = time()
            entry.token_id = token_id

            token = JITToken(token_id=token_id, code_entry=entry)
            self._tokens[token_id] = token

        logger.info(
            "approved code=%s by=%s token=%s commands=%d max_ops=%d",
            code, approved_by, token_id, len(entry.commands), entry.max_ops,
        )
        return token

    def reject_code(self, code: str, reason: str):
        """拒绝一个 pending 的 code。"""
        with self._lock:
            entry = self._codes.get(code)
            if entry is None:
                return
            if entry.status != STATUS_PENDING:
                return
            entry.status = STATUS_REJECTED
            entry.reject_reason = reason
        logger.info("rejected code=%s reason=%s", code, reason[:100])

    def revoke_token(self, token_id: str) -> bool:
        """吊销一个已签发的 token。"""
        with self._lock:
            token = self._tokens.get(token_id)
            if token is None:
                return False
            # 强制耗尽
            token.ops_used = token.max_ops
            return True

    # ── Token 验证与签名 ──

    def create_signed_request(
        self,
        token_id: str,
        command_index: int,
        actual_args: list[str],
        session_id: str,
    ) -> Optional[dict[str, Any]]:
        """用 token 换取签名后的请求。

        这是核心安全方法：
        1. 验证 token 有效
        2. 验证 command_index 在 allowed 列表内
        3. 验证 args_hash 匹配
        4. 扣减 ops_used
        5. 生成 Ed25519 signed_request

        Args:
            token_id: JIT token ID
            command_index: 命令在 allowed_commands 中的索引
            actual_args: 实际执行的参数
            session_id: Agent session ID

        Returns:
            signed_request dict (含 signature)，可直接发给特权代理
            None 验证失败
        """
        with self._lock:
            # debug 日志写文件（不碰 stdout，避免污染 MCP 通信）
            _debug_path = os.environ.get("NDLM_DEBUG_LOG", "/tmp/elevation_debug.log")
            _debug_lines = [
                f"[DEBUG] create_signed_request: token_id={token_id} command_index={command_index} actual_args={actual_args} session_id={session_id}",
                f"[DEBUG] _tokens keys: {list(self._tokens.keys())}",
            ]

            token = self._tokens.get(token_id)
            if token is None:
                _debug_lines.append(f"[DEBUG] ❌ ① token not found! token_id={token_id}")
                logger.warning("token=%s not found", token_id)
                try:
                    with open(_debug_path, "a") as _f:
                        _f.write("\n".join(_debug_lines) + "\n")
                except Exception:
                    pass
                return None
            _debug_lines.append(f"[DEBUG] ✅ ① token found, session_id={token.session_id} expired={token.is_expired} ops_used={token.ops_used}/{token.max_ops}")

            if token.is_expired:
                _debug_lines.append(f"[DEBUG] ❌ ② token expired! issued_at={token.issued_at} ttl={token.ttl_seconds}")
                logger.warning("token=%s expired", token_id)
                try:
                    with open(_debug_path, "a") as _f:
                        _f.write("\n".join(_debug_lines) + "\n")
                except Exception:
                    pass
                return None
            _debug_lines.append("[DEBUG] ✅ ② token not expired")

            if token.is_exhausted:
                _debug_lines.append(f"[DEBUG] ❌ ③ token exhausted! ops_used={token.ops_used}/{token.max_ops}")
                logger.warning("token=%s exhausted (%d/%d)", token_id, token.ops_used, token.max_ops)
                try:
                    with open(_debug_path, "a") as _f:
                        _f.write("\n".join(_debug_lines) + "\n")
                except Exception:
                    pass
                return None
            _debug_lines.append("[DEBUG] ✅ ③ token not exhausted")

            if token.session_id != session_id:
                _debug_lines.append(f"[DEBUG] ❌ ④ session mismatch! expected={token.session_id} got={session_id}")
                logger.warning(
                    "token=%s session mismatch (expected=%s, got=%s)",
                    token_id, token.session_id, session_id,
                )
                try:
                    with open(_debug_path, "a") as _f:
                        _f.write("\n".join(_debug_lines) + "\n")
                except Exception:
                    pass
                return None
            _debug_lines.append("[DEBUG] ✅ ④ session match")

            # 验证 command_index
            if command_index < 0 or command_index >= len(token.allowed_commands):
                _debug_lines.append(f"[DEBUG] ❌ ⑤ command_index out of range! index={command_index} allowed={len(token.allowed_commands)}")
                logger.warning(
                    "token=%s command_index=%d out of range (0-%d)",
                    token_id, command_index, len(token.allowed_commands) - 1,
                )
                try:
                    with open(_debug_path, "a") as _f:
                        _f.write("\n".join(_debug_lines) + "\n")
                except Exception:
                    pass
                return None
            _debug_lines.append(f"[DEBUG] ✅ ⑤ command_index valid, allowed_commands={token.allowed_commands}")

            allowed_cmd = token.allowed_commands[command_index]
            command_name = allowed_cmd["command"]

            # ── 双通道 hash 验证 ──
            cmd_hash = None
            script_hash = None
            if command_name == "exec_arbitrary_cmd":
                # Channel 1: actual_args[0] 是完整命令字符串
                inline_cmd = " ".join(actual_args) if actual_args else ""
                cmd_hash = hash_payload({"cmd": inline_cmd})
                expected_hash = token.inline_cmd_hash or ""
                if cmd_hash != expected_hash:
                    _debug_lines.append(f"[DEBUG] ❌ ⑥a cmd_hash mismatch! command={command_name} expected={expected_hash} actual={cmd_hash}")
                    logger.warning("token=%s cmd_hash mismatch", token_id)
                    try:
                        with open(_debug_path, "a") as _f:
                            _f.write("\n".join(_debug_lines) + "\n")
                    except Exception:
                        pass
                    return None
                _debug_lines.append("[DEBUG] ✅ ⑥a cmd_hash match")
            elif command_name == "exec_arbitrary_script":
                # Channel 2: actual_args[0] 是脚本路径
                script_path = actual_args[0] if actual_args else ""
                script_hash = token.script_hash or ""
                _debug_lines.append(f"[DEBUG] ✅ ⑥b script_path={script_path} script_hash={script_hash[:16]}…")
            else:
                # 标准 V2 命令: 验证 args_hash
                expected_hash = allowed_cmd["args_hash"]
                actual_hash = hash_payload({"args": actual_args})
                if actual_hash != expected_hash:
                    _debug_lines.append(f"[DEBUG] ❌ ⑥ args_hash mismatch! command={command_name} expected={expected_hash} actual={actual_hash} args={actual_args}")
                    logger.warning(
                        "token=%s command=%s args_hash mismatch (expected=%s, actual=%s)",
                        token_id, command_name, expected_hash, actual_hash,
                    )
                    try:
                        with open(_debug_path, "a") as _f:
                            _f.write("\n".join(_debug_lines) + "\n")
                    except Exception:
                        pass
                    return None
                _debug_lines.append("[DEBUG] ✅ ⑥ args_hash match")

            try:
                with open(_debug_path, "a") as _f:
                    _f.write("\n".join(_debug_lines) + "\n")
            except Exception:
                pass

            # 扣减
            token.ops_used += 1

            # 准备签名 payload（含双通道字段）
            nonce = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            sig_payload = {
                "requestId": f"v2-{uuid.uuid4()}",
                "command": command_name,
                "args": actual_args,
                "args_hash": hash_payload({"args": actual_args}),
                "token_id": token_id,
                "session_id": session_id,
                "timestamp": timestamp,
                "nonce": nonce,
                "cmd_hash": cmd_hash or "",
                "script_path": actual_args[0] if command_name == "exec_arbitrary_script" and actual_args else "",
                "script_hash": script_hash or "",
            }
            signature = sign(sig_payload, self._priv_key)

            signed_request = {**sig_payload, "signature": signature}

        logger.info(
            "signed request issued token=%s command=%s args=%s ops_left=%d",
            token_id, command_name, actual_args, token.max_ops - token.ops_used,
        )
        return signed_request

    # ── 后台清理 ──

    def _cleanup_loop(self):
        """每分钟清理过期的 code 和 token。"""
        import time as _time
        while True:
            _time.sleep(60)
            try:
                self._cleanup_expired()
            except Exception:
                logger.exception("cleanup error")

    def _cleanup_expired(self):
        now = time()
        with self._lock:
            # 清理过期 code
            expired_codes = [
                code for code, entry in self._codes.items()
                if entry.is_expired and entry.status in (STATUS_PENDING, STATUS_APPROVED)
            ]
            for code in expired_codes:
                entry = self._codes[code]
                entry.status = STATUS_EXPIRED
                logger.debug("code=%s auto-expired", code)

            # 清理过期 token
            expired_tokens = [
                tid for tid, token in self._tokens.items()
                if token.is_expired
            ]
            for tid in expired_tokens:
                del self._tokens[tid]
                logger.debug("token=%s auto-expired and removed", tid)

            # 清理 1 小时前的已消费/已拒绝 code（防止内存泄漏）
            old_codes = [
                code for code, entry in self._codes.items()
                if entry.status in (STATUS_CONSUMED, STATUS_REJECTED, STATUS_EXPIRED)
                and now - entry.requested_at > 86400  # 24h
            ]
            for code in old_codes:
                del self._codes[code]
