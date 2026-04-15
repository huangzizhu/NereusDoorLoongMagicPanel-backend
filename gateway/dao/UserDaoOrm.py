from typing import Optional

from sqlalchemy import or_

from gateway.Singleton import singletonInit
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.orm.OrmEngine import OrmEngine
from gateway.orm.UserOrm import UserOrm


class UserDaoOrm(UserDaoInterface):
    @singletonInit
    def __init__(self):
        super().__init__('logDaoOrm')
        self.engine = OrmEngine()
        # 保存 Session 工厂
        self.SessionLocal = self.engine.createSessionFactory()


    def getUserByAccount(self, account: str) -> Optional[UserOrm]:
        session = self.SessionLocal()
        try:
            return (session.query(UserOrm).filter(or_(
                UserOrm.username == account,
                UserOrm.email == account
            )).one_or_none())
        except Exception:
            raise
        finally:
            session.close()