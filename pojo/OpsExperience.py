from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


CategoryType = Literal["deployment", "fault", "optimization", "security", "negative"]
RiskLevelType = Literal["low", "medium", "high"]
StatusType = Literal["enabled", "disabled"]
SourceType = Literal["ai", "human"]


class OpsExperiencePackCreate(BaseModel):
    """创建经验包（人工录入，source=human）。"""

    title: str = Field(..., min_length=1, max_length=255, description="标题(一句话)")
    category: CategoryType = Field("deployment", description="deployment|fault|optimization|security|negative")
    osType: str = Field("通用", max_length=64, description="适用系统(麒麟/LoongArch/通用)")
    tags: list[str] = Field(default_factory=list, description="标签，如 [\"nginx\",\"ssl\"]")
    deploymentDoc: str = Field(..., min_length=1, description="正文 Markdown(部署/处置完整说明,主体)")
    stages: list[dict] = Field(default_factory=list, description="阶段: [{name, goal, steps[], verify, pitfallsRef[]}]")
    pitfalls: list[dict] = Field(default_factory=list, description="坑: [{phenomenon, cause, solution, stageRef|null}]")
    earlyWarnings: list[dict] = Field(
        default_factory=list,
        description="预警特征: [{metric, condition, threshold, severity, hint}]",
    )
    riskLevel: RiskLevelType = Field("medium", description="low|medium|high")
    status: StatusType = Field("enabled", description="enabled|disabled")


class OpsExperiencePackUpdate(BaseModel):
    """更新经验包（人工修改入口，version + 1）。全字段可选。"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[CategoryType] = None
    osType: Optional[str] = Field(None, max_length=64)
    tags: Optional[list[str]] = None
    deploymentDoc: Optional[str] = Field(None, min_length=1)
    stages: Optional[list[dict]] = None
    pitfalls: Optional[list[dict]] = None
    earlyWarnings: Optional[list[dict]] = None
    riskLevel: Optional[RiskLevelType] = None
    status: Optional[StatusType] = None


class OpsExperiencePackResponse(BaseModel):
    """经验包响应：含结构化字段 + 附件清单。"""

    id: int
    title: str
    category: str
    osType: str
    tags: Any = Field(default_factory=list)
    deploymentDoc: str
    stages: Any = Field(default_factory=list)
    pitfalls: Any = Field(default_factory=list)
    earlyWarnings: Any = Field(default_factory=list)
    riskLevel: str
    status: str
    source: str
    version: int
    sourceSessionId: Optional[str] = None
    hitCount: int
    usefulCount: int
    uselessCount: int
    qualityScore: int
    createdAt: datetime
    updatedAt: datetime
    attachments: list[Any] = Field(default_factory=list, description="附件清单（指针）")

    model_config = ConfigDict(from_attributes=True)


class OpsExperienceFeedbackRequest(BaseModel):
    """反馈：更新对应计数并重算 qualityScore。"""

    action: Literal["useful", "useless", "hit"]


class OpsExperienceSearchItem(BaseModel):
    """MCP searchOpsExperience 返回的单条结果。"""

    id: int
    title: str
    category: str
    osType: str
    tags: list[str] = Field(default_factory=list)
    riskLevel: str
    qualityScore: int
    hitCount: int
    summary: str = Field(..., description="deploymentDoc 首行摘要(截断)")
    negativeOf: Optional[str] = Field(None, description="negative 包针对的方案提示(二期增强)")


class OpsExperienceSubmit(BaseModel):
    """MCP submitOpsExperience 参数校验模型（source=ai）。"""

    title: str = Field(..., min_length=1, max_length=255)
    category: CategoryType = "deployment"
    deploymentDoc: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    stages: list[dict] = Field(default_factory=list)
    pitfalls: list[dict] = Field(default_factory=list)
    earlyWarnings: list[dict] = Field(default_factory=list)
    riskLevel: RiskLevelType = "medium"
    sourceSessionId: Optional[str] = None
