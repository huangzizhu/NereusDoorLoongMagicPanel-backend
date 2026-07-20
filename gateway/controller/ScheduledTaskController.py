from fastapi import APIRouter, Query, Request

from Exception.TokenAuthException import TokenAuthException
from gateway.Response import Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.ScheduledTaskService import ScheduledTaskService
from pojo.ScheduledTask import ScheduledTaskCreate, ScheduledTaskUpdate
from utils.JWTTokenTool import getUserId


class ScheduledTaskController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/scheduled-tasks", tags=["ScheduledTask"])
        self.service = ScheduledTaskService()
        super().__init__("scheduledTaskController", self.router)
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
        @self.router.post("")
        def createTask(request: Request, body: ScheduledTaskCreate):
            userId = self._getRequestUserId(request)
            return Response.success(self.service.createTask(userId, body))

        @self.router.get("")
        def listTasks(
            request: Request,
            status: str | None = Query(None),
            includeDeleted: bool = Query(False),
        ):
            self._getRequestUserId(request)
            return Response.success(
                self.service.listTasks(None, status, includeDeleted=includeDeleted)
            )

        @self.router.get("/all")
        def listAllTasks(
            request: Request,
            status: str | None = Query(None),
            includeDeleted: bool = Query(True),
        ):
            self._getRequestUserId(request)
            return Response.success(
                self.service.listTasks(None, status, includeDeleted=includeDeleted)
            )

        @self.router.get("/pending-approval")
        def listPendingApprovalTasks(request: Request):
            self._getRequestUserId(request)
            return Response.success(self.service.listPendingApprovalTasks())

        @self.router.get("/runs/{runId}")
        def getRun(runId: int):
            return Response.success(self.service.getRun(runId))

        @self.router.get("/{taskId}/approval")
        def getApproval(request: Request, taskId: int):
            self._getRequestUserId(request)
            return Response.success(self.service.getApproval(taskId))

        @self.router.post("/{taskId}/approval/reissue")
        def reissueApproval(request: Request, taskId: int):
            self._getRequestUserId(request)
            return Response.success(self.service.reissueApproval(taskId))

        @self.router.get("/{taskId}")
        def getTask(request: Request, taskId: int):
            self._getRequestUserId(request)
            return Response.success(self.service.getTask(taskId, None))

        @self.router.put("/{taskId}")
        def updateTask(request: Request, taskId: int, body: ScheduledTaskUpdate):
            self._getRequestUserId(request)
            return Response.success(self.service.updateTask(taskId, None, body))

        @self.router.delete("/{taskId}")
        def deleteTask(request: Request, taskId: int):
            self._getRequestUserId(request)
            self.service.deleteTask(taskId, None)
            return Response.success()

        @self.router.post("/{taskId}/pause")
        def pauseTask(request: Request, taskId: int):
            self._getRequestUserId(request)
            return Response.success(self.service.pauseTask(taskId, None))

        @self.router.post("/{taskId}/resume")
        def resumeTask(request: Request, taskId: int):
            self._getRequestUserId(request)
            return Response.success(self.service.resumeTask(taskId, None))

        @self.router.post("/{taskId}/trigger")
        async def triggerTask(request: Request, taskId: int):
            self._getRequestUserId(request)
            return Response.success(await self.service.triggerTask(taskId, None))

        @self.router.get("/{taskId}/runs")
        def listRuns(
            request: Request,
            taskId: int,
            limit: int = Query(50, ge=1, le=200),
        ):
            self._getRequestUserId(request)
            return Response.success(self.service.listRuns(taskId, None, limit))
