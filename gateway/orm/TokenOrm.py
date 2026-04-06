from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from datetime import datetime
from gateway.orm.OrmEngine import OrmEngine


class RefreshToken(OrmEngine().getBase()):
    __tablename__ = 'refresh_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.uid'), nullable=False)
    refreshToken = Column(String, nullable=False)
    ipAddress = Column(String)
    createdAt = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_refresh_tokens_userId', 'userId'),
    )
