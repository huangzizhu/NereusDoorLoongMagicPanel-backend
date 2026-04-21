from fastapi import APIRouter,Request
import asyncio
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.SystemInfoService import SystemInfoService
from pojo.PanelInfo import SystemHealthResponse,AlertQuery,AlertEvent
from fastapi.responses import StreamingResponse
from pojo.Common import ListResponse
from gateway.Response import ResponseModel,Response

class SystemInfoController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/system", tags=["系统信息管理"])
        self.systemInfoService = SystemInfoService()
        super().__init__("systemInfoController", self.router)
        self.routerSetup()

    async def getSystemInfo(self, request: Request):
        while True:
            # 检测客户端是否关闭连接
            if await request.is_disconnected():
                break
            # 调用同步 Service 层获取系统信息
            info: SystemHealthResponse = self.systemInfoService.getSystemInfo()
                # 将数据转为 SSE 格式
            yield f"data: {info.model_dump_json()}\n\n"
            await asyncio.sleep(2)  # 控制发送频率


    def routerSetup(self):

        @self.router.get("/health")
        async def getSystemInfoHealthSSE(request: Request):
            return StreamingResponse(self.getSystemInfo(request), media_type="text/event-stream")

        @self.router.get("/alerts")
        def getAllSystemAlerts(alertQuery: AlertQuery):
            alertList: ListResponse = self.systemInfoService.getAllSystemAlerts(alertQuery)
            return Response.success(alertList)

        @self.router.put("/alerts/{id}/read")
        def setAlertsRead(id: int):
            alert: AlertEvent = self.systemInfoService.setAlertsRead(id)
            return Response.success(alert)

        @self.router.put("/alerts/{id}/process")
        def setAlertsProcess(id: int):
            alert: AlertEvent = self.systemInfoService.setAlertsProcess(id)
            return Response.success(alert)


