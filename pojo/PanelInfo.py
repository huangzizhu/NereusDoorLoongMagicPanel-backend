from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from ndlmpanel_agent.models.ops.monitor.system_monitor_models import (CpuInfo
,MemoryInfo,DiskPartitionInfo,GpuInfo,NetworkInterfaceInfo)
from typing import List
from pojo.Common import PageSearchRequest

# ==========================================
# 1. SystemHealth Schemas
# ==========================================
class SystemHealthBase(BaseModel):
    """基础模型：包含业务核心字段"""
    hostname: str = Field(..., description="主机名")
    cpuUsage: float = Field(..., ge=0, le=100, description="CPU使用率")
    memoryUsage: float = Field(..., ge=0, le=100, description="内存使用率")
    diskUsage: float = Field(..., ge=0, le=100, description="磁盘使用率")
    healthScore: int = Field(..., ge=0, le=100, description="健康评分")
    status: int = Field(..., ge=0, le=2, description="状态: 0正常 1警告 2异常")

class SystemHealth(SystemHealthBase):
    """响应模型：继承 Base，包含数据库生成的字段"""
    # 继承字段: hostname, cpuUsage, memoryUsage, diskUsage, networkLatency, healthScore, status
    id: int = Field(..., description="主键ID")
    createTime: datetime = Field(..., description="入库时间")

    model_config = ConfigDict(from_attributes=True)

class SystemHealthResponse(SystemHealthBase):
    cpuInfo: CpuInfo = Field(..., description="CPU详细信息对象")
    memoryInfo: MemoryInfo = Field(..., description="内存详细信息对象")
    gpuInfos: Optional[List[GpuInfo]] = Field(None,description="gpu，如果有")
    diskInfos: List[DiskPartitionInfo] = Field(default_factory=list, description="磁盘详细信息列表")
    networkInfos: List[NetworkInterfaceInfo] = Field(...,description="网卡信息")
# ==========================================
# 2. AlertEvent Schemas
# ==========================================
class AlertEventBase(BaseModel):
    """基础模型"""
    level: int = Field(..., ge=0, le=2, description="级别: 0Info 1Warning 2Error")
    message: str = Field(..., min_length=1, max_length=500, description="告警详情")
    status: int = Field(0, ge=0, le=2, description="状态: 0未读 1未处理 2已处理")


class AlertEvent(AlertEventBase):
    """响应模型"""
    # 继承字段: level, message, status
    id: int = Field(..., description="主键ID")
    createTime: datetime = Field(..., description="发生时间")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. AgentStatus Schemas
# ==========================================
class AgentStatusBase(BaseModel):
    """基础模型"""
    agentId: int = Field(..., description="Agent ID")
    currentTask: Optional[str] = Field(None, max_length=100, description="正在执行的任务名称")
    status: int = Field(..., ge=0, le=2, description="状态: 0离线 1在线 2忙碌")

class AgentStatus(AgentStatusBase):
    """响应模型"""
    # 继承字段: agentId, currentTask, status
    id: int = Field(..., description="主键ID")
    createTime: datetime = Field(..., description="上报时间")

    model_config = ConfigDict(from_attributes=True)

class SystemHealthQuery(BaseModel):
    """SSE 请求参数"""
    clientTimestamp: int = Field(..., description="客户端时间戳，用于计算延迟")
class AlertQuery(PageSearchRequest):
    """告警列表查询参数"""
    excludeProcessed: bool = Field(False, description="是否排除已处理的告警")