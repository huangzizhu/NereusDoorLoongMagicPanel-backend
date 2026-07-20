from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from gateway.orm.OrmEngine import OrmEngine


class InspectionReportOrm(OrmEngine().getBase()):
    __tablename__ = "inspection_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionId = Column(String(64), ForeignKey("agent_sessions.sessionId"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="running", index=True)
    summary = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    fullReport = Column(Text, nullable=True)
    durationMs = Column(Integer, nullable=False, default=0)
    errorMessage = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.now, index=True)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)
