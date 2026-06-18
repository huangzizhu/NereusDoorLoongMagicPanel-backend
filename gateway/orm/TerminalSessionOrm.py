from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from gateway.orm.OrmEngine import OrmEngine


class TerminalSessionOrm(OrmEngine().getBase()):
    __tablename__ = "terminal_session_logs"

    logId = Column(Integer, primary_key=True, autoincrement=True)
    sessionId = Column(String(64), nullable=False, unique=True, index=True)
    userId = Column(Integer, nullable=False, index=True)
    panelUsername = Column(String(50), nullable=False)
    clientIp = Column(String(64), nullable=False)
    mode = Column(String(20), nullable=False, default="normal")
    normalContainerName = Column(String(100), nullable=False)
    adminLinuxUsername = Column(String(50), nullable=True)
    adminAuthAttempted = Column(Boolean, nullable=False, default=False)
    adminAuthSucceeded = Column(Boolean, nullable=False, default=False)
    adminAuthFailedCount = Column(Integer, nullable=False, default=0)
    startTime = Column(DateTime, nullable=False, default=datetime.now)
    endTime = Column(DateTime, nullable=True)
    closeReason = Column(String(100), nullable=True)
    exitCode = Column(Integer, nullable=True)
