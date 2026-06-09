"""事件记录器 — 审计链路追踪。"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from agent.trace_log.storage import TraceStorage
from agent.trace_log.hash_chain import HashChain
from agent.trace_log.sanitizer import sanitize
from gateway.dao.AgentTraceDaoOrm import AgentTraceDaoOrm

_logger = logging.getLogger("ndlmpanel.trace")


class TraceRecorder:
    """TraceLog 事件记录器。

    双写：JSONL 文件 + SQLite 数据库。
    哈希链：每个 session 独立链条。
    """

    def __init__(self, dbPath: str = "runtime/sqlite/traces.db",
                 jsonlDir: str = "runtime/traces"):
        self._storage = TraceStorage(dbPath)
        self._mainStorage = AgentTraceDaoOrm()
        self._jsonlDir = jsonlDir
        self._chains: dict[str, HashChain] = {}
        os.makedirs(jsonlDir, exist_ok=True)

    def record(self, traceId: str, sessionId: str,
               eventType: str, data: dict) -> str:
        """记录一条审计事件。

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

        # Main DB + legacy SQLite.
        self._mainStorage.insert(traceId, sessionId, eventTypeValue,
                                 timestamp, data, entryHash, prevHash)
        self._storage.insert(traceId, sessionId, eventTypeValue,
                             timestamp, data, entryHash, prevHash)

        # JSONL
        entry = json.dumps({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trace_id": traceId, "session_id": sessionId,
            "event": eventTypeValue, "data": data,
            "entry_hash": entryHash, "prev_hash": prevHash,
        }, ensure_ascii=False)
        jsonlPath = os.path.join(self._jsonlDir,
                                 datetime.utcnow().strftime("%Y-%m-%d") + ".jsonl")
        with open(jsonlPath, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

        _logger.debug("trace %s %s %s", traceId[:8], eventTypeValue, entryHash)
        return entryHash

    def query(self, traceId: str | None = None,
              sessionId: str | None = None, limit: int = 100) -> list[dict]:
        return self._mainStorage.query(traceId=traceId, sessionId=sessionId, limit=limit)

    def close(self) -> None:
        self._storage.close()
