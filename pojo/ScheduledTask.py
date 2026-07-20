from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScheduledTaskApprovalPolicy(BaseModel):
    allowedTools: list[str] = Field(default_factory=list)
    allowedPaths: list[str] = Field(default_factory=list)
    deniedPaths: list[str] = Field(default_factory=list)
    allowedPrivilegedCommands: list[str] = Field(default_factory=list)
    ttlSeconds: int = Field(3600, ge=60, le=30 * 24 * 3600)
    maxRuns: int = Field(100, ge=1, le=100000)


class ScheduledTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    cronExpression: str = Field(..., min_length=1, max_length=100)
    taskDescription: str = Field(..., min_length=1)
    approvalPolicy: Optional[ScheduledTaskApprovalPolicy] = None


class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    cronExpression: Optional[str] = Field(None, min_length=1, max_length=100)
    taskDescription: Optional[str] = Field(None, min_length=1)
    approvalPolicy: Optional[ScheduledTaskApprovalPolicy] = None


class ScheduledTaskResponse(BaseModel):
    id: int
    name: str
    cronExpression: str
    taskDescription: str
    status: str
    createdBy: int
    approvalPolicy: Optional[Any] = None
    approvalCode: Optional[str] = None
    approvalStatus: Optional[str] = None
    approvalApprovedAt: Optional[datetime] = None
    approvalApprovedBy: Optional[str] = None
    approvalTokenId: Optional[str] = None
    approvalRejectedReason: Optional[str] = None
    nextRunAt: Optional[datetime] = None
    lastRunAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskRunResponse(BaseModel):
    id: int
    taskId: int
    sessionId: Optional[str] = None
    status: str
    startedAt: datetime
    finishedAt: Optional[datetime] = None
    resultSummary: Optional[str] = None
    errorMessage: Optional[str] = None
    tokenUsage: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)


class InspectionConfigUpdate(BaseModel):
    intervalMinutes: int = Field(..., ge=1, le=1440)


class InspectionReportResponse(BaseModel):
    id: int
    sessionId: Optional[str] = None
    status: str
    summary: Optional[str] = None
    findings: Optional[Any] = None
    fullReport: Optional[str] = None
    durationMs: int
    errorMessage: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)
