from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# ==========================================
# 1. 数据库历史记录模型
# ==========================================

class NetworkTrafficBase(BaseModel):
    """基础模型，包含公共字段"""
    interfaceName: str = Field(..., max_length=50, description="网卡名称")
    ipAddress: Optional[str] = Field(None, max_length=50, description="IP地址")
    macAddress: Optional[str] = Field(None, max_length=50, description="MAC地址")
    uploadSpeed: float = Field(..., ge=0, description="上传速率")
    downloadSpeed: float = Field(..., ge=0, description="下载速率")
    uploadTotal: Optional[int] = Field(None, ge=0, description="累计上传流量")
    downloadTotal: Optional[int] = Field(None, ge=0, description="累计下载流量")
    status: int = Field(default=1, ge=0, le=1, description="网卡状态：0-禁用, 1-启用")


class NetworkTrafficInDb(NetworkTrafficBase):
    """数据库返回模型，包含ID和创建时间"""
    id: int
    createTime: datetime = Field(alias="createTime", description="记录创建时间")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==========================================
# 2. SSE 实时传输模型
# ==========================================

class NetworkTrafficSSE(BaseModel):
    """
    SSE 实时推送模型
    用于向前端实时推送当前的网卡负载情况
    """
    interfaceName: str = Field(..., description="网卡名称")
    ipAddress: Optional[str] = Field(None, description="IP地址")
    macAddress: Optional[str] = Field(None, description="MAC地址")
    uploadSpeed: float = Field(..., description="实时上传速率")
    downloadSpeed: float = Field(..., description="实时下载速率")
    status: int = Field(..., description="当前状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="实时时间戳")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')})