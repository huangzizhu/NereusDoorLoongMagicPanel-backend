import json
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.OrmEngine import OrmEngine
from gateway.orm.ToolAuthorizationOrm import (
    AUTH_REQ_STATUS_APPROVED,
    AUTH_REQ_STATUS_PENDING,
    ToolAuthorizationRequestOrm,
)


class ToolAuthorizationDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    # ── 序列化 ──

    @staticmethod
    def _loadJson(value: str | None):
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    @staticmethod
    def _toObj(row: ToolAuthorizationRequestOrm) -> SimpleNamespace:
        return SimpleNamespace(
            id=row.id,
            code=row.code,
            sessionId=row.sessionId,
            sourceType=row.sourceType,
            taskId=row.taskId,
            toolName=row.toolName,
            args=ToolAuthorizationDaoOrm._loadJson(row.argsJson),
            paths=ToolAuthorizationDaoOrm._loadJson(row.pathsJson),
            commandLine=row.commandLine,
            reason=row.reason,
            policyReason=row.policyReason,
            riskLevel=row.riskLevel,
            status=row.status,
            ttlSeconds=row.ttlSeconds,
            maxRuns=row.maxRuns,
            createdAt=row.createdAt,
            approvedAt=row.approvedAt,
            approvedBy=row.approvedBy,
            rejectReason=row.rejectReason,
            tokenId=row.tokenId,
            grant=ToolAuthorizationDaoOrm._loadJson(row.grantJson),
        )

    # ── 创建 ──

    def createRequest(
        self,
        *,
        code: str,
        sessionId: str,
        sourceType: str,
        toolName: str,
        args: dict | None = None,
        paths: list[str] | None = None,
        commandLine: str | None = None,
        reason: str | None = None,
        policyReason: str | None = None,
        riskLevel: str | None = None,
        ttlSeconds: int = 3600,
        maxRuns: int = 100,
        taskId: int | None = None,
    ) -> SimpleNamespace:
        session = self.SessionLocal()
        try:
            row = ToolAuthorizationRequestOrm(
                code=code,
                sessionId=sessionId,
                sourceType=sourceType,
                taskId=taskId,
                toolName=toolName,
                argsJson=json.dumps(args, ensure_ascii=False) if args is not None else None,
                pathsJson=json.dumps(paths, ensure_ascii=False) if paths else None,
                commandLine=commandLine,
                reason=reason,
                policyReason=policyReason,
                riskLevel=riskLevel,
                status=AUTH_REQ_STATUS_PENDING,
                ttlSeconds=ttlSeconds,
                maxRuns=maxRuns,
            )
            session.add(row)
            session.commit()
            result = self._toObj(row)
            session.expunge(row)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ── 查询 ──

    def findByCode(self, code: str) -> SimpleNamespace | None:
        session = self.SessionLocal()
        try:
            row = session.query(ToolAuthorizationRequestOrm).filter(
                ToolAuthorizationRequestOrm.code == code
            ).first()
            if row is None:
                return None
            result = self._toObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def findPendingBySessionAndTool(
        self, sessionId: str, toolName: str, commandLine: str | None = None
    ) -> SimpleNamespace | None:
        """同 session 内同一工具（同命令）的 pending 请求去重。"""
        session = self.SessionLocal()
        try:
            query = session.query(ToolAuthorizationRequestOrm).filter(
                ToolAuthorizationRequestOrm.sessionId == sessionId,
                ToolAuthorizationRequestOrm.toolName == toolName,
                ToolAuthorizationRequestOrm.status == AUTH_REQ_STATUS_PENDING,
            )
            if commandLine is not None:
                query = query.filter(
                    ToolAuthorizationRequestOrm.commandLine == commandLine
                )
            row = query.first()
            if row is None:
                return None
            result = self._toObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def listRequests(
        self, status: str | None = None, limit: int = 100
    ) -> list[SimpleNamespace]:
        session = self.SessionLocal()
        try:
            query = session.query(ToolAuthorizationRequestOrm)
            if status:
                query = query.filter(ToolAuthorizationRequestOrm.status == status)
            rows = query.order_by(
                ToolAuthorizationRequestOrm.createdAt.desc()
            ).limit(limit).all()
            result = [self._toObj(r) for r in rows]
            for row in rows:
                session.expunge(row)
            return result
        finally:
            session.close()

    def countPending(self) -> int:
        session = self.SessionLocal()
        try:
            return session.query(ToolAuthorizationRequestOrm).filter(
                ToolAuthorizationRequestOrm.status == AUTH_REQ_STATUS_PENDING
            ).count()
        finally:
            session.close()

    def listApproved(
        self,
        sessionId: str | None = None,
        taskId: int | None = None,
        sourceType: str | None = None,
    ) -> list[SimpleNamespace]:
        """已批准的授权请求（运行时动态白名单用）。

        过滤维度可组合：
        - sessionId: 同 session 内批准（本次运行内审批立即生效）
        - taskId + sourceType="scheduled": 该定时任务的所有已批准授权（跨运行持久）
        - sourceType="inspection": 巡检全局已批准授权（跨运行持久）
        """
        session = self.SessionLocal()
        try:
            query = session.query(ToolAuthorizationRequestOrm).filter(
                ToolAuthorizationRequestOrm.status == AUTH_REQ_STATUS_APPROVED,
            )
            if sessionId:
                query = query.filter(
                    ToolAuthorizationRequestOrm.sessionId == sessionId
                )
            if sourceType == "scheduled" and taskId is not None:
                query = query.filter(
                    ToolAuthorizationRequestOrm.sourceType == "scheduled",
                    ToolAuthorizationRequestOrm.taskId == taskId,
                )
            elif sourceType == "inspection":
                query = query.filter(
                    ToolAuthorizationRequestOrm.sourceType == "inspection"
                )
            rows = query.order_by(
                ToolAuthorizationRequestOrm.approvedAt.desc()
            ).all()
            result = [self._toObj(r) for r in rows]
            for row in rows:
                session.expunge(row)
            return result
        finally:
            session.close()

    # ── 更新 ──

    def updateStatus(
        self,
        code: str,
        status: str,
        *,
        approvedBy: str | None = None,
        rejectReason: str | None = None,
        tokenId: str | None = None,
        grant: dict[str, Any] | None = None,
    ) -> bool:
        session = self.SessionLocal()
        try:
            data: dict[str, Any] = {
                "status": status,
                "approvedAt": datetime.now() if status == "approved" else None,
            }
            if approvedBy is not None:
                data["approvedBy"] = approvedBy
            if rejectReason is not None:
                data["rejectReason"] = rejectReason
            if tokenId is not None:
                data["tokenId"] = tokenId
            if grant is not None:
                data["grantJson"] = json.dumps(grant, ensure_ascii=False)
            rowCount = session.query(ToolAuthorizationRequestOrm).filter(
                ToolAuthorizationRequestOrm.code == code
            ).update(data)
            session.commit()
            return rowCount > 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
