from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from datetime import datetime
from gateway.orm.OrmEngine import OrmEngine



class ProcessOperationLogOrm(OrmEngine().getBase()):
    """进程操作日志表"""
    __tablename__ = 'process_operation_logs'

    logId = Column(Integer, primary_key=True, autoincrement=True)
    operationType = Column(String(30), nullable=False)
    targetPids = Column(String(1000), nullable=False)
    operator = Column(String(50), nullable=False)
    reason = Column(String(500), nullable=True)
    result = Column(String(20), nullable=False)
    detail = Column(String(1000), nullable=True)
    createTime = Column(DateTime, nullable=False, default=datetime.now)