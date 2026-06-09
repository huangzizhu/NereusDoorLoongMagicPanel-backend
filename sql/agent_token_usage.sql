CREATE TABLE IF NOT EXISTS agent_token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sessionId TEXT NOT NULL,
    traceId TEXT,
    model TEXT NOT NULL,
    inputTokens INTEGER NOT NULL DEFAULT 0,
    outputTokens INTEGER NOT NULL DEFAULT 0,
    totalTokens INTEGER NOT NULL DEFAULT 0,
    inputCost REAL NOT NULL DEFAULT 0.0,       -- ¥ 元
    outputCost REAL NOT NULL DEFAULT 0.0,      -- ¥ 元
    totalCost REAL NOT NULL DEFAULT 0.0,       -- ¥ 元
    createdAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (sessionId) REFERENCES agent_sessions(sessionId)
);

CREATE INDEX IF NOT EXISTS idx_token_usage_session ON agent_token_usage(sessionId);
CREATE INDEX IF NOT EXISTS idx_token_usage_trace ON agent_token_usage(traceId);
