import json
import time
from datetime import datetime

from starlette.datastructures import MutableHeaders

from pojo.Log import Log
from fastapi import Request, Response, FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pojo.User import TokenResponse
from gateway.service.LogService import LogService
from utils.JWTTokenTool import getUserId
from Exception.TokenAuthException import TokenAuthException
# from pojo.User import User
# from gateway.dao.UserDaoInterface import UserDaoInterface
# from gateway.dao.UserDaoOrm import UserDaoOrm

class GlobalInterceptor(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.logService = LogService()
        # self.userDao: UserDaoInterface = UserDaoOrm()
        self.excludePaths = {
            "/user/login",
            "/docs",
            "/user/refresh",
        }

    async def dispatch(self, request: Request, call_next):

        # userId = 0
        # if request.url.path not in self.excludePaths:
        #     try:
        #         # token拦截
        #         accessToken = request.headers.get("accessToken")
        #         if not accessToken:
        #             raise TokenAuthException("accessToken is required")
        #         userId = getUserId(accessToken)
        #         if not userId:
        #             raise TokenAuthException("userId is required")#这个几乎不可能
        #         user: User = self.userDao.getUserByUid(userId) #验证用户是否存在
        #         if not user:
        #             raise TokenAuthException("userId is invalid")
        #     except Exception as e:
        #         return JSONResponse(
        #             content={
        #                 "code": 0,
        #                 "msg": str(e),
        #                 "data": None
        #             },
        #             status_code=401
        #         )
        # #到这里验证通过了
        # bodyBytes = await request.body()
        #
        # # 👇 把 body 塞回去
        # async def receive():
        #     return {
        #         "type": "http.request",
        #         "body": bodyBytes,
        #         "more_body": False,
        #     }
        #
        # request._receive = receive
        # #记录开始时间
        # startTime = time.perf_counter_ns()
        # #执行方法
        # response = await call_next(request)
        # endTime = time.perf_counter_ns()
        # #记录日志
        # endpoint = request.scope.get("endpoint")  # 当前请求对应的函数
        # shouldLog = getattr(endpoint, "_enable_logging", False)
        # if shouldLog:
        #     log: Log = Log(
        #         functionName=endpoint.__name__,
        #         userId=userId,
        #         ipAddress=request.client.host if request.client else None,
        #         operationTime=datetime.now(),
        #         executionTime=(endTime - startTime) / 1e6,  # 转换为秒,
        #         requestPath=request.url.path,
        #         httpMethod=request.method,
        #         logId = None,
        #         inputParams=None,
        #         returnValue = None,
        #         errorMessage=None
        #     )
        #     try:
        #         bodyJson = json.loads(bodyBytes.decode())
        #     except:
        #         bodyJson = None
        #     log.inputParams = bodyJson
        #     data = None
        #     body = b""
        #     async for chunk in response.body_iterator:
        #         body += chunk
        #     try:
        #         data = json.loads(body)
        #     except Exception:
        #         pass
        #     log.returnValue = data
        #     try:
        #         if data:
        #             if data['code'] == '1':
        #                 log.errorMessage = data['msg']
        #     except Exception:
        #         pass
        #     self.logService.insertLog(log)
        #     return Response(
        #         content=body,
        #         status_code=response.status_code,
        #         headers=dict(response.headers),
        #         media_type=response.media_type)

        # return response
        return await call_next(request)