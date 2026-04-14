from fastapi import APIRouter

from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.UserService import UserService
from pojo.User import TokenResponse,UserLoginRequest


class UserController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/user", tags=["用户管理"])
        self.userService: UserService = UserService()
        super().__init__("userController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.post("/login")
        def login(userLoginForm: UserLoginRequest) -> ResponseModel:
            tokens: TokenResponse = self.userService.login(userLoginForm)
            return Response.success(tokens)