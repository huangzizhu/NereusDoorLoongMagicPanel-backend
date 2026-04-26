from fastapi import APIRouter, Body
from gateway.controller.AbstractController import AbstractController
from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.service.FirewallService import FirewallService
from pojo.FireWall import SecuritySwitchState,SecuritySwitchUpdate,PortRuleCreate,PortRule, SshConfig,SshConfigUpdate,SshLogBase
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

        
        @self.router.put("/ssh/config")
        def updateSshConfig(updateRequest:SshConfigUpdate) -> ResponseModel:
            config: SshConfig = self.firewallService.updateSshConfig(updateRequest)
            return Response.success(data=config.model_dump())
        
        @self.router.get("/ssh/config")
        def getSshConfig()-> ResponseModel:
            state: SshConfig = self.firewallService.getSshConfig()
            return Response.success(data=state.model_dump())
        @self.router.put("/switch")
        def updateSecuritySwitchState(updateRequest: SecuritySwitchUpdate | None = Body(default=None)) -> ResponseModel:
            request = updateRequest or SecuritySwitchUpdate()
            state: SecuritySwitchState = self.firewallService.updateSecuritySwitchState(request)
            return Response.success(data=state.model_dump())
        
        @self.router.post("/port-rules")
        def createPortRule(rule:PortRuleCreate) -> ResponseModel:
            self.firewallService.createPortRule(rule)
            rules = self.firewallService.getPortRules()
            return Response.success(
                data={
                    "total":len(rules),
                    "list":[r.model_dump() for r in rules],
                }
            )
        
        @self.router.get("/port-rules")
        def getPortRules() -> ResponseModel:
            rules = self.firewallService.getPortRules()
            return Response.success(
                data={
                    "total":len(rules),
                    "list":[rule.model_dump() for rule in rules],
                }
            )
        
        @self.router.get("/ssh/logs")
        def getSshLogBase() -> ResponseModel:
            logs = self.firewallService.getSshLogBase()
            return Response.success(data={"total":len(logs),"list":[log.model_dump() for log in logs],})