import json
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentLlmProfileOrm import AgentLlmProfileOrm  # noqa: F401
from gateway.orm.AgentSessionOrm import AgentSessionOrm  # noqa: F401
from gateway.orm.InspectionReportOrm import InspectionReportOrm
from gateway.orm.OrmEngine import OrmEngine


class InspectionReportDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    @staticmethod
    def _toObj(row: InspectionReportOrm) -> SimpleNamespace:
        findings: Any = None
        if row.findings:
            try:
                findings = json.loads(row.findings)
            except (json.JSONDecodeError, TypeError):
                findings = row.findings
        return SimpleNamespace(
            id=row.id,
            sessionId=row.sessionId,
            status=row.status,
            summary=row.summary,
            findings=findings,
            fullReport=row.fullReport,
            durationMs=row.durationMs,
            errorMessage=row.errorMessage,
            createdAt=row.createdAt,
            updatedAt=row.updatedAt,
        )

    def createReport(
        self,
        sessionId: str | None,
        status: str,
        summary: str | None,
        findings: Any,
        fullReport: str | None,
        durationMs: int,
        errorMessage: str | None = None,
    ) -> SimpleNamespace:
        session = self.SessionLocal()
        try:
            row = InspectionReportOrm(
                sessionId=sessionId,
                status=status,
                summary=summary,
                findings=json.dumps(findings, ensure_ascii=False, default=str)
                if findings is not None else None,
                fullReport=fullReport,
                durationMs=durationMs,
                errorMessage=errorMessage,
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

    def getReport(self, reportId: int) -> SimpleNamespace | None:
        session = self.SessionLocal()
        try:
            row = session.query(InspectionReportOrm).filter(
                InspectionReportOrm.id == reportId
            ).one_or_none()
            if row is None:
                return None
            result = self._toObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def latestReport(self) -> SimpleNamespace | None:
        session = self.SessionLocal()
        try:
            row = session.query(InspectionReportOrm).order_by(
                InspectionReportOrm.createdAt.desc()
            ).first()
            if row is None:
                return None
            result = self._toObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def listReports(self, page: int, pageSize: int) -> tuple[int, list[SimpleNamespace]]:
        session = self.SessionLocal()
        try:
            query = session.query(InspectionReportOrm)
            total = query.count()
            rows = query.order_by(InspectionReportOrm.createdAt.desc()).offset(
                max(page - 1, 0) * pageSize
            ).limit(pageSize).all()
            result = [self._toObj(row) for row in rows]
            for row in rows:
                session.expunge(row)
            return total, result
        finally:
            session.close()

    def findBySessionId(self, sessionId: str) -> SimpleNamespace | None:
        """按执行会话反查巡检报告（授权写回用）。"""
        session = self.SessionLocal()
        try:
            row = session.query(InspectionReportOrm).filter(
                InspectionReportOrm.sessionId == sessionId
            ).order_by(InspectionReportOrm.createdAt.desc()).first()
            if row is None:
                return None
            result = self._toObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()
