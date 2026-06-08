from fastapi import APIRouter
from gateway.controller.AbstractController import AbstractController
from gateway.Response import Response, ResponseModel
from gateway.Singleton import singletonInit
from gateway.service.DatabaseService import DatabaseService
from pojo.Database import (
    MysqlConnectionTestRequest,
    CreateDatabaseRequest,
    CreateUserRequest,
)


class DatabaseController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/database", tags=["数据库管理"])
        self.databaseService = DatabaseService()
        super().__init__("databaseController", self.router)
        self.routerSetup()

    def routerSetup(self):
        # ── 已有 ──
        @self.router.get("/install/{databaseType}")
        def getInstallInfo(databaseType: str) -> ResponseModel:
            info = self.databaseService.getInstallInfo(databaseType)
            return Response.success(data=info.model_dump())

        @self.router.get("/status/{databaseType}")
        def getStatus(databaseType: str) -> ResponseModel:
            status = self.databaseService.getStatus(databaseType)
            return Response.success(data=status.model_dump())

        @self.router.post("/mysql/test-connection")
        def testMysqlConnection(request: MysqlConnectionTestRequest) -> ResponseModel:
            result = self.databaseService.testMysql(request)
            return Response.success(data=result)

        # ── 新增：创建数据库 ──
        @self.router.post("/mysql/database")
        def createDatabase(request: CreateDatabaseRequest) -> ResponseModel:
            result = self.databaseService.createDatabase(request)
            return Response.success(data=result)

        # ── 新增：创建用户并授权 ──
        @self.router.post("/mysql/user")
        def createUser(request: CreateUserRequest) -> ResponseModel:
            result = self.databaseService.createUser(request)
            return Response.success(data=result)

        # ── 新增：获取数据库列表 ──
        @self.router.get("/mysql/databases")
        def getDatabaseList() -> ResponseModel:
            databases = self.databaseService.getDatabaseList()
            return Response.success(data={
                "databaseType": "mysql",
                "databases": databases,
            })
