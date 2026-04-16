from typing import Dict, Type, Callable, Coroutine, Any
from fastapi import Request, FastAPI
import inspect

from Exception.FileAlreadyExistException import FileAlreadyExistException
from Exception.FileNotFoundException import FileNotFoundException
from Exception.FileTypeException import FileTypeException
from gateway.Response import ResponseModel, Response
from Exception.GatewayAbstractException import GatewayAbstractException
from Exception.DataBaseException import DataBaseException
from Exception.InvalidTokenException import InvalidTokenException
from Exception.AccessTokenExpiryException import AccessTokenExpiryException
from Exception.RefreshTokenExpiryException import RefreshTokenExpiryException
from Exception.PasswordIncorrectException import PasswordIncorrectException
from Exception.TokenAuthException import TokenAuthException
from Exception.UserNotFoundException import UserNotFoundException
from Exception.FilePermissionDeniedException import FilePermissionDeniedException
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from Exception.SecurityStatusReadException import SecurityStatusReadException



def ExceptionHandler(exception: Type[GatewayAbstractException]):
    def decorator(func):
        setattr(func, "_exception_class", exception)
        return func
    return decorator

class GlobalExceptionHandler:
    def __init__(self):
        self.exceptionHandlerMap: Dict[
            Type[GatewayAbstractException],
            Callable[[Request, GatewayAbstractException], Coroutine[Any, Any, ResponseModel]]
        ] = {}
        self._collectHandlers()

    #一个一个函数收集，装饰器标记异常类型，反射获取函数上的标记，构建异常类型到函数的映射
    def _collectHandlers(self):
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            exc_class = getattr(method, "_exception_class", None)
            if exc_class is not None:
                self.exceptionHandlerMap[exc_class] = method
    #注册所有处理器
    def registerAllHandler(self, app: FastAPI):
        for exc_class, handler in self.exceptionHandlerMap.items():
            app.add_exception_handler(exc_class, handler)

    @ExceptionHandler(TokenAuthException)
    async def handleTokenAuthException(self, request: Request, exception: TokenAuthException) -> ResponseModel:
        return Response.custom(code=40101, msg=exception.userMessage,status_code=401)#40101表示被未携带Token

    @ExceptionHandler(AccessTokenExpiryException)
    async def handleAccessTokenExpiryException(self, request: Request, exception: AccessTokenExpiryException) -> ResponseModel:
        return Response.custom(code=40102, msg=exception.userMessage,status_code=401)#40102表示访问Token过期

    @ExceptionHandler(RefreshTokenExpiryException)
    async def handleRefreshTokenExpiryException(self, request: Request, exception: RefreshTokenExpiryException) -> ResponseModel:
        return Response.custom(code=40103, msg=exception.userMessage,status_code=401)#40103表示刷新Token过期


    @ExceptionHandler(InvalidTokenException)
    async def handleInvalidTokenError(self, request: Request, exception: InvalidTokenException) -> ResponseModel:
        return Response.custom(code=40104, msg=exception.userMessage,status_code=401)#40104表示Token无效

    @ExceptionHandler(UserNotFoundException)
    async def handleUserNotFoundException(self, request: Request, exception: UserNotFoundException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)

    @ExceptionHandler(PasswordIncorrectException)
    async def handlePasswordIncorrectException(self, request: Request, exception: PasswordIncorrectException)-> ResponseModel:
        return Response.error(msg=exception.userMessage)

    @ExceptionHandler(DataBaseException)
    async def handleDataBaseException(self, request: Request, exception: DataBaseException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)

    @ExceptionHandler(FilePermissionDeniedException)
    async def handleFilePermissionDeniedException(self, request: Request, exception: FilePermissionDeniedException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)

    @ExceptionHandler(BuiltinToolExecutionException)
    async def handleBuiltinToolExecutionException(self, request: Request,
                                                  exception: BuiltinToolExecutionException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)

    @ExceptionHandler(SecurityStatusReadException)
    async def handleSecurityStatusReadException(self, request: Request, exception: SecurityStatusReadException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)
    @ExceptionHandler(FileNotFoundException)
    async def handleFileNotFoundException(self, request: Request,
                                                  exception: FileNotFoundException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)

    @ExceptionHandler(FileAlreadyExistException)
    async def handleFileAlreadyExistException(self, request: Request,
                                          exception: FileAlreadyExistException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)

    @ExceptionHandler(FileTypeException)
    async def handleFileTypeException(self, request: Request,
                                          exception: FileTypeException) -> ResponseModel:
        return Response.error(msg=exception.userMessage)



