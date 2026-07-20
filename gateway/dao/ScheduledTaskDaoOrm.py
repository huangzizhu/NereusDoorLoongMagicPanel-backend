import json
from datetime import datetime
from types import SimpleNamespace

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentLlmProfileOrm import AgentLlmProfileOrm  # noqa: F401
from gateway.orm.AgentSessionOrm import AgentSessionOrm  # noqa: F401
from gateway.orm.OrmEngine import OrmEngine
from gateway.orm.ScheduledTaskOrm import ScheduledTaskOrm, ScheduledTaskRunOrm
from pojo.ScheduledTask import ScheduledTaskCreate


class ScheduledTaskDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    @staticmethod
    def _loadJson(value: str | None):
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    @staticmethod
    def _taskToObj(row: ScheduledTaskOrm) -> SimpleNamespace:
        return SimpleNamespace(
            id=row.id,
            name=row.name,
            cronExpression=row.cronExpression,
            taskDescription=row.taskDescription,
            status=row.status,
            createdBy=row.createdBy,
            approvalPolicy=ScheduledTaskDaoOrm._loadJson(row.approvalPolicy),
            approvalCode=row.approvalCode,
            approvalStatus=row.approvalStatus,
            approvalApprovedAt=row.approvalApprovedAt,
            approvalApprovedBy=row.approvalApprovedBy,
            approvalTokenId=row.approvalTokenId,
            approvalRejectedReason=row.approvalRejectedReason,
            nextRunAt=row.nextRunAt,
            lastRunAt=row.lastRunAt,
            createdAt=row.createdAt,
            updatedAt=row.updatedAt,
        )

    @staticmethod
    def _runToObj(row: ScheduledTaskRunOrm) -> SimpleNamespace:
        tokenUsage = None
        if row.tokenUsage:
            try:
                tokenUsage = json.loads(row.tokenUsage)
            except (json.JSONDecodeError, TypeError):
                tokenUsage = row.tokenUsage
        return SimpleNamespace(
            id=row.id,
            taskId=row.taskId,
            sessionId=row.sessionId,
            status=row.status,
            startedAt=row.startedAt,
            finishedAt=row.finishedAt,
            resultSummary=row.resultSummary,
            errorMessage=row.errorMessage,
            tokenUsage=tokenUsage,
        )

    def createTask(
        self,
        userId: int,
        body: ScheduledTaskCreate,
        *,
        status: str = "active",
        approvalCode: str | None = None,
        approvalStatus: str | None = None,
    ) -> SimpleNamespace:
        session = self.SessionLocal()
        try:
            approval_policy = (
                body.approvalPolicy.model_dump(mode="json")
                if body.approvalPolicy is not None else None
            )
            row = ScheduledTaskOrm(
                name=body.name,
                cronExpression=body.cronExpression,
                taskDescription=body.taskDescription,
                status=status,
                createdBy=userId,
                approvalPolicy=json.dumps(approval_policy, ensure_ascii=False)
                if approval_policy is not None else None,
                approvalCode=approvalCode,
                approvalStatus=approvalStatus,
            )
            session.add(row)
            session.commit()
            result = self._taskToObj(row)
            session.expunge(row)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getTask(self, taskId: int, userId: int | None = None) -> SimpleNamespace | None:
        session = self.SessionLocal()
        try:
            query = session.query(ScheduledTaskOrm).filter(ScheduledTaskOrm.id == taskId)
            if userId is not None:
                query = query.filter(ScheduledTaskOrm.createdBy == userId)
            row = query.one_or_none()
            if row is None:
                return None
            result = self._taskToObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def listTasks(
        self,
        userId: int | None = None,
        status: str | None = None,
        includeDeleted: bool = False,
    ) -> list[SimpleNamespace]:
        session = self.SessionLocal()
        try:
            query = session.query(ScheduledTaskOrm)
            if userId is not None:
                query = query.filter(ScheduledTaskOrm.createdBy == userId)
            if status:
                query = query.filter(ScheduledTaskOrm.status == status)
            elif not includeDeleted:
                query = query.filter(ScheduledTaskOrm.status != "deleted")
            rows = query.order_by(ScheduledTaskOrm.createdAt.desc()).all()
            result = [self._taskToObj(row) for row in rows]
            for row in rows:
                session.expunge(row)
            return result
        finally:
            session.close()

    def listActiveTasks(self) -> list[SimpleNamespace]:
        return self.listTasks(status="active")

    def updateTask(self, taskId: int, data: dict, userId: int | None = None) -> int:
        if not data:
            return 0
        if "approvalPolicy" in data:
            policy = data["approvalPolicy"]
            data["approvalPolicy"] = (
                json.dumps(policy, ensure_ascii=False) if policy is not None else None
            )
        session = self.SessionLocal()
        try:
            data["updatedAt"] = datetime.now()
            query = session.query(ScheduledTaskOrm).filter(ScheduledTaskOrm.id == taskId)
            if userId is not None:
                query = query.filter(ScheduledTaskOrm.createdBy == userId)
            count = query.update(data)
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def setNextRunAt(self, taskId: int, nextRunAt: datetime | None) -> int:
        return self.updateTask(taskId, {"nextRunAt": nextRunAt})

    def markLastRun(self, taskId: int) -> int:
        return self.updateTask(taskId, {"lastRunAt": datetime.now()})

    def createRun(self, taskId: int) -> SimpleNamespace:
        session = self.SessionLocal()
        try:
            row = ScheduledTaskRunOrm(taskId=taskId, status="running")
            session.add(row)
            session.commit()
            result = self._runToObj(row)
            session.expunge(row)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def finishRun(
        self,
        runId: int,
        sessionId: str | None,
        status: str,
        resultSummary: str | None,
        errorMessage: str | None,
        tokenUsage: dict | None,
    ) -> int:
        session = self.SessionLocal()
        try:
            count = session.query(ScheduledTaskRunOrm).filter(
                ScheduledTaskRunOrm.id == runId
            ).update({
                "sessionId": sessionId,
                "status": status,
                "finishedAt": datetime.now(),
                "resultSummary": resultSummary,
                "errorMessage": errorMessage,
                "tokenUsage": json.dumps(tokenUsage, ensure_ascii=False, default=str)
                if tokenUsage is not None else None,
            })
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getRun(self, runId: int) -> SimpleNamespace | None:
        session = self.SessionLocal()
        try:
            row = session.query(ScheduledTaskRunOrm).filter(
                ScheduledTaskRunOrm.id == runId
            ).one_or_none()
            if row is None:
                return None
            result = self._runToObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def listRuns(self, taskId: int, limit: int = 50) -> list[SimpleNamespace]:
        session = self.SessionLocal()
        try:
            rows = session.query(ScheduledTaskRunOrm).filter(
                ScheduledTaskRunOrm.taskId == taskId
            ).order_by(ScheduledTaskRunOrm.startedAt.desc()).limit(limit).all()
            result = [self._runToObj(row) for row in rows]
            for row in rows:
                session.expunge(row)
            return result
        finally:
            session.close()
