-- 完美匹配 Python 驼峰命名的 SQLite 建表语句
CREATE TABLE api_credentials (
    credentialId INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    apiKey TEXT NOT NULL,
    baseUrl TEXT,
    isActive INTEGER DEFAULT 1,
    quotaLimit REAL,
    usedQuota REAL DEFAULT 0.0,
    expireAt TEXT,
    lastUsedAt TEXT,
    description TEXT,
    createTime TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updateTime TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
