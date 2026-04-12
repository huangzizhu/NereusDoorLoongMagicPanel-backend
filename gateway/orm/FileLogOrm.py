from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from gateway.orm.OrmEngine import OrmEngine

class FileOperationLogOrm(OrmEngine().getBase()):
    """文件操作日志表"""
    __tablename__ = 'file_operation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('users.userId'), nullable=False, comment="操作用户ID")
    operationType = Column(Integer, nullable=False, comment="操作类型:1上传,2删除,3批量删除,4改权限")
    targetPath = Column(String(1024), nullable=False, comment="目标路径")
    detail = Column(String(500), nullable=True, comment="详情")
    result = Column(String(255), nullable=False, comment="操作结果")
    operateTime = Column(DateTime, nullable=False, default=datetime.now, comment="操作时间")
    ipAddress = Column(String(50), nullable=True, comment="IP地址")

    # 可选：关联用户对象
    # user = relationship("UserOrm", backref="operation_logs")