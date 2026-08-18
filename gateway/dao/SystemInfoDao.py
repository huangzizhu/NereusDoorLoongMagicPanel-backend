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
                return int(session.query(func.count(AlertEventOrm.id)).filter(AlertEventOrm.status != 2).scalar() or 0)
            return int(session.query(func.count(AlertEventOrm.id)).scalar() or 0)
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
            sql = sql.order_by(
                AlertEventOrm.createTime.desc(),
                AlertEventOrm.id.desc(),
            )
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

    def getAlertEventById(self, id: int) -> AlertEvent | None:
        session = self.SessionLocal()
        try:
            alertOrm = session.query(AlertEventOrm).filter(AlertEventOrm.id == id).one_or_none()
            return AlertEvent.model_validate(alertOrm) if alertOrm is not None else None
        except Exception:
            raise
        finally:
            session.close()

    def createAlert(self, level: int, message: str) -> AlertEvent:
        """创建一条告警记录（0:Info 1:Warning 2:Error）。

        供 Agent 安全链路（金丝雀泄露、注入分类拦截等）写入告警。
        message 超出列宽 500 时截断，避免 DB 报错。
        """
        session = self.SessionLocal()
        try:
            orm = AlertEventOrm(
                level=int(level),
                message=str(message)[:500],
                status=0,
            )
            session.add(orm)
            session.commit()
            session.refresh(orm)
            return AlertEvent.model_validate(orm)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()







