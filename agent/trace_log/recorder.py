"""事件记录器 — 审计链路追踪。"""
from __future__ import annotations
import logging
from datetime import datetime
from agent.trace_log.hash_chain import HashChain
from agent.trace_log.sanitizer import sanitize
from gateway.dao.AgentTraceDaoOrm import AgentTraceDaoOrm

_logger = logging.getLogger("ndlmpanel.trace")


class TraceRecorder:
    """TraceLog 事件记录器。

    统一写入主库（panel.db 的 agent_trace_logs 表）。
    哈希链：每个 session 独立链条。
    旧版 legacy SQLite（runtime/sqlite/traces.db）与 JSONL（runtime/traces/*.jsonl）
    双写已移除——主库已覆盖全部字段，双写只增加存储与权限问题。
    """

    def __init__(self, dbPath: str = "runtime/sqlite/traces.db",
                 jsonlDir: str = "runtime/traces"):
        # 兼容旧签名：dbPath / jsonlDir 不再使用，trace 统一写入主库
        self._mainStorage = AgentTraceDaoOrm()
        self._chains: dict[str, HashChain] = {}

    def record(self, traceId: str, sessionId: str,
               eventType: str, data: dict) -> str:
        """记录一条审计事件到主库 agent_trace_logs 表。

        Returns:
            本条记录的哈希值
        """
        timestamp = datetime.utcnow().timestamp()
        data = sanitize(data)
        eventTypeValue = eventType.value if hasattr(eventType, "value") else str(eventType)

        # 哈希链
        if sessionId not in self._chains:
            self._chains[sessionId] = HashChain()
        chain = self._chains[sessionId]
        prevHash = chain.prevHash
        entryHash = chain.hash({
            "trace_id": traceId, "session_id": sessionId,
            "event_type": eventTypeValue, "timestamp": timestamp,
            "data": data,
        })

        # 写入主库（agent_trace_logs 表）
        self._mainStorage.insert(traceId, sessionId, eventTypeValue,
                                 timestamp, data, entryHash, prevHash)

        _logger.debug("trace %s %s %s", traceId[:8], eventTypeValue, entryHash)
        return entryHash

    def query(self, traceId: str | None = None,
              sessionId: str | None = None, limit: int = 100) -> list[dict]:
        return self._mainStorage.query(traceId=traceId, sessionId=sessionId, limit=limit)

    def close(self) -> None:
        pass
