from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PrivilegedAction(StrEnum):
    FIREWALL_GET_STATUS = "firewall.get_status"
    FIREWALL_LIST_RULES = "firewall.list_rules"
    FIREWALL_ADD_PORT_RULE = "firewall.add_port_rule"
    FIREWALL_REMOVE_PORT_RULE = "firewall.remove_port_rule"
    FIREWALL_SET_ENABLED = "firewall.set_enabled"
    NGINX_TEST_CONFIG = "nginx.test_config"
    NGINX_RELOAD = "nginx.reload"
    NGINX_RESTART = "nginx.restart"
    NGINX_SAVE_CONFIG = "nginx.save_config"
    NGINX_DELETE_SITE = "nginx.delete_site"
    NGINX_READ_FILE = "nginx.read_file"
    NGINX_LIST_DIR = "nginx.list_dir"
    NGINX_APPLY_SSL = "nginx.apply_ssl"
    NGINX_RENEW_SSL = "nginx.renew_ssl"
    NGINX_CONFIG_SSL = "nginx.config_ssl"
    NGINX_SAVE_CONFIG_ATOMIC = "nginx.save_config_atomic"
    SSH_LIST_LOGS = "ssh.list_logs"
    SERVICE_SET_STATE = "service.set_state"
    MYSQL_CREATE_DATABASE = "mysql.create_database"
    MYSQL_CREATE_USER = "mysql.create_user"
    MYSQL_GET_DATABASE_LIST = "mysql.get_database_list"
    MYSQL_EXEC = "mysql.exec"
    DOCKER_SET_DAEMON_CONFIG = "docker.set_daemon_config"

    # ── 通用文件操作（路径受限） ──
    FILE_WRITE_TO_ALLOWED = "file.write_to_allowed_path"
    FILE_CREATE_DIRECTORY = "file.create_directory_in_allowed"
    FILE_SET_PERMISSIONS = "file.set_permissions_in_allowed"

    # ── Nginx 专用 ──
    NGINX_WRITE_STATIC_FILE = "nginx.write_static_file"

    # ── 执行预定义的运维脚本 ──
    EXEC_SCRIPT = "exec.allowed_script"


class PrivilegedErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNKNOWN_ACTION = "UNKNOWN_ACTION"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    COMMAND_FAILED = "COMMAND_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # ── V2 安全错误码 ──
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    SIGNATURE_EXPIRED = "SIGNATURE_EXPIRED"
    NONCE_REPLAY = "NONCE_REPLAY"
    COMMAND_NOT_REGISTERED = "COMMAND_NOT_REGISTERED"
    ARGS_INVALID = "ARGS_INVALID"
    ARGS_HASH_MISMATCH = "ARGS_HASH_MISMATCH"
    PEER_UID_DENIED = "PEER_UID_DENIED"
    TOKEN_EXHAUSTED = "TOKEN_EXHAUSTED"
    RATE_LIMITED = "RATE_LIMITED"


class PrivilegedRequestContext(BaseModel):
    userId: int | None = None
    username: str | None = None
    clientIp: str | None = None
    source: str = Field(..., min_length=1, max_length=100)


class PrivilegedRequest(BaseModel):
    requestId: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    caller: PrivilegedRequestContext
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PrivilegedV2Request(BaseModel):
    """V2 带签名的特权请求。

    相比 V1 (PrivilegedRequest) 新增:
    - command / args:  命令注册表中的命令名和参数
    - args_hash:       SHA256(args) — 与 JIT token 绑定，防止参数篡改
    - token_id:        JIT token 引用
    - session_id:      来源 agent session
    - signature:       Ed25519 签名，供特权代理验签
    - nonce:           防重放
    """

    requestId: str = Field(..., min_length=1, max_length=100)
    action: str = Field(default="", max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    caller: PrivilegedRequestContext | None = None

    # V2 字段
    command: str = Field(..., min_length=1, max_length=100)
    args: list[str] = Field(default_factory=list)
    args_hash: str = Field(default="", max_length=128)
    token_id: str = Field(default="", max_length=128)
    session_id: str = Field(default="", max_length=128)
    timestamp: str = Field(..., description="ISO-8601 UTC")
    nonce: str = Field(..., min_length=8, max_length=128)
    signature: str = Field(..., min_length=1)


class PrivilegedResponse(BaseModel):
    success: bool
    auditId: str
    data: Any | None = None
    errorCode: str | None = None
    errorMessage: str | None = None
    errorDetails: str | None = None
