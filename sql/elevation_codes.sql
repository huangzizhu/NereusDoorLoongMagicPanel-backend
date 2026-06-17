-- 特权码审计日志（可选 — 持久化审计追踪用）
--
-- 核心状态机在 ElevationService 内存中运行（纯内存态，不入库）。
-- 此表仅用于事后审计查询，不参与运行时决策。
--
-- 注意: Hash 记录的是摘要，不是命令原文。
--       原文存储在 ElevationService 内存中，TTL 后自动销毁。

CREATE TABLE IF NOT EXISTS elevation_audit_log (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 来源
    code            VARCHAR(16) NOT NULL,
    session_id      VARCHAR(64) NOT NULL,

    -- 状态流转
    status          ENUM('pending', 'approved', 'rejected', 'expired', 'consumed')
                    NOT NULL DEFAULT 'pending',
    approved_by     VARCHAR(64),                     -- 谁 sudo approve 的
    reject_reason   VARCHAR(512),                    -- 拒绝原因

        -- 审批内容摘要
    commands_hash   VARCHAR(128),                    -- SHA256(commands_json)
    reason_hash     VARCHAR(128),                    -- SHA256(reason)
    command_count   INT NOT NULL DEFAULT 0,

    -- 双通道（Channel 1 / Channel 2）
    inline_cmd_hash     VARCHAR(128),                -- SHA256(inline_command)
    script_hash         VARCHAR(128),                -- SHA256(script_content)

    -- AI-SAST 审计结果
    audit_result        TEXT,                        -- JSON 审计报告
    audit_risk_level    VARCHAR(16),                 -- LOW/MEDIUM/HIGH/CRITICAL

    -- Token
    token_id        VARCHAR(64),                     -- 对应 JIT token

    -- 时间线
    requested_at    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    approved_at     DATETIME(3),
    expired_at      DATETIME(3),

    INDEX idx_code (code),
    INDEX idx_session (session_id),
    INDEX idx_token (token_id),
    INDEX idx_status (status),
    INDEX idx_requested (requested_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 特权操作执行日志（每次执行一条记录）
CREATE TABLE IF NOT EXISTS elevation_execution_log (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 关联
    code            VARCHAR(16) NOT NULL,
    token_id        VARCHAR(64) NOT NULL,
    session_id      VARCHAR(64) NOT NULL,

    -- 执行内容
    command         VARCHAR(128) NOT NULL,
    args_hash       VARCHAR(128),                    -- 校验 args 一致
    exit_code       INT,
    duration_ms     INT,

    -- 双通道记录
    cmd_hash        VARCHAR(128),                    -- Channel 1: inline command hash
    script_path     VARCHAR(512),                    -- Channel 2: script path
    script_hash     VARCHAR(128),                    -- Channel 2: script content hash

    -- 安全验证结果
    verdict         ENUM('allowed', 'denied_signature', 'denied_registry',
                         'denied_args_hash', 'denied_nonce', 'denied_peercred',
                         'denied_expired', 'denied_exhausted',
                         'denied_cmd_hash', 'denied_script_not_found',
                         'denied_script_hash', 'denied_script_blacklist')
                    DEFAULT 'allowed',

    -- 时间
    executed_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    INDEX idx_code (code),
    INDEX idx_token (token_id),
    INDEX idx_session (session_id),
    INDEX idx_verdict (verdict)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
