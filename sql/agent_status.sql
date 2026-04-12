-- Agent状态表
CREATE TABLE agent_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agentId INTEGER NOT NULL,
    currentTask TEXT, -- 可为空
    status INTEGER NOT NULL DEFAULT 0, -- 0:离线 1:在线 2:忙碌
    createTime DATETIME NOT NULL DEFAULT (datetime('now', 'localtime'))
);

INSERT INTO agent_status (agentId, currentTask, status, createTime)
VALUES
(1, '数据分析任务', 1, datetime('now', 'localtime', '-1 hour')),
(1, '模型微调中', 2, datetime('now', 'localtime', '-30 minute')),
(1, NULL, 0, datetime('now', 'localtime', '-2 hour'));