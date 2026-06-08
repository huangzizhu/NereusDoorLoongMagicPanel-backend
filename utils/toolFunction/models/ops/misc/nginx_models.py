from pydantic import BaseModel
from enum import Enum
from typing import Any


class NginxInstallInfo(BaseModel):
    isInstalled: bool
    version: str | None = None
    configPath: str | None = None


class NginxStatus(BaseModel):
    isRunning: bool
    workerProcessCount: int
    activeConnections: int | None = None
    requestsPerSecond: float | None = None


class NginxSiteMode(str, Enum):
    STATIC = "static"
    REVERSE_PROXY = "reverse_proxy"


class NginxSiteCreateResult(BaseModel):
    domain: str
    mode: NginxSiteMode
    listenPort: int
    configPath: str
    enabledPath: str | None = None
    rootPath: str | None = None
    proxyPass: str | None = None
    isEnabled: bool
    isReloaded: bool


class NginxLayoutType(str, Enum):
    """Nginx 配置目录布局类型"""
    SITES_ENABLED = "sites-enabled"   # Debian/Ubuntu 风格
    CONF_D = "conf.d"                 # RHEL/Kylin 风格
    UNKNOWN = "unknown"               # 无法确定


class NginxLayout(BaseModel):
    """检测到的 Nginx 配置目录布局"""
    layoutType: NginxLayoutType
    configDir: str                    # 配置存放目录
    enabledDir: str | None = None     # 启用目录（仅 Debian 风格）
    availableDir: str | None = None   # available 目录（仅 Debian 风格）
    mainConfigPath: str | None = None # nginx.conf 主配置路径
    nginxConfDir: str = "/etc/nginx"  # nginx 配置根目录


class NginxSiteInfo(BaseModel):
    """站点列表中的单个站点信息"""
    configName: str
    configPath: str
    domain: str | None = None
    listen: str | None = None
    mode: str = "unknown"
    rootPath: str | None = None
    proxyPass: str | None = None
    isEnabled: bool = True


class NginxSiteDeleteResult(BaseModel):
    """删除站点结果"""
    configName: str
    configPath: str
    isDeleted: bool
    isReloaded: bool


class NginxSslApplyResult(BaseModel):
    """SSL 证书申请结果"""
    domain: str
    webroot: str | None = None
    certPath: str | None = None
    keyPath: str | None = None
    isApplied: bool


class NginxSslConfigResult(BaseModel):
    """SSL 配置写入结果"""
    domain: str
    configPath: str
    certPath: str
    keyPath: str
    isSslConfigured: bool
    isReloaded: bool


class NginxSslRenewResult(BaseModel):
    """SSL 续期结果"""
    domain: str
    isRenewed: bool
    isReloaded: bool
