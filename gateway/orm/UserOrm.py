from sqlalchemy import Column, Integer, String

from gateway.orm.OrmEngine import OrmEngine


class UserOrm(OrmEngine().getBase()):
    __tablename__ = "user"

    uid = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(64), unique=True, nullable=False)
    hashedPassword = Column(String(256), nullable=False)