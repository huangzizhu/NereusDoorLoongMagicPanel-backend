CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    cronExpression VARCHAR(100) NOT NULL,
    taskDescription TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    createdBy INTEGER NOT NULL DEFAULT 0,
    nextRunAt DATETIME,
    lastRunAt DATETIME,
    createdAt DATETIME,
    updatedAt DATETIME
);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status
    ON scheduled_tasks(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_created_by
    ON scheduled_tasks(createdBy);
