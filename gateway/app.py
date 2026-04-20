from controller.SystemInfoController import SystemInfoController
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

    def createApp(self) -> FastAPI:
        self._registerAllController()
        app = FastAPI(
            debug=True,
            title="驭门龙面板后端",
            description="驭门龙面板后端",
            version="0.1.0",
            default_response_class=ResponseModel,
        )
        app.add_middleware(GlobalInterceptor)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        for controller in self.controllers:
            app.include_router(controller.router)

        self.globalExceptionHandler.registerAllHandler(app)
        return app


