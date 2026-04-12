-- 告警事件表
CREATE TABLE alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INTEGER NOT NULL DEFAULT 1, -- 0:Info 1:Warning 2:Error
    message TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 0, -- 0:未读 1:未处理 2:已处理
    createTime DATETIME NOT NULL DEFAULT (datetime('now', 'localtime'))
);
-- 告警数据
INSERT INTO alert_events (level, message, status, createTime)
VALUES
(1, 'CPU使用率超过80%，请检查', 0, datetime('now', 'localtime', '-5 minute')), -- 未读
(2, '数据库连接失败', 1, datetime('now', 'localtime')), -- 未处理
(0, '系统重启完成', 2, datetime('now', 'localtime', '-10 minute')); -- 已处理