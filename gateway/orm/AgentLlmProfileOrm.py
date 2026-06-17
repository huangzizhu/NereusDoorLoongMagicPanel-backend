from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from gateway.orm.OrmEngine import OrmEngine


class AgentLlmProfileOrm(OrmEngine().getBase()):
    __tablename__ = "agent_llm_profiles"

    profileId = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    credentialId = Column(Integer, ForeignKey("api_credentials.credentialId"), nullable=False)
    model = Column(String(100), nullable=False)
    maxTokens = Column(Integer, default=4096)
    contextWindow = Column(Integer, default=1048576)
    temperature = Column(Float, default=0.1)
    retryCount = Column(Integer, default=3)
    retryDelay = Column(Float, default=2.0)
    isDefault = Column(Boolean, default=False)
    isActive = Column(Boolean, default=True)
    description = Column(String(255), nullable=True)
    createTime = Column(DateTime, default=datetime.now)
    updateTime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
