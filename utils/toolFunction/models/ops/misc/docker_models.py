from pydantic import BaseModel


class DockerInstallInfo(BaseModel):
    isInstalled: bool
    version: str | None = None


class DockerContainer(BaseModel):
    containerId: str
    imageName: str
    status: str
    ports: str
    cpuPercent: float | None = None
    memoryUsageMB: float | None = None
    memoryLimitMB: float | None = None


class DockerSearchResult(BaseModel):
    """Docker Hub 搜索结果中的单个镜像"""
    name: str
    description: str | None = None
    starCount: int = 0
    isOfficial: bool = False
    isAutomated: bool = False


class DockerDaemonConfig(BaseModel):
    """Docker daemon.json 配置（仅镜像加速相关字段）"""
    registryMirrors: list[str] | None = None
    daemonJsonPath: str = "/etc/docker/daemon.json"
