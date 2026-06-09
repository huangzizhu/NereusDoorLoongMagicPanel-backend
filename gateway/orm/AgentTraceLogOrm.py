from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from gateway.orm.OrmEngine import OrmEngine


class AgentTraceLogOrm(OrmEngine().getBase()):
    __tablename__ = "agent_trace_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    traceId = Column(String(64), nullable=False, index=True)
    sessionId = Column(String(64), nullable=False, index=True)
    eventType = Column(String(80), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    data = Column(Text, nullable=False)
    entryHash = Column(String(64), nullable=True)
    prevHash = Column(String(64), nullable=True)
    createdAt = Column(DateTime, default=datetime.now)
