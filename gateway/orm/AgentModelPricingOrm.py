from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

# 确保 api_credentials 表在 create_all 前注册到同一 Base
from gateway.orm.ApiKeyOrm import ApiCredentialOrm  # noqa: F401
from gateway.orm.OrmEngine import OrmEngine


class AgentModelPricingOrm(OrmEngine().getBase()):
    __tablename__ = "agent_model_pricing"
    __table_args__ = (
        UniqueConstraint("model", "credentialId", name="uq_model_credential"),
    )

    pricingId = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(100), nullable=False, index=True)
    inputPrice = Column(Float, nullable=False, default=1.0)
    cachedInputPrice = Column(Float, nullable=False, default=0.1)
    outputPrice = Column(Float, nullable=False, default=3.0)
    multiplier = Column(Float, nullable=False, default=1.0)
    credentialId = Column(Integer, ForeignKey("api_credentials.credentialId", ondelete="CASCADE"), nullable=True, index=True)
    isActive = Column(Integer, nullable=False, default=1)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)
