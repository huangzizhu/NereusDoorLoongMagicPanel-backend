from typing import Optional, Literal
from pydantic import BaseModel, Field, conint, ConfigDict
from datetime import datetime

class Log(BaseModel):
    logId: Optional[int]
    functionName: str
    inputParams: Optional[dict]
    returnValue: Optional[dict]
    userId: Optional[int]
    ipAddress: str
    operationTime: Optional[datetime]
    executionTime: Optional[float]
    errorMessage: Optional[str]
    requestPath: str
    httpMethod: str
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True  # 去除前后空白
    )
