
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from gateway.orm.OrmEngine import OrmEngine
from datetime import datetime


class TokenOrm(OrmEngine().getBase()):
    __tablename__ = 'RefreshTokens'

    tokenId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('users.userId'), nullable=False)
    refreshToken = Column(String, nullable=False)
    expireIn = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(Integer, default=1, comment="1: 有效 2：过期 3：已撤销")



    def __repr__(self):
        return f"<RefreshToken(tokenId={self.tokenId}, userId={self.userId}, refreshToken={self.refreshToken}, expireIn={self.expireIn}, status={self.status})>"