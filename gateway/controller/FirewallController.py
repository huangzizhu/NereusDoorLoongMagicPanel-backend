from fastapi import APIRouter, Body
from gateway.controller.AbstractController import AbstractController
from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.service.FirewallService import FirewallService
from pojo.FireWall import SecuritySwitchState,SecuritySwitchUpdate
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
            return Response.success(data=state.model_dump())
        
        @self.router.put("/switch")
        def updateSecuritySwitchState(updateRequest: SecuritySwitchUpdate | None = Body(default=None)) -> ResponseModel:
            request = updateRequest or SecuritySwitchUpdate()
            state: SecuritySwitchState = self.firewallService.updateSecuritySwitchState(request)
            return Response.success(data=state.model_dump())
        
