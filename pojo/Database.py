from pydantic import BaseModel, Field
from typing import Optional


class MysqlConnectionTestRequest(BaseModel):
    host: str = Field(..., min_length=1, max_length=255, description="MySQL 主机地址")
    port: int = Field(3306, ge=1, le=65535, description="MySQL 端口")
    username: str = Field(..., min_length=1, max_length=128, description="MySQL 用户名")
    password: str = Field(..., max_length=256, description="MySQL 密码")


class CreateDatabaseRequest(BaseModel):
    dbName: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", description="数据库名称")


class CreateUserRequest(BaseModel):
    dbName: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", description="数据库名称")
    username: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", description="用户名")
    password: str = Field(..., min_length=1, max_length=256, description="密码")
