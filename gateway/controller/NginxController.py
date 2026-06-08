from fastapi import APIRouter
from gateway.controller.AbstractController import AbstractController
from gateway.Response import Response, ResponseModel
from gateway.Singleton import singletonInit
from gateway.service.NginxService import NginxService
from pojo.Nginx import (
    CreateSiteRequest,
    DeleteSiteRequest,
    ApplySslRequest,
    ConfigSslRequest,
    RenewSslRequest,
    UpdateSiteConfigRequest,
)


class NginxController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/nginx", tags=["Nginx 管理"])
        self.nginxService = NginxService()
        super().__init__("nginxController", self.router)
        self.routerSetup()

    def routerSetup(self):
        @self.router.get("/install")
        def getInstallInfo() -> ResponseModel:
            info = self.nginxService.getInstallInfo()
            return Response.success(data=info.model_dump())

        @self.router.get("/status")
        def getStatus() -> ResponseModel:
            status = self.nginxService.getStatus()
            return Response.success(data=status.model_dump())

        @self.router.post("/test-config")
        def testConfig() -> ResponseModel:
            return Response.success(data=self.nginxService.testConfig())

        @self.router.post("/reload")
        def reloadNginx() -> ResponseModel:
            return Response.success(data=self.nginxService.reload())

        @self.router.post("/restart")
        def restartNginx() -> ResponseModel:
            return Response.success(data=self.nginxService.restart())

        # ── 新增：站点列表 ──
        @self.router.get("/sites")
        def getSiteList() -> ResponseModel:
            sites = self.nginxService.getSiteList()
            return Response.success(data={
                "total": len(sites),
                "list": sites,
            })

        # ── 读取站点配置（JSON，前端网页编辑器直接使用） ──
        @self.router.get("/site/{domain}")
        def getSiteConfig(domain: str) -> ResponseModel:
            config = self.nginxService.getSiteConfig(domain)
            return Response.success(data=config)

        # ── 修改站点配置（JSON body，原子化保存） ──
        @self.router.put("/site/{domain}")
        def updateSiteConfig(domain: str, request: UpdateSiteConfigRequest) -> ResponseModel:
            result = self.nginxService.updateSiteConfigAtomic(domain, request.content)
            return Response.success(data=result)

        # ── 新增：创建站点 ──
        @self.router.post("/site")
        def createSite(request: CreateSiteRequest) -> ResponseModel:
            if request.mode == "reverse_proxy" and request.proxyPass and request.proxyPort:
                proxyTarget = f"{request.proxyProtocol}://{request.proxyPass}:{request.proxyPort}"
            else:
                proxyTarget = request.proxyPass

            result = self.nginxService.createSite(
                domain=request.domain,
                mode=request.mode,
                listenPort=request.listenPort,
                rootPath=request.rootPath,
                proxyPass=proxyTarget,
            )
            return Response.success(data=result)

        # ── 新增：删除站点 ──
        @self.router.delete("/site/{configName}")
        def deleteSite(configName: str) -> ResponseModel:
            result = self.nginxService.deleteSite(configName)
            return Response.success(data=result)

        # ── 新增：申请 SSL ──
        @self.router.post("/ssl/apply")
        def applySsl(request: ApplySslRequest) -> ResponseModel:
            result = self.nginxService.applySsl(request.domain, request.email)
            return Response.success(data=result)

        # ── 新增：配置 SSL ──
        @self.router.post("/ssl/config")
        def configSsl(request: ConfigSslRequest) -> ResponseModel:
            result = self.nginxService.configSsl(request.domain, request.certPath, request.keyPath)
            return Response.success(data=result)

        # ── 新增：续期 SSL ──
        @self.router.post("/ssl/renew")
        def renewSsl(request: RenewSslRequest) -> ResponseModel:
            result = self.nginxService.renewSsl(request.domain)
            return Response.success(data=result)
