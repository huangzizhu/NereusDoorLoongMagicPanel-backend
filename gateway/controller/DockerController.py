from fastapi import APIRouter, Query
from gateway.controller.AbstractController import AbstractController
from gateway.Response import Response, ResponseModel
from gateway.Singleton import singletonInit
from gateway.service.DockerService import DockerService


class DockerController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/docker", tags=["Docker 管理"])
        self.dockerService = DockerService()
        super().__init__("dockerController", self.router)
        self.routerSetup()

    def routerSetup(self):
        @self.router.get("/install")
        def getInstallInfo() -> ResponseModel:
            info = self.dockerService.getInstallInfo()
            return Response.success(data=info.model_dump())

        @self.router.get("/containers")
        def getRunningContainers() -> ResponseModel:
            containers = self.dockerService.getRunningContainers()
            return Response.success(
                data={
                    "total": len(containers),
                    "list": [item.model_dump() for item in containers],
                }
            )

        @self.router.get("/container/list")
        def getAllContainers() -> ResponseModel:
            containers = self.dockerService.getAllContainers()
            return Response.success(
                data={
                    "total": len(containers),
                    "list": [item.model_dump() for item in containers],
                }
            )

        @self.router.get("/images")
        def getImages() -> ResponseModel:
            images = self.dockerService.getImages()
            return Response.success(
                data={
                    "total": len(images),
                    "list": images,
                }
            )

        @self.router.get("/container/{containerId}")
        def getContainerInfo(containerId: str) -> ResponseModel:
            return Response.success(data=self.dockerService.getContainerInfo(containerId))

        @self.router.get("/container/{containerId}/logs")
        def getContainerLogs(
            containerId: str,
            tailLines: int = Query(200, ge=1, le=5000),
        ) -> ResponseModel:
            return Response.success(
                data=self.dockerService.getContainerLogs(containerId, tailLines)
            )

        @self.router.post("/container/{containerId}/start")
        def startContainer(containerId: str) -> ResponseModel:
            return Response.success(data=self.dockerService.startContainer(containerId))

        @self.router.post("/container/{containerId}/stop")
        def stopContainer(containerId: str) -> ResponseModel:
            return Response.success(data=self.dockerService.stopContainer(containerId))

        @self.router.post("/container/{containerId}/restart")
        def restartContainer(containerId: str) -> ResponseModel:
            return Response.success(data=self.dockerService.restartContainer(containerId))

        @self.router.delete("/container/{containerId}")
        def deleteContainer(containerId: str) -> ResponseModel:
            return Response.success(data=self.dockerService.deleteContainer(containerId))

        # ── 拉取镜像（支持 registry 和 platform） ──
        @self.router.post("/image/pull")
        def pullImage(
            imageName: str = Query(..., min_length=1, description="镜像名称"),
            tag: str = Query("latest", description="标签"),
            platform: str | None = Query(None, description="目标架构，如 linux/amd64"),
            registry: str | None = Query(None, description="自定义镜像仓库地址"),
        ) -> ResponseModel:
            result = self.dockerService.pullImage(
                imageName=imageName,
                tag=tag,
                platform=platform,
                registry=registry,
            )
            return Response.success(data=result)

        # ── 创建容器 ──
        @self.router.post("/container")
        def createContainer(
            imageName: str = Query(..., min_length=1, description="镜像名称"),
            containerName: str = Query(..., min_length=1, description="容器名称"),
            ports: str | None = Query(None, description='端口映射 JSON，如 {"80":"80"}'),
            envVars: str | None = Query(None, description='环境变量 JSON，如 {"KEY":"VAL"}'),
            volumes: str | None = Query(None, description='卷挂载 JSON，如 {"/host":"/container"}'),
            platform: str | None = Query(None, description="目标架构"),
            restartPolicy: str | None = Query(None, description="重启策略"),
        ) -> ResponseModel:
            import json
            result = self.dockerService.createContainer(
                imageName=imageName,
                containerName=containerName,
                ports=json.loads(ports) if ports else None,
                envVars=json.loads(envVars) if envVars else None,
                volumes=json.loads(volumes) if volumes else None,
                platform=platform,
                restartPolicy=restartPolicy,
            )
            return Response.success(data=result)

        # ── 新增：搜索镜像 ──
        @self.router.get("/search")
        def searchImages(
            q: str = Query(..., min_length=1, description="搜索关键词"),
            limit: int = Query(25, ge=1, le=100, description="返回数量"),
        ) -> ResponseModel:
            results = self.dockerService.searchImages(searchTerm=q, limit=limit)
            return Response.success(data={
                "total": len(results),
                "list": results,
            })

        # ── 新增：获取镜像加速配置 ──
        @self.router.get("/mirror")
        def getMirror() -> ResponseModel:
            config = self.dockerService.getDaemonConfig()
            return Response.success(data=config)

        # ── 新增：设置镜像加速站 ──
        @self.router.post("/mirror")
        def setMirror(
            mirrors: str = Query(..., description='镜像加速站 URL 列表 JSON，如 ["https://docker.m.daocloud.cn"]'),
        ) -> ResponseModel:
            import json
            mirrors_list = json.loads(mirrors)
            result = self.dockerService.setDaemonConfig(mirrors_list)
            return Response.success(data=result)
