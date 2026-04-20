from typing import Optional

from sqlalchemy import or_

from gateway.Singleton import singletonInit
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.orm.TokenOrm import TokenOrm
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
        except Exception as e:
            raise e
        finally:
            session.close()

    def insertTokens(self, tokenOrm: TokenOrm):
        session = self.SessionLocal()
        try:
            session.add(tokenOrm)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def deleteTokensByRefreshToken(self, refreshToken: str)  -> int:
        session = self.SessionLocal()
        try:
            row = session.query(TokenOrm).filter(TokenOrm.refreshToken == refreshToken).update({"status": 3})
            session.commit()
            return row
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deactivateTokensByRefreshToken(self, refreshToken: str)  -> int:
        session = self.SessionLocal()
        try:
            row = session.query(TokenOrm).filter(TokenOrm.refreshToken == refreshToken).update({"status": 2})
            session.commit()
            return row
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getUserByRefreshToken(self, refreshToken) -> UserOrm | None:
        session = self.SessionLocal()
        try:
            token: TokenOrm = session.query(TokenOrm).filter(TokenOrm.refreshToken == refreshToken, TokenOrm.status == 1).one_or_none()
            if token is None:
                return None
            user: UserOrm = session.query(UserOrm).filter(UserOrm.userId == token.userId).one_or_none()
            return user
        except Exception:
            raise
        finally:
            session.close()