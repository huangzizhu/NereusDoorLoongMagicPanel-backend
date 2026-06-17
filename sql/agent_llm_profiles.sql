CREATE TABLE IF NOT EXISTS agent_llm_profiles (
    profileId INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    credentialId INTEGER NOT NULL,
    model TEXT NOT NULL,
    maxTokens INTEGER DEFAULT 4096,
    contextWindow INTEGER DEFAULT 1048576,
    temperature REAL DEFAULT 0.1,
    retryCount INTEGER DEFAULT 3,
    retryDelay REAL DEFAULT 2.0,
    isDefault INTEGER DEFAULT 0,
    isActive INTEGER DEFAULT 1,
    description TEXT,
    createTime TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updateTime TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (credentialId) REFERENCES api_credentials(credentialId)
);

CREATE INDEX IF NOT EXISTS idx_agent_llm_profiles_default ON agent_llm_profiles(isDefault);
CREATE INDEX IF NOT EXISTS idx_agent_llm_profiles_active ON agent_llm_profiles(isActive);
