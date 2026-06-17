-- Agent 模型定价表
-- 支持官方全局价（credentialId IS NULL）和用户凭证自定义价
--
-- 价格查询优先级：
--   1. 匹配 model + credentialId（用户自定义价）
--   2. 匹配 model + credentialId IS NULL（官方全局价）
--   3. 代码默认值 (input=1.0, cached=0.1, output=3.0)

CREATE TABLE IF NOT EXISTS agent_model_pricing (
    pricingId INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,                             -- 模型名，如 "deepseek-v4-flash"
    inputPrice REAL NOT NULL DEFAULT 1.0,            -- 非缓存输入价格（¥/百万 tokens）
    cachedInputPrice REAL NOT NULL DEFAULT 0.1,       -- 缓存命中输入价格（¥/百万 tokens）
    outputPrice REAL NOT NULL DEFAULT 3.0,            -- 输出价格（¥/百万 tokens）
    multiplier REAL NOT NULL DEFAULT 1.0,             -- 倍率（默认 1.0）
    credentialId INTEGER,                             -- NULL = 官方价；非 NULL = 该凭证的自定义价
    isActive INTEGER NOT NULL DEFAULT 1,
    createdAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updatedAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (credentialId) REFERENCES api_credentials(credentialId) ON DELETE CASCADE,
    UNIQUE(model, credentialId)
);

CREATE INDEX IF NOT EXISTS idx_model_pricing_model ON agent_model_pricing(model);
CREATE INDEX IF NOT EXISTS idx_model_pricing_credential ON agent_model_pricing(credentialId);

-- 种子数据：官方全局价（从 DeepSeek 官网获取）
INSERT OR IGNORE INTO agent_model_pricing(model, inputPrice, cachedInputPrice, outputPrice, multiplier, credentialId)
VALUES
    ('deepseek-v4-flash', 1.0, 0.02, 2.0, 1.0, NULL),
    ('deepseek-v4-pro', 3.0, 0.025, 6.0, 1.0, NULL),
    ('deepseek-chat', 1.0, 0.02, 2.0, 1.0, NULL),
    ('deepseek-reasoner', 3.0, 0.025, 6.0, 1.0, NULL),
    ('qwen-plus', 0.8, 0.08, 2.0, 1.0, NULL),
    ('qwen-max', 2.0, 0.2, 6.0, 1.0, NULL),
    ('gpt-4o-mini', 0.15, 0.03, 0.6, 1.0, NULL),
    ('gpt-4o', 2.5, 0.5, 10.0, 1.0, NULL),
    ('claude-3-haiku', 0.25, 0.025, 1.25, 1.0, NULL),
    ('claude-3.5-sonnet', 3.0, 0.3, 15.0, 1.0, NULL);
