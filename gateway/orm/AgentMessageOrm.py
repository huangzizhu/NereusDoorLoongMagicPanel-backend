from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from gateway.orm.OrmEngine import OrmEngine


class AgentMessageOrm(OrmEngine().getBase()):
    __tablename__ = "agent_messages"

    messageId = Column(Integer, primary_key=True, autoincrement=True)
    sessionId = Column(String(64), ForeignKey("agent_sessions.sessionId"), nullable=False, index=True)
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=True)                 # nullable: assistant with only tool_calls
    toolCallId = Column(String(64), nullable=True)        # tool role: tool_call_id
    traceId = Column(String(64), nullable=True, index=True)
    roundIndex = Column(Integer, nullable=False, default=0)
    metadataJson = Column("metadata", Text, nullable=True)  # JSON: tool_calls[] for assistant, tool_name for tool
    createdAt = Column(DateTime, default=datetime.now)
