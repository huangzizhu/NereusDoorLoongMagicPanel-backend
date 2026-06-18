from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SqlEnum
from sqlalchemy.orm import declarative_base
import enum
from gateway.orm.OrmEngine import OrmEngine



# 这里复用 Pydantic 的枚举，或者单独定义
class ProviderType(str, enum.Enum):
    OPENAI = "OpenAI"
    AZURE = "Azure"
    ANTHROPIC = "Anthropic"
    CUSTOM = "Custom"


class ApiCredentialOrm(OrmEngine().getBase()):
    __tablename__ = 'api_credentials'

    credentialId = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(50), nullable=False, comment="凭证别名")
    provider = Column(SqlEnum(ProviderType), nullable=False, comment="服务商")

    # 关键安全字段： apiKey 完整存储，需要加密（代码层面处理，此处仅定义存储结构）
    apiKey = Column(String(255), nullable=False, comment="API Key密文")

    baseUrl = Column(String(255), nullable=True, comment="Base URL")
    isActive = Column(Boolean, default=True, comment="是否启用")

    # 额度相关
    quotaLimit = Column(Float, nullable=True, comment="额度上限")
    usedQuota = Column(Float, default=0.0, comment="已用额度")

    # 时间相关
    expireAt = Column(DateTime, nullable=True, comment="过期时间")
    lastUsedAt = Column(DateTime, nullable=True, comment="最后调用时间")
    description = Column(String(255), nullable=True, comment="备注")

    createTime = Column(DateTime, default=datetime.now, comment="创建时间")
    updateTime = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<ApiCredentialOrm(name='{self.name}', provider='{self.provider}')>"