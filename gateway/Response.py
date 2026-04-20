from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, Union
from fastapi.encoders import jsonable_encoder


class ResponseModel(JSONResponse):
    def __init__(self, code: int, msg: str, data: Optional[Any] = None,status_code: int = 200):
        content = {
            "code": code,
            "msg": msg,
            "data": data
        }
        super().__init__(content=jsonable_encoder(content),status_code=status_code)


class Response:

    @staticmethod
    def success(data: Optional[Any] = None, msg: str = "success",status_code: int = 200) -> ResponseModel:
        """成功响应"""
        if msg is None:
            msg = "success"
        assert isinstance(msg, str)
        return ResponseModel(code=1, msg=msg, data=data, status_code=status_code)

    @staticmethod
    def error(data: Optional[Any] = None, msg: str | None= "error",status_code: int = 200) -> ResponseModel:
        """失败响应"""
        if msg is None:
            msg = "error"
        assert isinstance(msg, str)
        return ResponseModel(code=0, msg=msg, data=data, status_code=status_code)

    @staticmethod
    def custom(code: int = 1, data: Optional[Any] = None, msg: str | None = None, status_code: int = 200) -> ResponseModel:
        if msg is None:
            msg = "null"
        assert isinstance(msg, str)
        return ResponseModel(code=code, msg=msg, data=data, status_code=status_code)
