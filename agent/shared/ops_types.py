"""
运维工具返回类型 — dataclass 定义。

替代原 models/ops/ 下的 pydantic models。
按类别分组，导入时按需加载。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


# ── 系统监控 ──

@dataclass
class CpuInfo:
    modelName: str
    coreCount: int
    usagePercent: float
    load1Min: float
    load5Min: float
    load15Min: float

@dataclass
class MemoryInfo:
    totalBytes: int
    usedBytes: int
    availableBytes: int
    usagePercent: float
    swapTotalBytes: int
    swapUsedBytes: int
    swapUsagePercent: float

@dataclass
class DiskPartitionInfo:
    mountPoint: str
    fileSystem: str = ""
    totalBytes: int = 0
    usedBytes: int = 0
    usagePercent: float = 0.0

@dataclass
class GpuInfo:
    modelName: str
    memoryTotalMB: int = 0
    memoryUsedMB: int = 0
    utilizationPercent: float = 0.0
    temperatureCelsius: float = 0.0

@dataclass
class NetworkInterfaceInfo:
    interfaceName: str
    ipAddress: str | None = None
    macAddress: str | None = None
    recvBytesPerSec: float = 0.0
    sentBytesPerSec: float = 0.0
    totalRecvBytes: int = 0
    totalSentBytes: int = 0
    isUp: bool = False

# ── 进程 ──

class ProcessSortBy(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    PID = "pid"

@dataclass
class ProcessInfo:
    pid: int
    processName: str
    userName: str
    cpuPercent: float
    memoryPercent: float
    status: str
    command: str
    ppid: int | None = None
    threadCount: int | None = None
    rssBytes: int | None = None

@dataclass
class ProcessKillResult:
    success: bool
    pid: int
    errorMessage: str | None = None

@dataclass
class BatchKillResult:
    results: list[ProcessKillResult] = field(default_factory=list)
    totalRequested: int = 0
    totalSuccess: int = 0
    totalFailed: int = 0

# ── 文件系统 ──

@dataclass
class FileInfo:
    name: str
    path: str
    sizeBytes: int
    isDirectory: bool
    permissions: str
    modifiedTime: float | None = None
    owner: str | None = None
    group: str | None = None

@dataclass
class FileOperationResult:
    success: bool
    path: str
    message: str = ""
    detail: dict | None = None

@dataclass
class GrepMatch:
    fileName: str
    lineNumber: int
    lineContent: str

@dataclass
class GrepResult:
    success: bool
    pattern: str
    matches: list[GrepMatch] = field(default_factory=list)
    totalMatches: int = 0

@dataclass
class TextFileReadResult:
    success: bool
    targetPath: str
    content: str = ""
    encoding: str | None = None
    sizeBytes: int = 0

# ── 网络 ──

@dataclass
class PingResult:
    isReachable: bool
    averageLatencyMs: float | None = None
    packetLossPercent: float | None = None

@dataclass
class PortCheckResult:
    isOpen: bool
    connectionTimeMs: float | None = None

# ── 服务 ──

class ServiceAction(str, Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    ENABLE = "enable"
    DISABLE = "disable"
    STATUS = "status"

@dataclass
class ServiceOperationResult:
    success: bool
    serviceName: str
    currentStatus: str = ""
    message: str = ""

@dataclass
class LogQueryResult:
    lines: list[str] = field(default_factory=list)
    totalLines: int = 0
    logSource: str = ""

# ── 用户 ──

@dataclass
class UserInfo:
    userName: str
    uid: int
    homeDirectory: str = ""
    loginShell: str = ""
    isSudoUser: bool = False

@dataclass
class LoginRecord:
    userName: str
    loginTime: str
    loginIp: str | None = None
    loginStatus: str = "success"

# ── 防火墙 ──

class FirewallBackendType(str, Enum):
    FIREWALLD = "firewalld"
    UFW = "ufw"
    UNKNOWN = "unknown"

@dataclass
class FirewallStatus:
    isActive: bool
    defaultPolicy: str = ""
    backendType: FirewallBackendType = FirewallBackendType.UNKNOWN

@dataclass
class FirewallPortRule:
    port: int
    protocol: str = "tcp"
    policy: str = "accept"
    sourceIp: str | None = None

@dataclass
class FirewallPortOperationResult:
    success: bool
    port: int
    protocol: str = "tcp"
    message: str = ""

# ── 中间件 ──

@dataclass
class DockerInstallInfo:
    isInstalled: bool
    version: str | None = None

@dataclass
class DockerContainer:
    containerId: str
    imageName: str
    status: str
    ports: str = ""
    cpuPercent: float | None = None
    memoryUsageMB: float | None = None
    memoryLimitMB: float | None = None

@dataclass
class NginxInstallInfo:
    isInstalled: bool
    version: str | None = None
    configPath: str | None = None

@dataclass
class NginxStatus:
    isRunning: bool
    workerProcessCount: int = 0
    activeConnections: int | None = None
    requestsPerSecond: float | None = None

@dataclass
class DatabaseInstallInfo:
    isInstalled: bool
    databaseType: str
    version: str | None = None

@dataclass
class DatabaseStatus:
    isRunning: bool
    databaseType: str
    currentConnections: int | None = None
    slowQueryCount: int | None = None

# ── 公共 ──

@dataclass
class OperationResult:
    success: bool
    message: str = ""
    detail: dict | None = None
