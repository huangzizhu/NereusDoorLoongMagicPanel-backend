import grp
import json
import logging
import os
import signal
import socket
import subprocess
import uuid
from pathlib import Path

from privileged_agent.firewall_adapter import (
    PrivilegedAgentActionError,
    add_port_rule,
    get_firewall_status,
    list_firewall_rules,
    remove_port_rule,
    list_ssh_logs,
    set_firewall_enabled,
)
from privileged_agent.models import (
    PrivilegedAction,
    PrivilegedErrorCode,
    PrivilegedRequest,
    PrivilegedResponse,
)


class PrivilegedAgentServer:
    def __init__(self):
        self.socket_path = os.getenv(
            "NDLM_PRIVILEGED_AGENT_SOCKET",
            "/run/ndlmpanel/privileged-agent.sock",
        )
        self.socket_group = os.getenv("NDLM_PRIVILEGED_AGENT_SOCKET_GROUP", "")
        self.socket_mode = int(os.getenv("NDLM_PRIVILEGED_AGENT_SOCKET_MODE", "660"), 8)
        self.logger = logging.getLogger("privileged_agent")
        self._server_socket: socket.socket | None = None
        self._running = True
        self.allowed_service_actions = {"start", "stop", "restart", "enable", "disable"}
        self.allowed_service_names = {"ssh", "sshd", "firewalld", "nginx", "docker"}

    def _run_command(self, command: list[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
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
        """
        Debian/Ubuntu 布局：在 sites-enabled 中创建软链接指向实际配置。
        """
        if layout_type == "sites-enabled":
            enabled_link = Path("/etc/nginx/sites-enabled") / f"{site_name}.conf"
            if not enabled_link.exists():
                enabled_link.symlink_to(Path(target_path))

    # ── MySQL 辅助 ──
    def _mysql_exec(self, sql: str) -> subprocess.CompletedProcess:
        return self._run_command(["mysql", "-e", sql])

    def _dispatch(self, request: PrivilegedRequest) -> object:
        action = request.action
        payload = request.payload

        # ── Firewall ──
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

        # ── Nginx 原子化保存（带备份回滚） ──
        if action == PrivilegedAction.NGINX_SAVE_CONFIG_ATOMIC.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            layout_type = str(payload.get("layoutType", ""))
            site_name = str(payload.get("siteName", ""))

            path = Path(target_path)
            # 1. 备份当前配置
            backup_content = None
            if path.exists():
                backup_content = path.read_text(encoding="utf-8")

            # 2. 写入新配置
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            os.chmod(str(path), 0o644)

            # 3. 创建 symlink（Debian 布局）
            self._ensure_symlink(target_path, site_name, layout_type)

            # 4. 测试 nginx -t
            test_result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True, text=True, check=False,
            )

            if test_result.returncode != 0:
                # 测试失败 → 回滚
                error_detail = (test_result.stderr or test_result.stdout or "").strip()
                if backup_content is not None:
                    path.write_text(backup_content, encoding="utf-8")
                    # 重新创建 symlink（如果回滚后文件还在）
                    self._ensure_symlink(target_path, site_name, layout_type)
                raise PrivilegedAgentActionError(
                    PrivilegedErrorCode.COMMAND_FAILED,
                    "Nginx 配置测试失败，已回滚",
                    error_detail,
                )

            # 5. 测试通过 → reload
            self._run_command(["systemctl", "reload", "nginx"])

            return {
                "targetPath": str(path),
                "isSaved": True,
                "isReloaded": True,
            }

        # ── Nginx 基础 ──
        if action == PrivilegedAction.NGINX_TEST_CONFIG.value:
            result = self._run_command(["nginx", "-t"])
            return {
                "isValid": True,
                "stdout": (result.stdout or "").strip(),
                "stderr": (result.stderr or "").strip(),
            }
        if action == PrivilegedAction.NGINX_RELOAD.value:
            self._run_command(["systemctl", "reload", "nginx"])
            return {"serviceName": "nginx", "action": "reload", "isReloaded": True}
        if action == PrivilegedAction.NGINX_RESTART.value:
            self._run_command(["systemctl", "restart", "nginx"])
            status_result = subprocess.run(
                ["systemctl", "is-active", "nginx"],
                capture_output=True, text=True, check=False,
            )
            return {
                "serviceName": "nginx", "action": "restart", "isRestarted": True,
                "currentStatus": (status_result.stdout or "").strip(),
            }

        # ── Nginx 配置管理 ──
        if action == PrivilegedAction.NGINX_SAVE_CONFIG.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            layout_type = str(payload.get("layoutType", ""))
            site_name = str(payload.get("siteName", ""))
            result_data = self._nginx_save_config(target_path, content)
            # Debian 布局：创建 sites-enabled 软链接
            self._ensure_symlink(target_path, site_name, layout_type)
            # 写入后自动 nginx -t
            self._run_command(["nginx", "-t"])
            return result_data

        if action == PrivilegedAction.NGINX_DELETE_SITE.value:
            config_path = str(payload["configPath"])
            layout_type = str(payload.get("layoutType", ""))
            site_name = str(payload.get("siteName", ""))
            path = Path(config_path)
            if path.exists():
                path.unlink()
            # Debian 布局：同时删除 sites-enabled 软链接
            if layout_type == "sites-enabled":
                enabled_link = Path("/etc/nginx/sites-enabled") / f"{site_name}.conf"
                if enabled_link.exists() or enabled_link.is_symlink():
                    enabled_link.unlink()
            # 删除后自动 nginx -t + reload
            self._run_command(["nginx", "-t"])
            self._run_command(["systemctl", "reload", "nginx"])
            return {
                "configPath": config_path,
                "isDeleted": True,
                "isReloaded": True,
            }

        if action == PrivilegedAction.NGINX_READ_FILE.value:
            file_path = str(payload["filePath"])
            path = Path(file_path)
            if not path.exists():
                raise PrivilegedAgentActionError(
                    PrivilegedErrorCode.SERVICE_UNAVAILABLE,
                    "文件不存在",
                    file_path,
                )
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
                    files.append({
                        "name": f.name,
                        "path": str(f),
                        "size": f.stat().st_size,
                    })
            return {"dirPath": dir_path, "files": files}

        # ── Nginx SSL ──
        if action == PrivilegedAction.NGINX_APPLY_SSL.value:
            domain = str(payload["domain"])
            email = str(payload["email"])
            webroot = str(payload["webroot"])
            # 检查 certbot
            result = subprocess.run(
                ["which", "certbot"], capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                # 尝试 pip3 安装的 certbot
                result = subprocess.run(
                    ["python3", "-m", "certbot", "--version"],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode != 0:
                    raise PrivilegedAgentActionError(
                        PrivilegedErrorCode.SERVICE_UNAVAILABLE,
                        "certbot 未安装",
                        "请先安装 certbot",
                    )
            command = [
                "certbot", "certonly", "--webroot",
                "-w", webroot, "-d", domain,
                "--email", email,
                "--agree-tos", "--non-interactive",
            ]
            self._run_command(command)
            live_dir = Path(f"/etc/letsencrypt/live/{domain}")
            return {
                "domain": domain,
                "webroot": webroot,
                "certPath": str(live_dir / "fullchain.pem"),
                "keyPath": str(live_dir / "privkey.pem"),
            }

        if action == PrivilegedAction.NGINX_RENEW_SSL.value:
            domain = str(payload["domain"])
            self._run_command([
                "certbot", "renew", "--cert-name", domain, "--non-interactive",
            ])
            self._run_command(["nginx", "-t"])
            self._run_command(["systemctl", "reload", "nginx"])
            return {"domain": domain, "isRenewed": True, "isReloaded": True}

        if action == PrivilegedAction.NGINX_CONFIG_SSL.value:
            target_path = str(payload["targetPath"])
            content = str(payload["content"])
            self._nginx_save_config(target_path, content)
            self._run_command(["nginx", "-t"])
            self._run_command(["systemctl", "reload", "nginx"])
            return {
                "targetPath": target_path,
                "isSslConfigured": True,
                "isReloaded": True,
            }

        # ── SSH ──
        if action == PrivilegedAction.SSH_LIST_LOGS.value:
            return list_ssh_logs(int(payload.get("maxLines", 500)))

        # ── Service ──
        if action == PrivilegedAction.SERVICE_SET_STATE.value:
            service_name = str(payload["serviceName"])
            service_action = str(payload["action"])
            if service_action not in self.allowed_service_actions:
                raise PrivilegedAgentActionError(
                    PrivilegedErrorCode.INVALID_REQUEST,
                    "不支持的服务动作",
                    service_action,
                )
            if service_name not in self.allowed_service_names:
                raise PrivilegedAgentActionError(
                    PrivilegedErrorCode.PERMISSION_DENIED,
                    "当前不允许操作该系统服务",
                    service_name,
                )
            subprocess.run(
                ["systemctl", service_action, service_name],
                capture_output=True, text=True, check=True,
            )
            status_result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True, text=True, check=False,
            )
            return {
                "serviceName": service_name,
                "action": service_action,
                "currentStatus": (status_result.stdout or "").strip(),
            }

        # ── Docker ──
        if action == PrivilegedAction.DOCKER_SET_DAEMON_CONFIG.value:
            target_path = str(payload.get("daemonJsonPath", "/etc/docker/daemon.json"))
            content = str(payload.get("content", "{}"))
            # 写 daemon.json
            path = Path(target_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            os.chmod(str(path), 0o644)
            # 重启 Docker 守护进程
            self._run_command(["systemctl", "restart", "docker"])
            return {
                "daemonJsonPath": str(path),
                "isSet": True,
                "isRestarted": True,
            }

        # ── MySQL ──
        if action == PrivilegedAction.MYSQL_CREATE_DATABASE.value:
            db_name = str(payload["dbName"])
            sql = (f"CREATE DATABASE IF NOT EXISTS `{db_name}`"
                   " CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
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
            return {
                "dbName": db_name, "username": username, "host": "localhost",
                "privileges": "ALL PRIVILEGES", "isGranted": True, "isCreated": True,
            }

        if action == PrivilegedAction.MYSQL_GET_DATABASE_LIST.value:
            result = self._mysql_exec("SHOW DATABASES;")
            dbs = [line.strip() for line in result.stdout.strip().splitlines()
                   if line.strip() and not line.strip().startswith("Database")]
            return {"databases": dbs}

        if action == PrivilegedAction.MYSQL_EXEC.value:
            sql = str(payload["sql"])
            result = self._mysql_exec(sql)
            return {
                "stdout": (result.stdout or "").strip(),
                "stderr": (result.stderr or "").strip(),
            }

        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.UNKNOWN_ACTION,
            "不支持的特权动作",
            action,
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
                    audit_id,
                    PrivilegedErrorCode.INVALID_REQUEST,
                    "空请求",
                )
                conn.sendall((response.model_dump_json() + "\n").encode("utf-8"))
                return
            try:
                request = PrivilegedRequest.model_validate_json(raw.decode("utf-8"))
                data = self._dispatch(request)
                response = PrivilegedResponse(success=True, auditId=audit_id, data=data)
                self.logger.info(
                    "audit_id=%s source=%s action=%s success=true",
                    audit_id,
                    request.caller.source,
                    request.action,
                )
            except PrivilegedAgentActionError as exc:
                response = self._build_error_response(audit_id, exc.code, exc.message, exc.details)
                self.logger.warning(
                    "audit_id=%s success=false code=%s message=%s details=%s",
                    audit_id,
                    exc.code.value,
                    exc.message,
                    exc.details,
                )
            except subprocess.CalledProcessError as exc:
                details = (exc.stderr or exc.stdout or str(exc)).strip()
                response = self._build_error_response(
                    audit_id,
                    PrivilegedErrorCode.COMMAND_FAILED,
                    "系统命令执行失败",
                    details,
                )
                self.logger.warning(
                    "audit_id=%s success=false code=%s details=%s",
                    audit_id,
                    PrivilegedErrorCode.COMMAND_FAILED.value,
                    details,
                )
            except Exception as exc:
                response = self._build_error_response(
                    audit_id,
                    PrivilegedErrorCode.INTERNAL_ERROR,
                    "特权代理内部错误",
                    str(exc),
                )
                self.logger.exception("audit_id=%s success=false unhandled_error", audit_id)

            conn.sendall((response.model_dump_json() + "\n").encode("utf-8"))

    def serve_forever(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
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
        self.logger.info("privileged agent listening on %s", self.socket_path)

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
