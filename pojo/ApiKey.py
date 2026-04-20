from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# 定义服务商枚举（便于后续扩展）
class ProviderEnum(str, Enum):
    OPENAI = "OpenAI"
    AZURE = "Azure"
    ANTHROPIC = "Anthropic"
    CUSTOM = "Custom"

# === Base 模型：包含公共字段 ===
class ApiCredentialBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="凭证别名")
    provider: ProviderEnum = Field(..., description="服务商类型")
    baseUrl: Optional[str] = Field(None, max_length=255, description="自定义请求地址")
    isActive: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, max_length=255, description="备注说明")
    quotaLimit: Optional[float] = Field(None, ge=0, description="预算额度限制")

# === Create 模型：创建时需要的字段 ===
class ApiCredentialCreate(ApiCredentialBase):
    apiKey: str = Field(..., min_length=10, max_length=255, description="完整的API Key")

# === Update 模型：更新时需要的字段（所有字段可选）===
class ApiCredentialUpdate(BaseModel):
    credentialId: int = Field(...,ge=1)
    name: Optional[str] = Field(None, max_length=50)
    baseUrl: Optional[str] = Field(None, max_length=255)
    isActive: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=255)
    quotaLimit: Optional[float] = Field(None, ge=0)

# 从数据库到响应模型的中间模型
class ApiCredentialOrm2pydantic(ApiCredentialBase):
    credentialId: int
    apiKey: str = Field(..., min_length=10, max_length=255, description="完整的API Key")
    usedQuota: float = Field(default=0.0, description="已使用额度")
    expireAt: Optional[datetime] = Field(None, description="过期时间")
    lastUsedAt: Optional[datetime] = Field(None, description="最后调用时间")
    createTime: datetime
    updateTime: datetime
    model_config = ConfigDict(from_attributes=True)
# === Response 模型：输出给前端的字段（注意排除敏感字段 apiKey）===
class ApiCredentialResponse(ApiCredentialBase):
    credentialId: int
    maskedKey: str = Field(..., description="脱敏后的Key")
    usedQuota: float = Field(default=0.0, description="已使用额度")
    expireAt: Optional[datetime] = Field(None, description="过期时间")
    lastUsedAt: Optional[datetime] = Field(None, description="最后调用时间")
    createTime: datetime
    updateTime: datetime

    model_config = ConfigDict(from_attributes=True)