from typing import Optional

from gateway.Singleton import singletonInit
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.orm.OrmEngine import OrmEngine
from gateway.orm.UserOrm import UserOrm


class UserDaoOrm(UserDaoInterface):
    @singletonInit
    def __init__(self):
        super().__init__("userDaoOrm")
        self.ormEngine = OrmEngine()
        self.SessionLocal = self.ormEngine.createSessionFactory()
        UserOrm.__table__.create(bind=self.ormEngine.engine, checkfirst=True)
        self._ensureDefaultUser()

    def _ensureDefaultUser(self):
        session = self.SessionLocal()
        try:
            user = session.query(UserOrm).filter(UserOrm.account == "admin").first()
            if user is None:
                session.add(UserOrm(account="admin", hashedPassword="123456"))
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getUserByAccount(self, account: str) -> Optional[UserOrm]:
        session = self.SessionLocal()
        try:
            return session.query(UserOrm).filter(UserOrm.account == account).first()
        except Exception:
            raise
        finally:
            session.close()