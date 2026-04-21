from sqlalchemy import func
from typing import List
from gateway.Singleton import singletonInit
from gateway.dao.SystemInfoDaoInterface import SystemInfoDaoInterface
from gateway.orm.OrmEngine import OrmEngine
from pojo.PanelInfo import AlertEvent,AlertQuery
from gateway.orm.PanelInfoOrm import AlertEventOrm


class SystemInfoDao(SystemInfoDaoInterface):
    @singletonInit
    def __init__(self):
        super().__init__('systemInfoDaoOrm')
        self.engine = OrmEngine()
        # 保存 Session 工厂
        self.SessionLocal = self.engine.createSessionFactory()

    def getAllSystemAlertsCount(self, excludeProcessed: bool) -> int:
        session = self.SessionLocal()
        try:
            if excludeProcessed:
                return session.query(func.count(AlertEventOrm.id)).filter(AlertEventOrm.status != 2).scalar()
            return session.query(func.count(AlertEventOrm.id)).scalar()
        except Exception:
            raise
        finally:
            session.close()

    def getAllSystemAlerts(self, alertQuery: AlertQuery) -> List[AlertEvent]:
        session = self.SessionLocal()
        try:
            sql = session.query(AlertEventOrm)
            if alertQuery.excludeProcessed:
                sql = sql.filter(AlertEventOrm.status != 2)
            if alertQuery.page or alertQuery.pageSize:#分页
                sql = sql.offset((alertQuery.page - 1) * alertQuery.pageSize).limit(alertQuery.pageSize)
            alertOrms: List[AlertEventOrm]  =  sql.all()
            return [AlertEvent.model_validate(alertOrm) for alertOrm in alertOrms]
        except Exception:
            raise
        finally:
            session.close()

    def setAlertsRead(self, id: int) -> int:
        session = self.SessionLocal()
        try:
            countRow: int = session.query(AlertEventOrm).filter(AlertEventOrm.id == id).update({"status": 1})
            session.commit()
            return countRow
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def setAlertsProcess(self, id: int) -> int:
        session = self.SessionLocal()
        try:
            countRow: int = session.query(AlertEventOrm).filter(AlertEventOrm.id == id).update({"status": 2})
            session.commit()
            return countRow
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getAlertEventById(self, id: int) -> AlertEvent:
        session = self.SessionLocal()
        try:
            return session.query(AlertEventOrm).filter(AlertEventOrm.id == id).one_or_none()
        except Exception:
            raise
        finally:
            session.close()









