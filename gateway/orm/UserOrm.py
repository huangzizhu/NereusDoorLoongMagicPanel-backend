from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from gateway.orm.OrmEngine import OrmEngine


class UserOrm(OrmEngine().getBase()):
    """用户表 ORM 模型"""
    __tablename__ = 'users'

    userId = Column( Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(50), nullable=False, unique=True, index=True, comment="用户名")
    email = Column(String(100), nullable=False, unique=True, index=True, comment="邮箱")
    hashedPassword = Column(String(60), nullable=False, comment="密码哈希")
    role = Column(String(20), nullable=False, default='viewer', comment="角色")
    status = Column(Boolean, nullable=False, default=True, comment="状态")

    # 登录限制相关字段
    loginFailedCount = Column(Integer, nullable=False, default=0, comment="登录失败次数")
    lockUntil = Column(DateTime, nullable=True, comment="锁定截止时间")

    lastLoginAt = Column(DateTime, nullable=True, comment="最后登录时间")
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updatedAt = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                       comment="更新时间")

    def __repr__(self):
        return f"<User(userId={self.userId}, username='{self.username}')>"