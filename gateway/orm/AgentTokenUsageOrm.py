from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from gateway.orm.OrmEngine import OrmEngine


class AgentTokenUsageOrm(OrmEngine().getBase()):
    __tablename__ = "agent_token_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionId = Column(String(64), ForeignKey("agent_sessions.sessionId"), nullable=False, index=True)
    traceId = Column(String(64), nullable=True, index=True)
    model = Column(String(100), nullable=False)

    # token 数量（仅存原始数据，不计费）
    inputTokens = Column(Integer, nullable=False, default=0)
    cachedInputTokens = Column(Integer, nullable=False, default=0)
    nonCachedInputTokens = Column(Integer, nullable=False, default=0)
    outputTokens = Column(Integer, nullable=False, default=0)
    totalTokens = Column(Integer, nullable=False, default=0)

    createdAt = Column(DateTime, default=datetime.now)
