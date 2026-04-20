CREATE TABLE RefreshTokens (
    tokenId INTEGER PRIMARY KEY AUTOINCREMENT,
    userId INTEGER NOT NULL,
    refreshToken TEXT NOT NULL,
    expireIn DATETIME NOT NULL,
    createdAt DATETIME DEFAULT (datetime('now')),
    updatedAt DATETIME DEFAULT (datetime('now')),
    status INTEGER DEFAULT 1,-- 1: 有效 2：过期 3：已撤销
    FOREIGN KEY (userId) REFERENCES users(userId)
);