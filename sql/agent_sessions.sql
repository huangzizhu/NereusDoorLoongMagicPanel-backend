CREATE TABLE IF NOT EXISTS agent_sessions (
    sessionId TEXT PRIMARY KEY,
    userId INTEGER NOT NULL,
    title TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'agent',
    status TEXT NOT NULL DEFAULT 'idle',
    profileId INTEGER,
    toolSource TEXT NOT NULL DEFAULT 'current_mcp',
    mcpServers TEXT,
    safetyPolicy TEXT NOT NULL DEFAULT 'default',
    summary TEXT,
    lastError TEXT,
    createdAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updatedAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    finishedAt TEXT,
    FOREIGN KEY (profileId) REFERENCES agent_llm_profiles(profileId)
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_user ON agent_sessions(userId);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_updated ON agent_sessions(updatedAt);
