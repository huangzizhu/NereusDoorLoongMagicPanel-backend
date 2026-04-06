from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float
from gateway.orm.OrmEngine import OrmEngine
import datetime



class LogOrm(OrmEngine().getBase()):
    __tablename__ = 'logs'

    logId = Column(Integer, primary_key=True, autoincrement=True)  # 日志ID
    functionName = Column(String(100), nullable=False)  # 函数名称
    inputParams = Column(JSON, nullable=True)  # 入参，存储为 JSON 格式
    returnValue = Column(JSON, nullable=True)  # 返回值，存储为 JSON 格式
    userId = Column(Integer, nullable=False)  # 操作用户ID
    ipAddress = Column(String(50), nullable=False)  # 用户 IP 地址
    operationTime = Column(DateTime, default=datetime.datetime.utcnow)  # 操作时间
    executionTime = Column(Float, nullable=True)  # 执行时长（单位：秒）
    errorMessage = Column(Text)  # 异常信息
    requestPath = Column(String(200), nullable=False)  # 请求路径
    httpMethod = Column(String(20), nullable=False)  # HTTP 方法（GET, POST, etc.）