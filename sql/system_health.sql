CREATE TABLE system_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    cpuUsage REAL NOT NULL,
    memoryUsage REAL NOT NULL,
    diskUsage REAL NOT NULL,
    healthScore INTEGER NOT NULL,
    status INTEGER NOT NULL DEFAULT 0, -- 0:正常 1:警告 2:异常
    createTime DATETIME NOT NULL DEFAULT (datetime('now', 'localtime'))
);