from fastapi import APIRouter
from typing import List
from gateway.controller.AbstractController import AbstractController
from gateway.service.LogService import LogService
from pojo.Log import Log
from gateway.Response import ResponseModel,Response
from gateway.Singleton import singletonInit

class LogController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/log", tags=["日志管理"])
        self.logService: LogService = LogService()
        super().__init__("logController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.get("/all")
        def getAll() -> ResponseModel:
            logs: List[Log] = self.logService.getAllLogs()
            return Response.success(logs)

