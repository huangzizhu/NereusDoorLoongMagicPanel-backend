CREATE TABLE IF NOT EXISTS file_operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    userId INTEGER NOT NULL,
    operationType INTEGER NOT NULL, -- 1:上传, 2:删除, 3:批量删除, 4:修改权限
    targetPath VARCHAR(1024) NOT NULL,
    detail VARCHAR(500),
    result VARCHAR(255) NOT NULL,
    operateTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ipAddress VARCHAR(50),
    FOREIGN KEY (userId) REFERENCES users(userId)
);