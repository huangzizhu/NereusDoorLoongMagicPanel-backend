CREATE TABLE IF NOT EXISTS scheduled_task_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taskId INTEGER NOT NULL,
    sessionId VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'running',
    startedAt DATETIME,
    finishedAt DATETIME,
    resultSummary TEXT,
    errorMessage TEXT,
    tokenUsage TEXT,
    FOREIGN KEY(taskId) REFERENCES scheduled_tasks(id),
    FOREIGN KEY(sessionId) REFERENCES agent_sessions(sessionId)
);

CREATE INDEX IF NOT EXISTS idx_scheduled_task_runs_task
    ON scheduled_task_runs(taskId);
CREATE INDEX IF NOT EXISTS idx_scheduled_task_runs_session
    ON scheduled_task_runs(sessionId);
CREATE INDEX IF NOT EXISTS idx_scheduled_task_runs_started
    ON scheduled_task_runs(startedAt);
