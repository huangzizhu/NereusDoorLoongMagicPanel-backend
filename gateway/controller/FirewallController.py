from fastapi import APIRouter
from gateway.controller.AbstractController import AbstractController
from gateway.Response import ResponseModel,Response
from gateway.Singleton import singletonInit
from gateway.service.FirewallService import FirewallService
from pojo.FireWall import SecuritySwitchState
class FirewallController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/firewall", tags=["防火墙"])
        self.firewallService: FirewallService = FirewallService()
        super().__init__("firewallController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.get("/switch")
        def getSecuritySwitchState() -> ResponseModel:
            state: SecuritySwitchState = self.firewallService.getSecuritySwitchState()
            return Response.success(data=state)

