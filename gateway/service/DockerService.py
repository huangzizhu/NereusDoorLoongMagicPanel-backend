from gateway.Singleton import Singleton, singletonInit
from utils.toolFunction import (
    checkDockerInstalled,
    deleteDockerContainer,
    getDockerContainerInfo,
    getDockerContainerList,
    getDockerContainerLogs,
    getDockerContainers,
    getDockerImageList,
    pullDockerImage,
    createDockerContainer,
    restartDockerContainer,
    startDockerContainer,
    stopDockerContainer,
    searchDockerImages,
    getDockerDaemonConfig,
    _buildDaemonConfigPayload,
)
from utils.toolFunction.exceptions import (
    PermissionDeniedException,
    ServiceUnavailableException,
    ToolExecutionException,
)
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from Exception.ExecutePermissionDeniedException import ExecutePermissionDeniedException
from gateway.service.PrivilegedAgentClient import (
    PrivilegedAgentClient,
    PrivilegedAgentRemoteError,
)
from privileged_agent.models import PrivilegedAction


class DockerService(Singleton):
    @singletonInit
    def __init__(self):
        self.privilegedAgentClient = PrivilegedAgentClient()

    def _agentContext(self):
        return self.privilegedAgentClient.defaultContext("gateway.docker")

    def _callPrivilegedAgent(self, action: PrivilegedAction, payload: dict, userMessage: str):
        try:
            return self.privilegedAgentClient.call(action, payload, self._agentContext())
        except PrivilegedAgentRemoteError as e:
            if e.code in ["PERMISSION_DENIED", "PROXY_PERMISSION_DENIED"]:
                raise ExecutePermissionDeniedException(
                    innerMessage=e.details or e.message,
                    userMessage=userMessage,
                    cause=e,
                )
            raise BuiltinToolExecutionException(
                innerMessage=e.details or e.message,
                userMessage=userMessage,
                cause=e,
            )

    # ── 基础接口（直连） ──

    def getInstallInfo(self):
        return self._wrap("读取 Docker 安装信息失败", checkDockerInstalled)

    def getRunningContainers(self):
        return self._wrap("读取 Docker 容器列表失败", getDockerContainers, includeStoppedContainers=False)

    def getAllContainers(self):
        return self._wrap("读取 Docker 容器列表失败", getDockerContainerList)

    def getImages(self):
        return self._wrap("读取 Docker 镜像列表失败", getDockerImageList)

    def getContainerInfo(self, containerId: str):
        return self._wrap("读取 Docker 容器详情失败", getDockerContainerInfo, containerId)

    def getContainerLogs(self, containerId: str, tailLines: int):
        return self._wrap("读取 Docker 容器日志失败", getDockerContainerLogs, containerId, tailLines=tailLines)

    def startContainer(self, containerId: str):
        self._wrap("启动 Docker 容器失败", startDockerContainer, containerId)
        return {"containerId": containerId, "isStarted": True}

    def stopContainer(self, containerId: str):
        self._wrap("停止 Docker 容器失败", stopDockerContainer, containerId)
        return {"containerId": containerId, "isStopped": True}

    def restartContainer(self, containerId: str):
        self._wrap("重启 Docker 容器失败", restartDockerContainer, containerId)
        return {"containerId": containerId, "isRestarted": True}

    def deleteContainer(self, containerId: str):
        self._wrap("删除 Docker 容器失败", deleteDockerContainer, containerId)
        return {"containerId": containerId, "isDeleted": True}

    # ── 镜像拉取（直连，支持 registry） ──

    def pullImage(self, imageName: str, tag: str = "latest",
                  platform: str | None = None, registry: str | None = None) -> dict:
        return self._wrap(
            "拉取 Docker 镜像失败",
            pullDockerImage,
            imageName,
            tag=tag,
            platform=platform,
            registry=registry,
        )

    # ── 创建容器（直连） ──

    def createContainer(
        self,
        imageName: str,
        containerName: str,
        ports: dict | None = None,
        envVars: dict | None = None,
        volumes: dict | None = None,
        platform: str | None = None,
        restartPolicy: str | None = None,
    ) -> dict:
        return self._wrap(
            "创建 Docker 容器失败",
            createDockerContainer,
            imageName,
            containerName,
            ports=ports,
            envVars=envVars,
            volumes=volumes,
            platform=platform,
            restartPolicy=restartPolicy,
        )

    # ── 新增：搜索镜像（直连） ──

    def searchImages(self, searchTerm: str, limit: int = 25) -> list[dict]:
        return self._wrap(
            "搜索 Docker 镜像失败",
            searchDockerImages,
            searchTerm,
            limit=limit,
        )

    # ── 新增：读取镜像加速配置（直连） ──

    def getDaemonConfig(self) -> dict:
        return self._wrap(
            "读取 Docker 配置失败",
            getDockerDaemonConfig,
        )

    # ── 新增：设置镜像加速站（特权代理） ──

    def setDaemonConfig(self, mirrors: list[str]) -> dict:
        payload = _buildDaemonConfigPayload(mirrors)
        return self._callPrivilegedAgent(
            PrivilegedAction.DOCKER_SET_DAEMON_CONFIG,
            payload,
            "设置 Docker 镜像加速站失败",
        )

    def _wrap(self, userMessage: str, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(
                innerMessage=e.innerMessage,
                userMessage=userMessage,
                cause=e,
            )
        except ServiceUnavailableException as e:
            raise BuiltinToolExecutionException(
                innerMessage=e.innerMessage,
                userMessage=e.userMessage or userMessage,
                cause=e,
            )
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(
                innerMessage=e.innerMessage,
                userMessage=userMessage,
                cause=e,
            )
