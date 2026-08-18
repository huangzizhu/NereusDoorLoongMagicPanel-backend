from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentLlmProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    credentialId: int = Field(..., ge=1)
    model: str = Field(..., min_length=1, max_length=100)
    maxTokens: int = Field(default=4096, ge=1, le=393216)
    contextWindow: int = Field(default=1048576, ge=1, le=10485760)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    retryCount: int = Field(default=3, ge=0)
    retryDelay: float = Field(default=2.0, ge=0.0)
    isDefault: bool = False
    isActive: bool = True
    description: Optional[str] = Field(None, max_length=255)


class AgentLlmProfileCreate(AgentLlmProfileBase):
    pass


class AgentLlmProfileBatchCreate(BaseModel):
    credentialId: int = Field(..., ge=1)
    models: list[str] = Field(..., min_length=1)
    namePrefix: Optional[str] = Field(None, min_length=1, max_length=80)
    maxTokens: int = Field(default=4096, ge=1, le=393216)
    contextWindow: int = Field(default=1048576, ge=1, le=10485760)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    retryCount: int = Field(default=3, ge=0)
    retryDelay: float = Field(default=2.0, ge=0.0)
    isDefaultFirst: bool = False
    isActive: bool = True
    description: Optional[str] = Field(None, max_length=255)


class AgentLlmProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    credentialId: Optional[int] = Field(None, ge=1)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    maxTokens: Optional[int] = Field(None, ge=1, le=393216)
    contextWindow: Optional[int] = Field(None, ge=1, le=10485760)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    retryCount: Optional[int] = Field(None, ge=0)
    retryDelay: Optional[float] = Field(None, ge=0.0)
    isDefault: Optional[bool] = None
    isActive: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=255)


class AgentLlmProfileOrm2Pydantic(AgentLlmProfileBase):
    profileId: int
    createTime: datetime
    updateTime: datetime
    credentialName: Optional[str] = None
    credentialProvider: Optional[str] = None
    credentialBaseUrl: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AgentLlmProfileResponse(AgentLlmProfileOrm2Pydantic):
    pass


class AgentLlmModelInfo(BaseModel):
    id: str
    name: Optional[str] = None
    ownedBy: Optional[str] = None
    raw: Optional[dict] = None


class AgentLlmCredentialModelsResponse(BaseModel):
    credentialId: int
    credentialName: str
    credentialProvider: str
    credentialBaseUrl: str
    sourceUrl: str
    models: list[AgentLlmModelInfo]


class AgentLlmProfileTestResponse(BaseModel):
    profileId: int
    credentialId: int
    model: str
    available: bool
    latencyMs: float
    content: Optional[str] = None
    finishReason: Optional[str] = None
    usage: dict = Field(default_factory=dict)
    error: Optional[str] = None


class AgentSessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(default="新 Agent 会话", min_length=1, max_length=100)
    mode: str = Field(default="agent", max_length=32)
    profileId: Optional[int] = Field(None, ge=1)
    toolSource: Literal["current_mcp", "stdio"] = "current_mcp"
    safetyPolicy: str = Field(default="default", max_length=50)
    source: str = Field(default="manual", max_length=32,
                        description="会话来源: manual / scheduled / inspection")
    mcpServers: Optional[list["McpServerSpec"]] = None


class McpServerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    command: list[str] = Field(..., min_length=1, description="argv style command")
    cwd: Optional[str] = Field(None, min_length=1, max_length=500)


class AgentToolSourceSwitch(BaseModel):
    toolSource: Literal["current_mcp", "stdio"]
    mcpServers: Optional[list[McpServerSpec]] = None


class AgentModelSwitch(BaseModel):
    profileId: int


class AgentModeSwitch(BaseModel):
    """切换 Agent 运行模式请求。"""
    model_config = ConfigDict(extra="forbid")
    mode: str = Field(..., max_length=32,
                      description="目标模式: read_only / plan / agent / break_glass")


class AgentSessionResponse(BaseModel):
    sessionId: str
    title: str
    mode: str
    status: str
    source: str = "manual"
    profileId: Optional[int] = None
    toolSource: Literal["current_mcp", "stdio"]
    safetyPolicy: str
    mcpServers: Optional[list[McpServerSpec]] = None
    summary: Optional[str] = None
    lastError: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    finishedAt: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AgentStatusItem(BaseModel):
    """最近 Agent 对话的轻量状态，用于首页状态卡片。"""

    sessionId: str
    title: str
    status: str
    source: str = "manual"
    summary: Optional[str] = None
    lastError: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    finishedAt: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AgentMessageResponse(BaseModel):
    messageId: int
    sessionId: str
    role: str
    content: Optional[str] = None          # nullable: assistant with only tool_calls
    toolCallId: Optional[str] = None        # tool role: tool_call_id
    traceId: Optional[str] = None
    roundIndex: int
    metadata: Optional[Any] = Field(default=None, validation_alias="metadataJson")
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentTokenUsageResponse(BaseModel):
    id: int
    sessionId: str
    traceId: Optional[str] = None
    model: str
    inputTokens: int
    cachedInputTokens: int = 0
    nonCachedInputTokens: int = 0
    outputTokens: int
    totalTokens: int
    cachedInputCost: float = 0.0
    nonCachedInputCost: float = 0.0
    inputCost: float
    outputCost: float
    totalCost: float
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentSessionBillingResponse(BaseModel):
    sessionId: str
    totalInputTokens: int = 0
    totalCachedInputTokens: int = 0
    totalNonCachedInputTokens: int = 0
    totalOutputTokens: int = 0
    totalTokens: int = 0
    totalCachedInputCost: float = 0.0
    totalNonCachedInputCost: float = 0.0
    totalInputCost: float = 0.0
    totalOutputCost: float = 0.0
    totalCost: float = 0.0
    callCount: int = 0


class AgentTraceLogResponse(BaseModel):
    id: int
    traceId: str
    sessionId: str
    eventType: str
    timestamp: float
    data: Any
    entryHash: Optional[str] = None
    prevHash: Optional[str] = None
    createdAt: datetime


class AgentTraceTimelineItem(BaseModel):
    id: int
    traceId: str
    sessionId: str
    eventType: str
    stage: str
    timestamp: float
    data: Any


class AgentTraceSummary(BaseModel):
    sessionId: str
    totalEvents: int
    toolCalls: int
    approvalCount: int
    hasInjection: bool
    traces: list[str]
