from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from utils.toolFunction.models.ops.process.process_models import ProcessInfo

# ==================== 操作日志相关模型 ====================

class ProcessOperationLogBase(BaseModel):
    """日志基础字段"""
    operationType: str = Field(..., max_length=30, description="操作类型: KILL, FORCE_KILL, BATCH_KILL, AUTO_CLEAN等")
    targetPids: str = Field(..., max_length=1000, description="目标PID列表, 逗号分隔")
    operator: str = Field(..., max_length=50, description="操作人/触发源")
    reason: Optional[str] = Field(None, max_length=500, description="操作原因")
    result: str = Field(..., max_length=20, description="执行结果: SUCCESS, PARTIAL_SUCCESS, FAILED")
    detail: Optional[str] = Field(None, max_length=1000, description="详细信息/报错")



class ProcessOperationLog(ProcessOperationLogBase):
    """日志响应模型"""
    logId: int
    createTime: datetime
    model_config = ConfigDict(from_attributes=True)


# ==================== API 请求模型 ====================

class KillProcessRequest(BaseModel):
    """杀进程请求"""
    pid: int
    reason: Optional[str] = Field(None, max_length=500)


class BatchKillProcessRequest(BaseModel):
    """批量杀进程请求"""
    pids: List[int] = Field(..., min_length=1, description="待杀死的PID列表")
    reason: Optional[str] = Field(None, max_length=500)


class AutoCleanRequest(BaseModel):
    """自动清理请求"""
    cpuThreshold: float = Field(90.0, description="CPU占用阈值 (%)", gt=30)
    memoryThreshold: float = Field(80.0, description="内存占用阈值 (%)",gt=30)
