from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from gateway.orm.OrmEngine import OrmEngine


class AgentTokenUsageOrm(OrmEngine().getBase()):
    __tablename__ = "agent_token_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionId = Column(String(64), ForeignKey("agent_sessions.sessionId"), nullable=False, index=True)
    traceId = Column(String(64), nullable=True, index=True)
    model = Column(String(100), nullable=False)
    inputTokens = Column(Integer, nullable=False, default=0)
    outputTokens = Column(Integer, nullable=False, default=0)
    totalTokens = Column(Integer, nullable=False, default=0)
    inputCost = Column(Float, nullable=False, default=0.0)
    outputCost = Column(Float, nullable=False, default=0.0)
    totalCost = Column(Float, nullable=False, default=0.0)
    createdAt = Column(DateTime, default=datetime.now)
