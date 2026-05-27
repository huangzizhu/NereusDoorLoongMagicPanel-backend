from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from pojo.Common import PageSearchRequest


TerminalMode = Literal["normal", "admin"]


class TerminalSessionLogBase(BaseModel):
    sessionId: str = Field(..., min_length=1, max_length=64, description="终端会话ID")
    userId: int = Field(..., ge=1, description="面板用户ID")
    panelUsername: str = Field(..., min_length=1, max_length=50, description="面板用户名")
    clientIp: str = Field(..., min_length=1, max_length=64, description="客户端IP")
    mode: TerminalMode = Field(..., description="当前终端模式")
    normalContainerName: str = Field(..., min_length=1, max_length=100, description="普通模式容器名")
    adminLinuxUsername: Optional[str] = Field(None, max_length=50, description="管理员模式Linux用户名")
    adminAuthAttempted: bool = Field(False, description="是否发起过管理员认证")
    adminAuthSucceeded: bool = Field(False, description="管理员认证是否成功")
    adminAuthFailedCount: int = Field(0, ge=0, description="管理员认证失败次数")
    startTime: datetime = Field(..., description="会话开始时间")
    endTime: Optional[datetime] = Field(None, description="会话结束时间")
    closeReason: Optional[str] = Field(None, max_length=100, description="关闭原因")
    exitCode: Optional[int] = Field(None, description="子进程退出码")


class TerminalSessionLogCreate(TerminalSessionLogBase):
    pass


class TerminalSessionAdminAuthUpdate(BaseModel):
    sessionId: str = Field(..., min_length=1, max_length=64)
    mode: TerminalMode = Field(..., description="认证后的终端模式")
    adminLinuxUsername: Optional[str] = Field(None, max_length=50)
    adminAuthAttempted: bool = Field(True)
    adminAuthSucceeded: bool = Field(..., description="管理员认证是否成功")
    adminAuthFailedCount: int = Field(..., ge=0)


class TerminalSessionCloseUpdate(BaseModel):
    sessionId: str = Field(..., min_length=1, max_length=64)
    mode: TerminalMode = Field(..., description="关闭时的终端模式")
    endTime: datetime = Field(..., description="会话结束时间")
    closeReason: str = Field(..., min_length=1, max_length=100)
    exitCode: Optional[int] = Field(None, description="子进程退出码")
    adminLinuxUsername: Optional[str] = Field(None, max_length=50)


class TerminalSessionLog(TerminalSessionLogBase):
    logId: int = Field(..., description="主键ID")
    model_config = ConfigDict(from_attributes=True)


class TerminalLogSearchRequest(PageSearchRequest):
    pass


class TerminalInputMessage(BaseModel):
    type: Literal["input"] = "input"
    data: str = Field(..., description="终端输入数据")


class TerminalResizeMessage(BaseModel):
    type: Literal["resize"] = "resize"
    cols: int = Field(..., ge=1, le=500, description="终端列数")
    rows: int = Field(..., ge=1, le=500, description="终端行数")


class TerminalAdminLoginMessage(BaseModel):
    type: Literal["admin_login"] = "admin_login"
    username: str = Field(..., min_length=1, max_length=50, description="Linux 用户名")
    password: str = Field(..., min_length=1, max_length=200, description="Linux 用户密码")


class TerminalOutputMessage(BaseModel):
    type: Literal["output"] = "output"
    data: str = Field(..., description="终端输出数据")


class TerminalStateMessage(BaseModel):
    type: Literal["state"] = "state"
    sessionId: str = Field(..., description="终端会话ID")
    mode: TerminalMode = Field(..., description="当前终端模式")
    linuxUser: str = Field(..., description="当前Linux用户")
    title: str = Field(..., description="终端标题")


class TerminalErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    code: str = Field(..., min_length=1, max_length=50, description="错误码")
    msg: str = Field(..., min_length=1, max_length=200, description="错误信息")


class TerminalAdminLoginResultMessage(BaseModel):
    type: Literal["admin_login_result"] = "admin_login_result"
    success: bool = Field(..., description="提权是否成功")
    mode: TerminalMode = Field(..., description="提权后的终端模式")
    msg: str = Field(..., min_length=1, max_length=200, description="结果说明")
