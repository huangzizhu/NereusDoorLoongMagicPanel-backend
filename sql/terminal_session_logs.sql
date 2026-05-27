CREATE TABLE IF NOT EXISTS terminal_session_logs (
    logId INTEGER PRIMARY KEY AUTOINCREMENT,
    sessionId VARCHAR(64) NOT NULL UNIQUE,
    userId INTEGER NOT NULL,
    panelUsername VARCHAR(50) NOT NULL,
    clientIp VARCHAR(64) NOT NULL,
    mode VARCHAR(20) NOT NULL DEFAULT 'normal',
    normalContainerName VARCHAR(100) NOT NULL,
    adminLinuxUsername VARCHAR(50),
    adminAuthAttempted BOOLEAN NOT NULL DEFAULT 0,
    adminAuthSucceeded BOOLEAN NOT NULL DEFAULT 0,
    adminAuthFailedCount INTEGER NOT NULL DEFAULT 0,
    startTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endTime DATETIME,
    closeReason VARCHAR(100),
    exitCode INTEGER
);
