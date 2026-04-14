from fastapi import APIRouter

from gateway.controller.AbstractController import AbstractController
from pojo.User import UserLoginRequest,TokenResponse
from gateway.Response import Response,ResponseModel
from gateway.service.UserService import UserService
from gateway.Singleton import singletonInit
class UserController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/user", tags=["用户管理"])
        self.userService: UserService = UserService()
        super().__init__("userController", self.router)
        self.routerSetup()

    def routerSetup (self):

        @self.router.post("/login")
        def login(userLoginRequest: UserLoginRequest) ->ResponseModel:
            token :TokenResponse = self.userService.login(userLoginRequest)
            return Response.success(token)


