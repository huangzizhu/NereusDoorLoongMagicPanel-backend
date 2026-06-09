CREATE TABLE IF NOT EXISTS agent_messages (
    messageId INTEGER PRIMARY KEY AUTOINCREMENT,
    sessionId TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,                              -- nullable: assistant with only tool_calls
    toolCallId TEXT,                           -- tool role: tool_call_id reference
    traceId TEXT,
    roundIndex INTEGER NOT NULL DEFAULT 0,
    metadata TEXT,                             -- JSON: tool_calls[] for assistant, tool_name for tool
    createdAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (sessionId) REFERENCES agent_sessions(sessionId)
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(sessionId);
CREATE INDEX IF NOT EXISTS idx_agent_messages_trace ON agent_messages(traceId);
CREATE INDEX IF NOT EXISTS idx_agent_messages_round ON agent_messages(sessionId, roundIndex);
