import json
from collections import Counter
from typing import Any

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentTraceLogOrm import AgentTraceLogOrm
from gateway.orm.OrmEngine import OrmEngine


_STAGE_MAP = {
    "input.received": "接收指令",
    "llm.request": "推理决策",
    "llm.response": "推理决策",
    "safety.check": "安全校验",
    "approval.requested": "人工审批",
    "approval.resolved": "人工审批",
    "tool.result": "执行结果",
    "injection.detected": "注入风险",
    "session.done": "闭环完成",
}


class AgentTraceDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    def insert(self, traceId: str, sessionId: str, eventType: str,
               timestamp: float, data: dict, entryHash: str | None = None,
               prevHash: str | None = None) -> int:
        session = self.SessionLocal()
        try:
            orm = AgentTraceLogOrm(
                traceId=traceId,
                sessionId=sessionId,
                eventType=eventType,
                timestamp=timestamp,
                data=json.dumps(data, ensure_ascii=False),
                entryHash=entryHash,
                prevHash=prevHash,
            )
            session.add(orm)
            session.commit()
            return orm.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def query(self, sessionId: str | None = None,
              traceId: str | None = None,
              eventType: str | None = None,
              limit: int = 100,
              ascending: bool = False) -> list[dict[str, Any]]:
        session = self.SessionLocal()
        try:
            query = session.query(AgentTraceLogOrm)
            if sessionId:
                query = query.filter(AgentTraceLogOrm.sessionId == sessionId)
            if traceId:
                query = query.filter(AgentTraceLogOrm.traceId == traceId)
            if eventType:
                query = query.filter(AgentTraceLogOrm.eventType == eventType)
            order = AgentTraceLogOrm.timestamp.asc() if ascending else AgentTraceLogOrm.id.desc()
            rows = query.order_by(order).limit(limit).all()
            return [self._rowToDict(row) for row in rows]
        finally:
            session.close()

    def timeline(self, sessionId: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.query(sessionId=sessionId, limit=limit, ascending=True)
        for row in rows:
            row["stage"] = _STAGE_MAP.get(row["eventType"], row["eventType"])
        return rows

    def summary(self, sessionId: str) -> dict[str, Any]:
        rows = self.query(sessionId=sessionId, limit=10000, ascending=True)
        counts = Counter(row["eventType"] for row in rows)
        return {
            "sessionId": sessionId,
            "totalEvents": len(rows),
            "toolCalls": counts.get("tool.result", 0),
            "approvalCount": (
                counts.get("approval.requested", 0)
                + counts.get("approval.resolved", 0)
            ),
            "hasInjection": counts.get("injection.detected", 0) > 0,
            "traces": sorted({row["traceId"] for row in rows}),
        }

    @staticmethod
    def _rowToDict(row: AgentTraceLogOrm) -> dict[str, Any]:
        try:
            data = json.loads(row.data)
        except Exception:
            data = row.data
        return {
            "id": row.id,
            "traceId": row.traceId,
            "sessionId": row.sessionId,
            "eventType": row.eventType,
            "timestamp": row.timestamp,
            "data": data,
            "entryHash": row.entryHash,
            "prevHash": row.prevHash,
            "createdAt": row.createdAt,
        }
