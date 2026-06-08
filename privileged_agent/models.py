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


class PrivilegedErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNKNOWN_ACTION = "UNKNOWN_ACTION"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    COMMAND_FAILED = "COMMAND_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


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


class PrivilegedResponse(BaseModel):
    success: bool
    auditId: str
    data: Any | None = None
    errorCode: str | None = None
    errorMessage: str | None = None
    errorDetails: str | None = None
