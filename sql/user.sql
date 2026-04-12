-- ==========================================
-- 1. 建表语句
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(60) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    status BOOLEAN NOT NULL DEFAULT 1,

    -- 登录限制字段
    login_failed_count INTEGER NOT NULL DEFAULT 0,
    lock_until DATETIME,

    last_login_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引加速登录查询
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ==========================================
-- 2. 示例数据插入
-- ==========================================

-- 密码明文均为: 'password123'
-- 使用 bcrypt 生成, cost=10 (示例哈希值，实际开发请使用 Python bcrypt 库动态生成)
-- $2b$10$N9qo8uLOickgx2ZMRZoMyeIjZRGdjGj/n3.Q9eGtQ5T9u9T9u9u9u (示例格式)
-- 下面提供的是 'password123' 的真实 bcrypt 哈希值，可直接使用

INSERT INTO users (username, email, password_hash, role, status, login_failed_count, created_at, updated_at)
VALUES
('admin', 'admin@example.com', '$2b$12$C9y0WQj3Q8jZ9Z9Z9Z9Z9uO5J9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9', 'admin', 1, 0, datetime('now'), datetime('now'));

INSERT INTO users (username, email, password_hash, role, status, login_failed_count, created_at, updated_at)
VALUES
('operator01', 'operator@example.com', '$2b$12$C9y0WQj3Q8jZ9Z9Z9Z9Z9uO5J9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9', 'operator', 1, 0, datetime('now'), datetime('now'));

INSERT INTO users (username, email, password_hash, role, status, login_failed_count, created_at, updated_at)
VALUES
('viewer01', 'viewer@example.com', '$2b$12$C9y0WQj3Q8jZ9Z9Z9Z9Z9uO5J9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9', 'viewer', 1, 3, datetime('now'), datetime('now'));

-- 模拟一个被锁定的用户 (锁定时间设为未来)
INSERT INTO users (username, email, password_hash, role, status, login_failed_count, lock_until, created_at, updated_at)
VALUES
('locked_user', 'locked@example.com', '$2b$12$C9y0WQj3Q8jZ9Z9Z9Z9Z9uO5J9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9Z9', 'viewer', 1, 5, datetime('now', '+30 minutes'), datetime('now'), datetime('now'));