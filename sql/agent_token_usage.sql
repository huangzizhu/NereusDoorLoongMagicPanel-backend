-- Agent Token 用量表（仅存原始 token 数，不计费）
-- 计费在查询时动态计算，通过 agent_model_pricing 表查找价格
--
-- 计算公式（读时计算）：
--   nonCachedInputCost = nonCachedInputTokens / 1_000_000 × inputPrice × multiplier
--   cachedInputCost    = cachedInputTokens    / 1_000_000 × cachedInputPrice × multiplier
--   outputCost         = outputTokens         / 1_000_000 × outputPrice × multiplier

CREATE TABLE IF NOT EXISTS agent_token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sessionId TEXT NOT NULL,
    traceId TEXT,
    model TEXT NOT NULL,
    inputTokens          INTEGER NOT NULL DEFAULT 0,   -- 总输入 = cached + nonCached
    cachedInputTokens    INTEGER NOT NULL DEFAULT 0,   -- 缓存命中 tokens
    nonCachedInputTokens INTEGER NOT NULL DEFAULT 0,   -- 未命中缓存 tokens
    outputTokens         INTEGER NOT NULL DEFAULT 0,
    totalTokens          INTEGER NOT NULL DEFAULT 0,
    createdAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (sessionId) REFERENCES agent_sessions(sessionId)
);

CREATE INDEX IF NOT EXISTS idx_token_usage_session ON agent_token_usage(sessionId);
CREATE INDEX IF NOT EXISTS idx_token_usage_trace ON agent_token_usage(traceId);
