from typing import List

from gateway.Singleton import singletonInit
from gateway.dao.TerminalDaoInterface import TerminalDaoInterface
from gateway.orm.OrmEngine import OrmEngine
from gateway.orm.TerminalSessionOrm import TerminalSessionOrm
from pojo.Terminal import TerminalSessionAdminAuthUpdate, TerminalSessionCloseUpdate, TerminalSessionLog, \
    TerminalSessionLogCreate


class TerminalDaoOrm(TerminalDaoInterface):
    @singletonInit
    def __init__(self):
        super().__init__("terminalDaoOrm")
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    def insertSession(self, sessionLog: TerminalSessionLogCreate):
        session = self.SessionLocal()
        try:
            orm = TerminalSessionOrm(**sessionLog.model_dump(exclude_none=True, exclude_unset=True))
            session.add(orm)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def markAdminAuthResult(self, updateRequest: TerminalSessionAdminAuthUpdate) -> int:
        session = self.SessionLocal()
        try:
            rowCount = (session.query(TerminalSessionOrm)
                        .filter(TerminalSessionOrm.sessionId == updateRequest.sessionId)
                        .update(updateRequest.model_dump(exclude_none=True, exclude_unset=True)))
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def closeSession(self, updateRequest: TerminalSessionCloseUpdate) -> int:
        session = self.SessionLocal()
        try:
            rowCount = (session.query(TerminalSessionOrm)
                        .filter(TerminalSessionOrm.sessionId == updateRequest.sessionId)
                        .update(updateRequest.model_dump(exclude_none=True, exclude_unset=True)))
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getTotal(self) -> int:
        session = self.SessionLocal()
        try:
            return session.query(TerminalSessionOrm).count()
        except Exception:
            raise
        finally:
            session.close()

    def getLog(self, page: int, pageSize: int) -> List[TerminalSessionLog]:
        session = self.SessionLocal()
        try:
            offset = max(page - 1, 0) * pageSize
            rows = (session.query(TerminalSessionOrm)
                    .order_by(TerminalSessionOrm.startTime.desc())
                    .offset(offset)
                    .limit(pageSize)
                    .all())
            return [TerminalSessionLog.model_validate(row) for row in rows]
        except Exception:
            raise
        finally:
            session.close()
