from fastapi import APIRouter,Response,Cookie

from gateway.Response import ResponseModel, Response as MyResponse
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.UserService import UserService
from pojo.User import TokenResponse,UserLoginRequest,TokenRefreshRequest


class UserController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/user", tags=["用户管理"])
        self.userService: UserService = UserService()
        super().__init__("userController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.post("/login")
        def login(userLoginForm: UserLoginRequest, response: Response) -> ResponseModel:
            tokens: TokenResponse = self.userService.login(userLoginForm)
            # ============== 关键：把 access_token 和 refresh_token 写入安全 Cookie ==============
            # 开发环境 secure=False，生产环境改成 True
            is_prod = False  # 上线改成 True

            # Access Token（短有效期， 5 分钟）
            response.set_cookie(
                key="accessToken",
                value=tokens.accessToken,
                httponly=True,
                secure=is_prod,
                samesite="lax",
                max_age=5 * 60,
                path="/"
            )

            # Refresh Token（长有效期， 7 天）
            response.set_cookie(
                key="refreshToken",
                value=tokens.refreshToken,
                httponly=True,
                secure=is_prod,
                samesite="lax",
                max_age=7 * 24 * 60 * 60,
                path="/"
            )

            res = MyResponse.success(tokens)
            for k, v in response.headers.raw:
                res.headers.raw.append((k, v))
            return res

        @self.router.delete("/logout")
        def logout(
                response: Response,
                refreshToken: str = Cookie(None)
        ) -> ResponseModel:
            tokens = TokenRefreshRequest(refreshToken=refreshToken)
            self.userService.logout(tokens)

            # 删除两个Cookie
            response.delete_cookie(key="accessToken", path="/")
            response.delete_cookie(key="refreshToken", path="/")
            res = MyResponse.success(msg="退出成功")
            for k, v in response.headers.raw:
                res.headers.raw.append((k, v))
            return res

        @self.router.post("/refresh")
        def refresh(
            response: Response,
            refreshToken: str = Cookie(None)
        ) -> ResponseModel:

            # 构造请求对象给 service
            tokenRequest = TokenRefreshRequest(refreshToken=refreshToken)
            token: TokenResponse = self.userService.refreshToken(tokenRequest)

            # 刷新后更新Cookie
            is_prod = False
            response.set_cookie(key="accessToken", value=token.accessToken, httponly=True, secure=is_prod, samesite="lax", max_age=300, path="/")
            response.set_cookie(key="refreshToken", value=token.refreshToken, httponly=True, secure=is_prod, path="/")
            res = MyResponse.success(token)
            for k, v in response.headers.raw:
                res.headers.raw.append((k, v))
            return res

