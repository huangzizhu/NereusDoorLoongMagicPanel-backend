"""SQLite 存储 — 审计日志持久化。"""
from __future__ import annotations
import json
import os
import sqlite3


class TraceStorage:
    """SQLite 审计日志存储。"""

    def __init__(self, dbPath: str = "runtime/sqlite/traces.db"):
        self._dbPath = dbPath
        self._initDb()

    def _initDb(self) -> None:
        parent = os.path.dirname(self._dbPath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with sqlite3.connect(self._dbPath) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    data TEXT NOT NULL,
                    entry_hash TEXT,
                    prev_hash TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trace_id ON traces(trace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON traces(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON traces(event_type)")

    def insert(self, traceId: str, sessionId: str, eventType: str,
               timestamp: float, data: dict, entryHash: str | None = None,
               prevHash: str | None = None) -> None:
        with sqlite3.connect(self._dbPath) as conn:
            conn.execute(
                "INSERT INTO traces (trace_id, session_id, event_type, timestamp, data, entry_hash, prev_hash) VALUES (?,?,?,?,?,?,?)",
                (traceId, sessionId, eventType, timestamp,
                 json.dumps(data, ensure_ascii=False), entryHash, prevHash),
            )

    def query(self, traceId: str | None = None, sessionId: str | None = None,
              limit: int = 100) -> list[dict]:
        with sqlite3.connect(self._dbPath) as conn:
            conn.row_factory = sqlite3.Row
            if traceId:
                rows = conn.execute(
                    "SELECT * FROM traces WHERE trace_id=? ORDER BY id DESC LIMIT ?",
                    (traceId, limit),
                ).fetchall()
            elif sessionId:
                rows = conn.execute(
                    "SELECT * FROM traces WHERE session_id=? ORDER BY id DESC LIMIT ?",
                    (sessionId, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM traces ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def close(self) -> None:
        pass
