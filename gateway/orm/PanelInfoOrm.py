from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from gateway.orm.OrmEngine import OrmEngine



class SystemHealthOrm(OrmEngine().getBase()):
    """系统健康度 ORM 模型"""
    __tablename__ = 'system_health'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    hostname = Column(String(50), nullable=False, comment='主机名')
    cpuUsage = Column(Float, nullable=False, comment='CPU使用率')
    memoryUsage = Column(Float, nullable=False, comment='内存使用率')
    diskUsage = Column(Float, nullable=False, comment='磁盘使用率')
    healthScore = Column(Integer, nullable=False, comment='健康评分')
    # 0:正常 1:警告 2:异常
    status = Column(Integer, nullable=False, default=0, comment='状态')
    createTime = Column(DateTime, nullable=False, default=datetime.now, comment='入库时间')
class AlertEventOrm(OrmEngine().getBase()):
    """告警事件 ORM 模型"""
    __tablename__ = 'alert_events'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    # 0:Info 1:Warning 2:Error
    level = Column(Integer, nullable=False, default=1, comment='告警级别')
    message = Column(String(500), nullable=False, comment='告警详情')
    # 0:未读 1:未处理 2:已处理
    status = Column(Integer, nullable=False, default=0, comment='处理状态')
    createTime = Column(DateTime, nullable=False, default=datetime.now, comment='发生时间')
class AgentStatusOrm(OrmEngine().getBase()):
    """Agent状态 ORM 模型"""
    __tablename__ = 'agent_status'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    # 假设关联的外键表存在，这里只做字段定义，实际需配合 AgentInfo 表
    agentId = Column(Integer, nullable=False, comment='Agent ID (外键)')
    currentTask = Column(String(100), nullable=True, comment='正在执行的任务名称')
    # 0:离线 1:在线 2:忙碌
    status = Column(Integer, nullable=False, default=0, comment='运行状态')
    createTime = Column(DateTime, nullable=False, default=datetime.now, comment='上报时间')

