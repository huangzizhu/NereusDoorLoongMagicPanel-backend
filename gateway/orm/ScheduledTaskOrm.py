from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from gateway.orm.OrmEngine import OrmEngine


class ScheduledTaskOrm(OrmEngine().getBase()):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    cronExpression = Column(String(100), nullable=False)
    taskDescription = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="active", index=True)
    createdBy = Column(Integer, nullable=False, default=0, index=True)
    approvalPolicy = Column(Text, nullable=True)
    approvalCode = Column(String(32), nullable=True, index=True)
    approvalStatus = Column(String(32), nullable=True, index=True)
    approvalApprovedAt = Column(DateTime, nullable=True)
    approvalApprovedBy = Column(String(100), nullable=True)
    approvalTokenId = Column(String(128), nullable=True)
    approvalRejectedReason = Column(Text, nullable=True)
    nextRunAt = Column(DateTime, nullable=True)
    lastRunAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ScheduledTaskRunOrm(OrmEngine().getBase()):
    __tablename__ = "scheduled_task_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    taskId = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False, index=True)
    sessionId = Column(String(64), ForeignKey("agent_sessions.sessionId"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="running", index=True)
    startedAt = Column(DateTime, default=datetime.now, index=True)
    finishedAt = Column(DateTime, nullable=True)
    resultSummary = Column(Text, nullable=True)
    errorMessage = Column(Text, nullable=True)
    tokenUsage = Column(Text, nullable=True)
