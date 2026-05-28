from fastapi import APIRouter,Request,Query
from fastapi.responses import StreamingResponse
import asyncio
from typing import List
from pojo.Common import ListResponse, PageSearchRequest
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.ProcessService import ProcessService
from pojo.Process import KillProcessRequest, AutoCleanRequest, BatchKillProcessRequest
from gateway.Response import ResponseModel,Response
from ndlmpanel_agent.models.ops.process.process_models import ProcessKillResult, ProcessDetailInfo, \
    ProcessAutoCleanResult, ProcessInfo, BatchKillResult
import json
class ProcessController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/process", tags=["进程"])
        self.processService: ProcessService = ProcessService()
        super().__init__("processController", self.router)
        self.routerSetup()
    async def getProcessSse(self, request,sortedBy,keyword):
        while True:
            # 检测客户端是否关闭连接
            if await request.is_disconnected():
                break
            info: list[ProcessInfo] = self.processService.getProcessInfo(sortedBy, keyword)
            data = [item.model_dump() for item in info]
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(4)  # 控制发送频率

    def routerSetup(self):
        @self.router.get("/sse/")
        def getProcessSse(
                request: Request,
                sortedBy: int = Query(..., description="排序关键词，cpu0,mem1,pid2，默认0"),
                keyword: str = Query(None, description="进程名或命令查询关键词")
        ):
            # sortedBy 是必选（Query(...)），keyword 是可选（默认 None）
            return StreamingResponse(
                self.getProcessSse(request, sortedBy=sortedBy, keyword=keyword),
                media_type="text/event-stream"
            )

        @self.router.delete("/kill")
        def killProcess(killRequest:  KillProcessRequest) -> ResponseModel:
            res: ProcessKillResult = self.processService.killProcess(killRequest)
            return Response.success(res)

        @self.router.delete("/force-kill")
        def forceKillProcess(killRequest: KillProcessRequest) -> ResponseModel:
            res: ProcessKillResult = self.processService.forceKillProcess(killRequest)
            return Response.success(res)

        @self.router.get("/{pid}")
        def getProcessDetail(pid: int):
            res: ProcessDetailInfo = self.processService.getProcessDetail(pid)
            return Response.success(res)

        @self.router.post("/auto-clean")
        def autoClean(request: AutoCleanRequest):
            res: ProcessAutoCleanResult = self.processService.autoClean(request)
            return Response.success(res)

        @self.router.get("/get/zombies")
        def getZombies():
            res: List[ProcessInfo] | None = self.processService.getZombies()
            return Response.success(res)

        @self.router.delete("/batch-kill")
        def batchKillProcess(request: BatchKillProcessRequest):
            res: BatchKillResult = self.processService.batchKillProcess(request)
            return Response.success(res)

        @self.router.delete("/batch-force-kill")
        def batchForceKillProcess(request: BatchKillProcessRequest):
            res: BatchKillResult = self.processService.batchForceKillProcess(request)
            return Response.success(res)

        @self.router.post("/log")
        def getLog(request: PageSearchRequest):
            res: ListResponse = self.processService.getLog(request)
            return Response.success(res)


