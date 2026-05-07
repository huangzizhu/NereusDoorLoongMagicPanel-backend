from Singleton import Singleton, singletonInit
from gateway.dao.ProcessDaoInterface import ProcessDaoInterface
from orm.OrmEngine import OrmEngine
from gateway.orm.ProcessOrm import ProcessOperationLogOrm
from pojo.Process import ProcessOperationLog
from typing import List

class ProcessDaoOrm(ProcessDaoInterface):

    @singletonInit
    def __init__(self):
        super().__init__('processDaoOrm')
        self.engine = OrmEngine()
        # 保存 Session 工厂
        self.SessionLocal = self.engine.createSessionFactory()


    def addLog(self, data: ProcessOperationLogOrm):
        session = self.SessionLocal()
        try:
            session.add(data)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getTotal(self) -> int:
        session = self.SessionLocal()
        try:
            return session.query(ProcessOperationLogOrm).count()
        except Exception:
            raise
        finally:
            session.close()

    def getLog(self, page, pageSize) -> List[ProcessOperationLog]:
        session = self.SessionLocal()
        try:
            orms: List[ProcessOperationLogOrm]
            if page == 0 and pageSize == 0:
                orms = session.query(ProcessOperationLogOrm).all()
            else:
                orms  = session.query(ProcessOperationLogOrm).offset((page - 1) * pageSize).limit(pageSize).all()
            return [ProcessOperationLog.model_validate(orm) for orm in orms]
        except Exception:
            raise
        finally:
            session.close()