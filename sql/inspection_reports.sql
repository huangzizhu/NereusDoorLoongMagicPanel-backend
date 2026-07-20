CREATE TABLE IF NOT EXISTS inspection_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sessionId VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'running',
    summary TEXT,
    findings TEXT,
    fullReport TEXT,
    durationMs INTEGER NOT NULL DEFAULT 0,
    errorMessage TEXT,
    createdAt DATETIME,
    updatedAt DATETIME,
    FOREIGN KEY(sessionId) REFERENCES agent_sessions(sessionId)
);

CREATE INDEX IF NOT EXISTS idx_inspection_reports_session
    ON inspection_reports(sessionId);
CREATE INDEX IF NOT EXISTS idx_inspection_reports_status
    ON inspection_reports(status);
CREATE INDEX IF NOT EXISTS idx_inspection_reports_created
    ON inspection_reports(createdAt);
