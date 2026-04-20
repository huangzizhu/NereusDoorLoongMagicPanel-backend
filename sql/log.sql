CREATE TABLE logs (
    logId INTEGER PRIMARY KEY AUTOINCREMENT,       -- 日志 ID
    functionName TEXT NOT NULL,                    -- 函数名称
    inputParams TEXT,                              -- 入参（JSON 格式）
    returnValue TEXT,                              -- 返回值（JSON 格式）
    userId INTEGER NOT NULL,                       -- 用户 ID
    ipAddress TEXT NOT NULL,                       -- 用户 IP 地址
    operationTime DATETIME DEFAULT CURRENT_TIMESTAMP, -- 操作时间
    executionTime REAL,                            -- 执行时长（单位：秒）
    errorMessage TEXT,                             -- 错误信息（如果有的话）
    requestPath TEXT NOT NULL,                     -- 请求路径
    httpMethod TEXT NOT NULL                      -- HTTP 方法（GET, POST, etc.）
);