from gateway.controller.ConfigController import ConfigController
from gateway.controller.SystemInfoController import SystemInfoController
from gateway.controller.FileController import FileController
from gateway.controller.AbstractController import AbstractController
from gateway.Response import ResponseModel
from fastapi import FastAPI
from typing import List
from gateway.GlobalInterceptor import GlobalInterceptor
from gateway.GlobalExceptionHandler import GlobalExceptionHandler
from gateway.controller.LogController import LogController
from gateway.controller.UserController import UserController
from fastapi.middleware.cors import CORSMiddleware
from gateway.controller.FirewallController import FirewallController
from gateway.controller.ProcessController import ProcessController
from gateway.controller.TerminalController import TerminalController
from gateway.controller.DockerController import DockerController
from gateway.controller.DatabaseController import DatabaseController
from gateway.controller.NginxController import NginxController
from gateway.controller.AgentController import AgentController
from gateway.controller.ModelPricingController import ModelPricingController
from gateway.controller.AdminController import AdminController
from gateway.controller.ScheduledTaskController import ScheduledTaskController
from gateway.controller.InspectionController import InspectionController
from gateway.internal_rpc import start_backend_rpc_server, stop_backend_rpc_server
from gateway.scheduler.scheduler import AgentScheduler

from gateway.orm.OrmEngine import OrmEngine

from starlette.formparsers import MultiPartParser


MAX_JSON_BODY = 10 * 1024 * 1024
MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024  # 3GB


class Application:

    def __init__(self):
        self.controllers: List[AbstractController] = []
        self.globalExceptionHandler = GlobalExceptionHandler()

    def _registerAllController(self):
        self.controllers.append(LogController())
        self.controllers.append(UserController())
        self.controllers.append(FileController())
        self.controllers.append(FirewallController())
        self.controllers.append(SystemInfoController())
        self.controllers.append(ConfigController())
        self.controllers.append(ProcessController())
        self.controllers.append(TerminalController())
        self.controllers.append(DockerController())
        self.controllers.append(DatabaseController())
        self.controllers.append(NginxController())
        self.controllers.append(AgentController())
        self.controllers.append(ModelPricingController())
        self.controllers.append(AdminController())
        self.controllers.append(ScheduledTaskController())
        self.controllers.append(InspectionController())

    def createApp(self) -> FastAPI:
        self._registerAllController()
        # 所有 ORM 模型已加载完毕（通过 controller import 链），
        # 初始化数据库表结构 + 迁移
        OrmEngine().ensureDbInit()
        app = FastAPI(
            debug=True,
            title="驭门龙面板后端",
            description="驭门龙面板后端",
            version="0.1.0",
            default_response_class=ResponseModel,
            max_json_body_size=MAX_JSON_BODY,
        )
        MultiPartParser.max_file_size = MAX_FILE_SIZE
        MultiPartParser.max_part_size = MAX_FILE_SIZE  # 每个part上限
        app.add_middleware(GlobalInterceptor)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                '*'
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        for controller in self.controllers:
            app.include_router(controller.router)

        self.globalExceptionHandler.registerAllHandler(app)

        @app.on_event("startup")
        async def _startupScheduler():
            await AgentScheduler().start()
            start_backend_rpc_server()

        @app.on_event("shutdown")
        async def _shutdownScheduler():
            stop_backend_rpc_server()
            await AgentScheduler().shutdown()

        return app
