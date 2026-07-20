from fastapi import APIRouter, Query, Request

from Exception.TokenAuthException import TokenAuthException
from gateway.Response import Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.scheduler.scheduler import AgentScheduler
from gateway.service.InspectionService import InspectionService
from pojo.ScheduledTask import InspectionConfigUpdate
from utils.JWTTokenTool import getUserId


class InspectionController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/inspection", tags=["Inspection"])
        self.service = InspectionService()
        self.scheduler = AgentScheduler()
        super().__init__("inspectionController", self.router)
        self.routerSetup()

    @staticmethod
    def _getRequestUserId(request: Request) -> int:
        accessToken = request.cookies.get("accessToken")
        if not accessToken:
            raise TokenAuthException(userMessage="未携带accessToken")
        userId = getUserId(accessToken)
        if not userId:
            raise TokenAuthException(userMessage="Token非法")
        return int(userId)

    def routerSetup(self):
        @self.router.get("/reports")
        def listReports(
            page: int = Query(1, ge=1),
            pageSize: int = Query(20, ge=1, le=200),
        ):
            return Response.success(self.service.listReports(page, pageSize))

        @self.router.get("/reports/latest")
        def latestReport():
            return Response.success(self.service.latestReport())

        @self.router.get("/reports/{reportId}")
        def getReport(reportId: int):
            return Response.success(self.service.getReport(reportId))

        @self.router.post("/trigger")
        async def triggerInspection(request: Request):
            userId = self._getRequestUserId(request)
            return Response.success(
                await self.service.triggerInspection(userId=userId, triggeredBy="manual")
            )

        @self.router.get("/config")
        def getConfig():
            return Response.success(self.scheduler.getConfig())

        @self.router.put("/config")
        def updateConfig(body: InspectionConfigUpdate):
            self.scheduler.setInspectionInterval(body.intervalMinutes)
            return Response.success(self.scheduler.getConfig())
