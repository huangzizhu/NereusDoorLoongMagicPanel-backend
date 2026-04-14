from datetime import datetime
from typing import List,Any
from pydantic import BaseModel, Field, ConfigDict

class ListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    items: List[Any] = Field(..., description="数据列表")

class PageSearchRequest(BaseModel):
    page: int = Field(..., description="当前页码", ge=0)
    pageSize: int = Field(..., description="每页记录数", ge=0)
