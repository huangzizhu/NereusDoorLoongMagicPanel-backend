import json
import time
from datetime import datetime
from typing import Optional

from pojo.Log import Log
from fastapi import Request, Response, FastAPI
from gateway.Response import Response as MyResponse
from starlette.middleware.base import BaseHTTPMiddleware
from gateway.service.LogService import LogService
from utils.JWTTokenTool import getUserId
from Exception.TokenAuthException import TokenAuthException
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.dao.UserDaoOrm import UserDaoOrm
from gateway.orm.UserOrm import UserOrm

class GlobalInterceptor(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.logService = LogService()
        self.userDao: UserDaoInterface = UserDaoOrm()
        self.excludePaths = {
            "/user/login",
            "/docs",
            "/user/refresh",
        }
        self.websocketPaths = {
            "/terminal/ws",
            "/terminal/admin/ws",
        }
        self.ssePath = {
            "/system/health",
        }

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.websocketPaths:
            return await call_next(request)

        userId = 0
        if request.url.path not in self.excludePaths:
            try:
                # token拦截
                accessToken = request.cookies.get("accessToken")
                if not accessToken:
                    raise TokenAuthException(userMessage="未携带accessToken")
                userId = getUserId(accessToken)
                if not userId:
                    raise TokenAuthException(userMessage="未携带accessToken")#这个几乎不可能
                user: Optional[UserOrm] = self.userDao.getUserByUid(userId) #验证用户是否存在
                if not user:
                    raise TokenAuthException(userMessage="Token非法")
            except TokenAuthException as e:
                return MyResponse.custom(msg=e.userMessage,status_code=401,code=40101)
            except Exception as e:
                return MyResponse.custom(msg="校验token出错，请重试",status_code=401,code=40101)
        #到这里验证通过了
        if request.url.path.startswith("/process/sse/"):
            return await call_next(request)

        if request.url.path in self.ssePath:
            #sse不要记录日志，因为有点区别
            return await call_next(request)

        bodyBytes = await request.body()

        # 👇 把 body 塞回去
        async def receive():
            return {
                "type": "http.request",
                "body": bodyBytes,
                "more_body": False,
            }

        request._receive = receive
        #记录开始时间
        startTime = time.perf_counter_ns()
        #执行方法
        response = await call_next(request)
        endTime = time.perf_counter_ns()
        #记录日志
        endpoint = request.scope.get("endpoint")  # 当前请求对应的函数
        shouldLog = getattr(endpoint, "_enable_logging", False)
        if shouldLog:
            log: Log = Log(
                functionName=endpoint.__name__,
                userId=userId,
                ipAddress=request.client.host if request.client and request.client.host else "unknown",
                operationTime=datetime.now(),
                executionTime=(endTime - startTime) / 1e6,  # 转换为秒,
                requestPath=request.url.path,
                httpMethod=request.method,
                logId = None,
                inputParams=None,
                returnValue = None,
                errorMessage=None
            )
            try:
                bodyJson = json.loads(bodyBytes.decode())
            except:
                bodyJson = None
            log.inputParams = bodyJson
            data = None
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            try:
                data = json.loads(body)
            except Exception:
                pass
            log.returnValue = data
            try:
                if data:
                    if data['code'] == '1':
                        log.errorMessage = data['msg']
            except Exception:
                pass
            self.logService.insertLog(log)
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type)

        return response
