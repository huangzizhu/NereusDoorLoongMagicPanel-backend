CREATE TABLE IF NOT EXISTS agent_trace_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    traceId TEXT NOT NULL,
    sessionId TEXT NOT NULL,
    eventType TEXT NOT NULL,
    timestamp REAL NOT NULL,
    data TEXT NOT NULL,
    entryHash TEXT,
    prevHash TEXT,
    createdAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_agent_trace_logs_trace ON agent_trace_logs(traceId);
CREATE INDEX IF NOT EXISTS idx_agent_trace_logs_session ON agent_trace_logs(sessionId);
CREATE INDEX IF NOT EXISTS idx_agent_trace_logs_event ON agent_trace_logs(eventType);
CREATE INDEX IF NOT EXISTS idx_agent_trace_logs_time ON agent_trace_logs(timestamp);
