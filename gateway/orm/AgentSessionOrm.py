import json
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from gateway.orm.OrmEngine import OrmEngine


class AgentSessionOrm(OrmEngine().getBase()):
    __tablename__ = "agent_sessions"

    sessionId = Column(String(64), primary_key=True)
    userId = Column(Integer, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    mode = Column(String(32), nullable=False, default="agent")
    status = Column(String(32), nullable=False, default="idle")
    profileId = Column(Integer, ForeignKey("agent_llm_profiles.profileId"), nullable=True)
    toolSource = Column(String(50), nullable=False, default="current_mcp")
    mcpServersJson = Column("mcpServers", Text, nullable=True)
    safetyPolicy = Column(String(50), nullable=False, default="default")
    summary = Column(Text, nullable=True)
    lastError = Column(Text, nullable=True)
    pendingApproval = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    finishedAt = Column(DateTime, nullable=True)

    @property
    def mcpServers(self) -> list[dict] | None:
        if self.mcpServersJson is None:
            return None
        try:
            return json.loads(self.mcpServersJson)
        except (json.JSONDecodeError, TypeError):
            return None
