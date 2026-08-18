# 特权模型 V2：部署与集成文档

> 文档日期：2026-08-18
> 对应代码：特权代理 V2、Agent 提权工具与无人值守授权闭环

---

## 目录

1. [本次更新了什么](#1-本次更新了什么)
2. [依赖了什么](#2-依赖了什么)
3. [部署步骤（从零开始）](#3-部署步骤从零开始)
4. [CLI 使用手册](#4-cli-使用手册)
5. [新 API 接口文档](#5-新-api-接口文档)
6. [与前端对接](#6-与前端对接)
7. [Agent MCP 工具](#7-agent-mcp-工具)
8. [常见问答](#8-常见问答)
9. [排障指南](#9-排障指南)

---

## 1. 本次更新了什么

### 新增文件

| 文件 | 说明 |
|------|------|
| `privileged_agent/crypto.py` | Ed25519 非对称密码学模块：密钥生成、签名、验签、hash 计算 |
| `conf/privileged_commands.yaml` | 命令注册表：定义特权代理允许执行的 15 个命令及其参数约束 |
| `privileged_agent/validator.py` | 注册表加载器 + 参数校验器（路径白名单、参数格式、SQL 前缀） |
| `gateway/service/elevation_service.py` | 特权码纯内存状态机：code 生成/审批/token 签发/Ed25519 签名/扣减 |
| `gateway/controller/AdminController.py` | Admin REST API：CLI 调用的 4 个审批端点 |
| `deploy/cli/nereus` | CLI 工具：`sudo nereus {init,approve,list-pending,revoke,history}` |
| `sql/elevation_codes.sql` | 审计日志表（可选持久化），`elevation_audit_log` + `elevation_execution_log` |
| `docs/privilege-model-v2-deploy.md` | 本文档 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `privileged_agent/models.py` | 新增 `PrivilegedV2Request` 模型、9 个 V2 安全错误码 |
| `privileged_agent/server.py` | 重写：V1/V2 双协议、SO_PEERCRED、Ed25519 验签、命令注册表、SAFE_ENV、nonce 去重 |
| `deploy/systemd/nereus-privileged-agent.service` | 加固：ProtectKernelTunables/PrivateTmp/NoNewPrivileges/RuntimeDirectory 等 |
| `deploy/systemd/nereus-privileged-agent-dev.service` | 同上（开发版） |
| `gateway/app.py` | 注册 `AdminController` 到 FastAPI 路由 |
| `requirements.txt` | 新增 `cryptography`、`pyyaml` 依赖 |

### 本轮已实现

| 功能 | 说明 |
|------|------|
| Agent MCP 工具 `submitElevation` / `runPrivileged` | 已注册到 MCP schema；执行链路在 Gateway 进程内完成 |
| AI 安全审计 | `audit_commands` / `audit_script_content` 提供结构化审计，CLI 审批前展示 |
| 工具授权请求 | 预授权未覆盖时生成 `authorization.requested`，CLI 批准后写回任务/巡检策略 |
| 提权通道约束 | 预设命令、单条简单命令、审计脚本三通道互斥，均受命令注册表、路径和 hash 约束 |

---

## 2. 依赖了什么

### Python 依赖

| 包 | 用途 | 安装方式 |
|----|------|---------|
| `cryptography` >= 49.0.0 | Ed25519 密钥生成、签名、验签 | `uv add cryptography` |
| `pyyaml` >= 6.0.3 | 解析命令注册表 YAML | `uv add pyyaml` |

已通过 `uv add` 安装并更新 `requirements.txt`，重新部署时执行：

```bash
uv sync
```

### 系统依赖

| 组件 | 用途 | 备注 |
|------|------|------|
| systemd >= 245 | 服务管理 + 安全加固（ProtectKernelTunables 等） | KylinOS V10 自带 |
| Unix Domain Socket | 特权代理通信 | Linux 内核通用，无需额外安装 |

---

## 3. 部署步骤（从零开始）

### 3.1 生成 Ed25519 密钥对

```bash
# 创建密钥目录
sudo mkdir -p /etc/nereus

# 生成密钥对
cd /path/to/NereusDoorLoongMagicPanel-backend
python -m privileged_agent.crypto generate \
  --priv /etc/nereus/ed25519_priv.pem \
  --pub /etc/nereus/ed25519_pub.pem

# 私钥仅 root 可读
sudo chmod 400 /etc/nereus/ed25519_priv.pem
sudo chmod 644 /etc/nereus/ed25519_pub.pem
```

**密钥安全说明：**
- **私钥** (`ed25519_priv.pem`)：后端（nobody）读取，用于签名请求。权限 400，仅 root 可读。
  - 泄露影响**有限**：攻击者需要同时绕过 SO_PEERCRED（UID 白名单）+ 命令注册表（命令白名单）
  - 建议定期轮换（见 8.8 节）
- **公钥** (`ed25519_pub.pem`)：特权代理（root）读取，用于验签。泄露**无害**——公钥只能验签不能签名。

### 3.2 生成 admin_token

**⚠️ 权限坑：后端进程必须能读取这个文件。**

后端进程（nobody/backend 用户）需要读取 admin_token 来验证 CLI 请求。
但文件默认 `400 root:root`（仅 root 可读）→ **后端读不了**。

修复方法：指定后端运行的用户和组，init 会自动 chown：

```bash
# 如果后端以 nobody 运行
sudo deploy/cli/nereus init --user nobody --group nogroup

# 如果后端以 backend 用户运行（推荐生产）
sudo deploy/cli/nereus init --user backend --group backend
```

> **为什么 root 仍能读？** Linux 内核中 root（UID=0）绕过所有文件权限检查，
> 所以 `sudo nereus approve` 永远可以读这个文件。
> 详见 [Linux Kernel File Permission Checks](https://www.kernel.org/doc/html/latest/admin-guide/security.rst)。

输出示例：
```
✅ admin_token 已生成: /etc/nereus/admin_token
   所有权: nobody:nogroup  (400)
   Token: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b
```

**自定义 token 路径（可选）：**
如果你想把 token 放在别处，在 `.env` 或 systemd 中设置：
```bash
# .env 文件
NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token

# 或 systemd unit 中
Environment=NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token
```

> **注意**：CLI 通过 `sudo` 运行，不读取项目的 `.env` 文件。自定义路径时 CLI 需：
> ```bash
> sudo NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token deploy/cli/nereus approve CODE
> ```

### 3.3 安装 CLI 到 PATH

```bash
sudo ln -sf /path/to/NereusDoorLoongMagicPanel-backend/deploy/cli/nereus /usr/local/bin/nereus
```

安装后直接使用：

```bash
sudo nereus init                    # 生成 admin_token
sudo nereus approve NGA7-K3X9       # 批准特权码
sudo nereus list-pending            # 查看待审批
```

### 3.4 部署特权代理 systemd 服务

**重要：** 提供的 `deploy/systemd/nereus-privileged-agent.service` **不能直接用**，需要根据你的实际部署路径修改：

```bash
# 复制到 systemd 目录
sudo cp deploy/systemd/nereus-privileged-agent.service /etc/systemd/system/

# 编辑，修改以下路径为你的实际路径
sudo vim /etc/systemd/system/nereus-privileged-agent.service
```

**必须修改的项：**
```ini
WorkingDirectory=/your/actual/path                    # 项目根目录
ExecStart=/your/actual/path/.venv/bin/python -m privileged_agent.server
ReadWritePaths=/run/ndlmpanel /your/data/paths        # 根据需要调整

# socket 组的 RunAs 用户
Environment=NDLM_PRIVILEGED_AGENT_SOCKET_GROUP=backend  # 改为实际组名

# 允许连接的 UID（多个用逗号分隔）
Environment=NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS=65534    # nobody 的 UID
```

**注意 `ReadWritePaths`**：因为设置了 `ProtectSystem=strict`，特权代理只能写 `ReadWritePaths` 中声明的目录。如果未来需要写新的路径（如新的部署目录），必须先加到这里，否则写操作会被 systemd 阻止。

**启动服务：**

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nereus-privileged-agent
sudo systemctl status nereus-privileged-agent
```

### 3.5 配置后端

后端（FastAPI）需要通过 systemd 或 shell 环境变量加载 admin_token 路径。

**方式 A：在 systemd unit 中（推荐）**

如果后端也有 systemd 服务，在 `[Service]` 段添加：

```ini
Environment=NDLM_ADMIN_TOKEN_PATH=/etc/nereus/admin_token
Environment=NDLM_ELEVATION_PRIVKEY=/etc/nereus/ed25519_priv.pem
```

**方式 B：在 .env 中（开发环境）**

在项目根目录 `.env` 文件添加：

```bash
NDLM_ADMIN_TOKEN_PATH=/etc/nereus/admin_token
NDLM_ELEVATION_PRIVKEY=/etc/nereus/ed25519_priv.pem
```

后端启动时通过 `os.getenv()` 读取。**注意**：当前 `main.py` 不自动加载 `.env`，如果你用开发模式需要先 `source`：

```bash
export $(grep -v '^#' .env | xargs)
uv run python main.py
```

### 3.6 重启后端

```bash
sudo systemctl restart nereus-backend   # 如果有 systemd 服务
# 或开发模式
pkill -f "uvicorn main" && uv run python main.py
```

### 3.7 验证部署

```bash
# 1. 特权代理在运行
sudo systemctl status nereus-privileged-agent

# 2. socket 存在且权限正确
ls -l /run/ndlmpanel/privileged-agent.sock   # 应显示 srw-rw----

# 3. CLI 可用
sudo nereus list-pending                     # 应显示 "没有待审批的特权码"

# 4. API 可用
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $(sudo cat /etc/nereus/admin_token)" \
  http://127.0.0.1:8000/admin/elevation/pending
# 应返回 200
```

### 3.8 配置项怎么获取？

部署时需要填几个环境变量，这里逐一说明怎么确定值。

#### `NDLM_PRIVILEGED_AGENT_SOCKET_GROUP`

Unix socket 文件的组所有权，**后端进程必须属于这个组**才能连接 socket。

```bash
# 1. 确定后端以什么用户运行
#    生产环境通常是 nobody 或 backend
ps aux | grep uvicorn | grep -v grep

# 2. 查这个用户的组
groups nobody
#   输出: nobody : nogroup          → SOCKET_GROUP=nogroup
# 或:
groups backend
#   输出: backend : backend          → SOCKET_GROUP=backend
```

**生产推荐**：创建一个 `backend` 系统用户：
```bash
sudo groupadd --system backend
sudo useradd --system --no-create-home --gid backend --shell /sbin/nologin backend
```

#### `NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS`

允许连接特权代理的 UID 列表（多个用逗号分隔）。

```bash
# 后端进程的 UID
id -u nobody          # 65534
# 或
id -u backend         # 1001 之类

# 多个 UID 可以共存
# NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS=65534,1000
# 表示 nobody + 开发用户 he 都可以连接
```

#### `ReadWritePaths`（systemd 参数）

在 `ProtectSystem=strict` 模式下，特权代理**只能写**这些路径。

判断标准：特权代理需要在哪些目录创建/修改文件。

| 目录 | 需要原因 | 必选？ |
|------|---------|--------|
| `/run/ndlmpanel` | 创建 socket 文件 | **必选** |
| `/opt/ndlmpanel` | 写入脚本/tmp 文件 | 如果使用脚本通道 |
| `/etc/nginx` | Nginx 配置写入 | 如果管理 Nginx |
| `/var/www` | 静态文件写入 | 如果管理 Web 站点 |
| `/etc/docker` | Docker daemon.json | 如果管理 Docker |
| `/etc/letsencrypt` | SSL 证书 | 如果管理证书 |
| `/etc/mysql` | MySQL 配置 | 如果管理 MySQL |

```ini
# 最小配置（只管理 Nginx）
ReadWritePaths=/run/ndlmpanel /etc/nginx /var/www

# 完整配置
ReadWritePaths=/run/ndlmpanel /opt/ndlmpanel /etc/nginx /var/www \
               /etc/docker /etc/letsencrypt /etc/mysql
```

**⚠️ 遗漏后果**：特权代理执行 `mkdir` 时会报 `Permission denied`，因为 systemd 封锁了写权限。

#### `NDLM_ADMIN_TOKEN_PATH`

admin_token 路径。默认 `/etc/nereus/admin_token` — 90% 场景不需要改。

如果希望自定义（例如多个后端共用同一个 token）：
```bash
# 在 systemd unit 中
Environment=NDLM_ADMIN_TOKEN_PATH=/data/shared/admin_token

# 或在 .env 中
NDLM_ADMIN_TOKEN_PATH=/data/shared/admin_token
```

#### 快速检查清单

```bash
echo "=========================================="
echo "1. 后端运行用户:"
ps aux | grep uvicorn | grep -v grep | awk '{print $1}'
echo ""
echo "2. 后端用户 UID:"
ps aux | grep uvicorn | grep -v grep | awk '{print $1}' | xargs id -u 2>/dev/null
echo ""
echo "3. 后端用户组:"
ps aux | grep uvicorn | grep -v grep | awk '{print $1}' | xargs groups 2>/dev/null
echo ""
echo "4. Socket 当前权限:"
ls -l /run/ndlmpanel/privileged-agent.sock 2>/dev/null || echo "(未启动)"
echo ""
echo "5. Token 文件权限:"
ls -l /etc/nereus/admin_token 2>/dev/null || echo "(未生成)"
echo ""
echo "6. 密钥文件权限:"
ls -l /etc/nereus/ed25519_*.pem 2>/dev/null || echo "(未生成)"
echo "=========================================="
```

---

## 4. CLI 使用手册

### 4.1 安装

```bash
# 方式一：符号链接到 PATH（推荐）
sudo ln -sf $(pwd)/deploy/cli/nereus /usr/local/bin/nereus

# 方式二：直接使用路径
sudo deploy/cli/nereus <command>
```

### 4.2 命令列表

| 命令 | 权限 | 说明 |
|------|------|------|
| `init` | root | 首次部署，生成 `/etc/nereus/admin_token` |
| `approve <CODE>` | root | 批准一个待审批的特权码 |
| `list-pending` | root | 列出所有待审批的特权码 |
| `revoke <TOKEN_ID>` | root | 吊销一个已签发的 token |
| `history` | root | 查看审批历史 |
| `help` | - | 显示帮助 |

### 4.3 init — 首次部署

```bash
sudo nereus init
```

输出示例：
```
✅ admin_token 已生成: /etc/nereus/admin_token
   请在后端配置中设置相同的 token
   Token: a1b2c3d4e5f6...
```

只需执行一次。之后 `approve`/`list-pending` 等命令会自动读取这个文件。

### 4.4 approve <CODE> — 审批特权码

```bash
sudo nereus approve NGA7-K3X9
```

交互界面：
```
============================================================
🔐  特权请求批准
============================================================
  Session:  sess_abc123
  原因:     修复 nginx 站点配置
  请求者:   AI Agent

  将批准以下操作:
    1. mkdir -p /var/www/newsite
    2. write_file /etc/nginx/sites-enabled/newsite

  有效期: 60 分钟  |  操作次数上限: 10 次

  批准以上操作? (y/N):
```

输入 `y` 批准，其他任何输入拒绝。

### 4.5 list-pending — 列出待审批

```bash
sudo nereus list-pending
```

输出示例：
```
📋  待审批特权码 (2 个)
------------------------------------------------------------
  Code:     NGA7-K3X9
  原因:     修复 nginx 站点配置
  操作:     mkdir, write_file
  过期:     2026-06-15T10:30:00

  Code:     B2X4-M7PQ
  原因:     重启 MySQL 服务
  操作:     systemctl
  过期:     2026-06-15T11:00:00
```

### 4.6 revoke <TOKEN_ID> — 吊销 token

```bash
sudo nereus revoke 550e8400-e29b-41d4-a716-446655440000
```

确认后立即失效，Agent 无法再用该 token 执行操作。

### 4.7 history — 查看历史

```bash
sudo nereus history
```

### 4.8 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NDLM_ADMIN_TOKEN_PATH` | `/etc/nereus/admin_token` | admin_token 文件路径 |
| `NDLM_ADMIN_URL` | `http://127.0.0.1:8000` | 后端 API 地址 |

CLI 通过 `sudo` 运行，不读取项目的 `.env` 文件。如需自定义：

```bash
sudo NDLM_ADMIN_URL=http://127.0.0.1:8080 nereus list-pending
```

---

## 5. 新 API 接口文档

### 5.1 鉴权方式

所有 admin API 使用 **Bearer Token** 鉴权：

```http
Authorization: Bearer <token>
```

Token 值存储在 `/etc/nereus/admin_token`（仅 root 可读），CLI 自动读取并发送。

**安全约束：**
- 仅接受来自 `127.0.0.1`、`::1`、`localhost` 的请求
- token 文件权限必须为 400（root:root）
- 后端和生产环境的 CLI 读取同一个文件

### 5.2 GET /admin/elevation/codes/{code}

查询一个特权码的详细信息。

**请求示例：**
```http
GET /admin/elevation/codes/NGA7-K3X9 HTTP/1.1
Authorization: Bearer <token>
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "code": "NGA7-K3X9",
    "session_id": "sess_abc123",
    "commands": [
      {"command": "mkdir", "args": ["-p", "/var/www/newsite"]},
      {"command": "write_file", "args": ["/etc/nginx/sites-enabled/newsite", "server { ... }"]}
    ],
    "reason": "修复 nginx 站点配置",
    "status": "pending",
    "ttl_seconds": 3600,
    "max_ops": 10,
    "ops_used": 0,
    "requested_at": "2026-06-15T10:00:00+00:00",
    "approved_by": null,
    "approved_at": null,
    "token_id": null,
    "expired": false,
    "exhausted": false
  }
}
```

**错误：** `{"success": false, "message": "特权码不存在"}`

### 5.3 GET /admin/elevation/pending

列出所有待审批的特权码。

**请求示例：**
```http
GET /admin/elevation/pending HTTP/1.1
Authorization: Bearer <token>
```

**成功响应：**
```json
{
  "success": true,
  "data": [
    {
      "code": "NGA7-K3X9",
      "session_id": "sess_abc123",
      "commands": [...],
      "reason": "修复 nginx 站点配置",
      "status": "pending",
      ...
    }
  ]
}
```

### 5.4 POST /admin/elevation/approve

批准一个 pending 的 code，签发 JIT token。

**请求：**
```json
{
  "code": "NGA7-K3X9",
  "approved_by": "admin"
}
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "status": "approved",
    "code": "NGA7-K3X9",
    "token_id": "550e8400-e29b-41d4-a716-446655440000",
    "max_ops": 10,
    "allowed_commands": [
      {"command": "mkdir", "args_hash": "55fe2ed8..."},
      {"command": "write_file", "args_hash": "87837d69..."}
    ]
  }
}
```

**错误：** `{"success": false, "message": "批准失败：code 不存在或状态不是 pending"}`

### 5.5 POST /admin/elevation/reject

拒绝一个 pending 的 code。

**请求：**
```json
{
  "code": "NGA7-K3X9",
  "reason": "操作风险过高，请在审批后联系管理员"
}
```

### 5.6 POST /admin/elevation/revoke

吊销一个已签发的 token（立即失效）。

**请求：**
```json
{
  "token_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5.7 GET /admin/elevation/history

查询审批历史。

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `limit` | int | 50 | 返回条数 |

---

## 6. 与前端对接

### 6.1 核心流程

```
┌───── Agent ──────────────────────────────────────────────┐
│  Agent 需要 root 权限                                     │
│  → 调用 submitElevation(commands, reason, session_id)     │
│  → 后端生成 code，返回 {"code": "NGA7-K3X9", ...}        │
│  → 前端显示审批引导界面                                    │
└──────────────────────────────────────────────────────────┘
         │ Agent 显示: "请在 SSH 中执行 sudo nereus approve NGA7-K3X9"
         ▼
┌───── 管理员 SSH ─────────────────────────────────────────┐
│  sudo nereus approve NGA7-K3X9                           │
│  → 查看操作列表 → y 确认                                  │
│  → 后端签发 token                                        │
│  → CLI 输出 "✅ 已批准"                                   │
└──────────────────────────────────────────────────────────┘
         │ Agent 轮询到 code 状态变成 approved
         ▼
┌───── Agent ──────────────────────────────────────────────┐
│  Agent 检测到已批准                                       │
│  → 调用 runPrivileged(token_id, command_index, args)     │
│  → 后端验证 token，Ed25519 签名 signed_request            │
│  → 特权代理验签 + 注册表验证 → 执行                       │
│  → 返回执行结果                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.2 前端需要实现的 3 个界面

**界面 A：审批引导弹窗**

当 Agent 调用 `submitElevation` 后，后端返回 code。前端应显示：

```
┌────────────────────────────────────────────┐
│ 🔐 需要特权批准                             │
│                                             │
│ 请在 SSH 中执行:                            │
│ $ sudo nereus approve NGA7-K3X9            │
│                                             │
│ 原因: 修复 nginx 站点配置                   │
│ 操作:                                       │
│   1. mkdir -p /var/www/newsite             │
│   2. write_file /etc/nginx/site.conf       │
│                                             │
│ 状态: ⏳ 等待审批...                         │
│ (自动刷新)                                  │
└────────────────────────────────────────────┘
```

**界面 B：审批成功通知**

```
┌────────────────────────────────────────────┐
│ ✅ 已批准 — Agent 正在执行                  │
│                                             │
│ Token: 550e8400-...                         │
│ 剩余操作次数: 10                            │
└────────────────────────────────────────────┘
```

**界面 C：审批拒绝/过期通知**

```
┌────────────────────────────────────────────┐
│ ❌ 审批已拒绝                               │
│                                             │
│ 原因: 操作风险过高                          │
└────────────────────────────────────────────┘
```

### 6.3 事件与前端展示

交互会话通过 WebSocket 接收 `elevation.resolved` 事件；无人值守任务遇到预授权未覆盖的工具时，会在事件流中记录 `authorization.requested`，同时把审批提示写入会话消息和巡检报告。

```json
{
  "type": "authorization.requested",
  "data": {
    "approval_code": "NGA7-K3X9",
    "tool": "runShellCommand",
    "args": {},
    "ai_reason": "检查服务状态",
    "reason": "高危工具需要管理员确认",
    "policy_reason": "命令未命中 allowedCommands 白名单"
  }
}
```

前端建议将审批码渲染为复制卡片，并提供“查看执行会话”入口；管理员在服务器侧执行 `sudo nereus approve CODE` 后，前端等待 `elevation.resolved` 或下一次任务运行结果即可。

### 6.4 Agent 工具的实际执行位置

Agent 工具不通过额外的 `/api/v1/elevation/*` HTTP 接口调用，而是在 AgentCore / Gateway 进程内完成状态交接：

| 工具 | 执行位置 | 说明 |
|------|------|------|
| `submitElevation` | MCP schema + Gateway 结果同步 | 生成审批码并进入 ElevationService |
| `runPrivileged` | `AgentCore._executeTool` | 使用已批准 token 创建签名请求，经 Unix socket 交给特权代理 |

---

## 7. Agent MCP 工具

这是 Agent 层（LLM）调用的 MCP 工具，当前已注册并接入提权执行链路。无人值守任务会剔除需要在线交互的提权工具；只有管理员在线批准后，交互会话才可以继续执行。

### 7.1 submitElevation 工具

```python
# 应放在 agent/agent_mcp/tools/ops/elevation.py

@mcp.tool()
async def submitElevation(
    ctx: Context,
    session_id: str,
    commands: list[dict],  # [{"command": "mkdir", "args": ["-p", "/var/www/test"]}, ...]
    reason: str,
) -> str:
    """提交特权操作申请，返回一个审批 code。

    Agent 调用此工具时，后端生成一个 8 位 code（如 NGA7-K3X9）。
    管理员需通过 SSH 执行 `sudo nereus approve <CODE>` 批准。
    批准后 Agent 可以调用 runPrivileged 执行操作。
    """
    # 返回待审批 code；批准后由 Agent 调用 runPrivileged
```

### 7.2 runPrivileged 工具

```python
@mcp.tool()
async def runPrivileged(
    ctx: Context,
    token_id: str,
    command_index: int,
    args: list[str],
) -> dict:
    """用已批准的 token 执行一个特权操作。

    Args:
        token_id: approve 后返回的 token_id
        command_index: 申请时第几个命令（从 0 开始）
        args: 实际参数（必须与申请时完全一致，否则 args_hash 不匹配）

    Returns:
        命令执行结果（stdout/stderr/returnCode）
    """
    return result
```

### 7.3 实现要点

- `submitElevation` → 通过 Agent 事件流展示 code → 用户执行 `sudo nereus approve` → 后端签发 token
- `runPrivileged` → `ElevationService.create_signed_request()` → `PrivilegedAgentClient` → Unix socket 特权代理 → 返回结果
- 高危请求同时进入 `ToolAuthorizationService`；定时任务/巡检批准后把工具、命令和路径授权合并回来源策略。

---

## 8. 常见问答

### Q1: 密钥文件绝对安全吗？

没有"绝对"安全，但设计上泄露的影响被多层防御限制：

```
私钥泄露 → 攻击者能签名请求 → 但还有两层拦截:
  ① SO_PEERCRED: 连接方 UID 必须在白名单内
  ② 命令注册表: 不在表中的命令特权代理直接拒绝

公钥泄露 → 无害（只能验签不能签名）
```

**真正的风险点**：后端进程被攻破 → 内存中的私钥被 dump。
**缓解**：私钥文件 chmod 400 + 后端以 nobody 运行 + 定期轮换密钥。

**⚠️ 权限坑：后端读不了密钥文件**

文件在 `/etc/nereus/` 下，默认 `400 root:root`。
但后端进程以 `nobody`（或 `backend`）运行，不是 root → **读不了**。

修复：
```bash
# 让后端进程所在的组可以读
sudo chgrp nogroup /etc/nereus/ed25519_priv.pem /etc/nereus/admin_token
sudo chmod 440 /etc/nereus/ed25519_priv.pem /etc/nereus/admin_token

# 或用 init 的 --user 参数自动设置
sudo nereus init --user nobody --group nogroup
```

### Q2: sudo deploy/cli/nereus init 之后怎么用？

`init` 只需执行**一次**，之后正常使用：

```bash
# 安装到 PATH（推荐）
sudo ln -sf $(pwd)/deploy/cli/nereus /usr/local/bin/nereus

# 然后直接用
sudo nereus list-pending       # 查看待审批
sudo nereus approve NGA7-K3X9  # 批准
sudo nereus history             # 查看历史
```

也可以不安装，直接用路径：
```bash
sudo deploy/cli/nereus list-pending
```

### Q3: 你给的 nereus-privileged-agent.service 直接用？

**不可以直接用**。需要根据你的实际部署路径修改 3 项：

```ini
WorkingDirectory=/your/actual/path
ExecStart=/your/actual/path/.venv/bin/python -m privileged_agent.server
Environment=NDLM_PRIVILEGED_AGENT_SOCKET_GROUP=your_group_name
```

另外，`ReadWritePaths` 中需要加上你的部署目录：
```ini
ReadWritePaths=/run/ndlmpanel /your/actual/deploy/path /opt/ndlmpanel ...
```

### Q4: init 之后 admin token 就不用管了？

**对，但有前提：后端进程必须能读取 token 文件。**

`sudo nereus init --user nobody --group nogroup` 做了三件事：
1. 生成随机 token → 写入 `/etc/nereus/admin_token`
2. chown 给 `nobody:nogroup`，权限 `400`（仅 owner=nobody 可读）
3. 打印 token 值

后端 `AdminController` 启动时自动读取。CLI（root）启动时也读取同一个文件
（Linux root 绕过权限检查）。**只要文件存在且权限正确，一切自动生效。**

**如果 init 时没传 `--user/--group`**，文件是 `400 root:root`，后端读不了。
手动修复：
```bash
sudo chown nobody:nogroup /etc/nereus/admin_token
```

### Q5: 能不能用 .env 配置 token 路径？

可以。后端和 CLI 都支持 `NDLM_ADMIN_TOKEN_PATH` 环境变量：

```bash
# .env 文件
NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token
NDLM_ELEVATION_PRIVKEY=/etc/nereus/ed25519_priv.pem

# 或 systemd unit
Environment=NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token
```

**注意**：CLI 通过 sudo 运行，不读取项目的 `.env` 文件。如果自定义了路径，需要在 sudo 时传环境变量：

```bash
sudo NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token nereus approve CODE
```

### Q6: 所有的 MCP 和 API 写了吗？注册了吗？

**API（后端部分）已写完并注册：**
- `AdminController` → 已注册到 `gateway/app.py` 的 FastAPI 路由
- 4 个 admin API 端点全部可用

**MCP 工具（Agent 层）已实现：**
- `submitElevation` 和 `runPrivileged` 已注册到工具 schema
- `AgentCore` 在 Gateway 进程内处理 `runPrivileged`，确保 token 状态与管理员审批使用同一进程
- 工具授权请求支持 `authorization.requested` 事件、CLI 审批和跨运行策略写回

### Q7: admin token 也会过期吗？

不会过期。与 JIT token（几分钟到几小时过期）不同，admin_token 是**静态凭证**，跟 SSH 密钥类似。```bash
# 手动轮换
sudo nereus init          # 重新生成
sudo systemctl restart nereus-backend  # 后端重新加载
```

### Q8: 如何轮换 Ed25519 密钥？

```bash
# 1. 生成新密钥
python -m privileged_agent.crypto generate \
  --priv /etc/nereus/ed25519_priv_new.pem \
  --pub /etc/nereus/ed25519_pub_new.pem

# 2. 替换公钥（特权代理热加载 — 重启即可）
sudo cp /etc/nereus/ed25519_pub_new.pem /etc/nereus/ed25519_pub.pem
sudo systemctl restart nereus-privileged-agent

# 3. 替换私钥（后端）
sudo cp /etc/nereus/ed25519_priv_new.pem /etc/nereus/ed25519_priv.pem
sudo chmod 400 /etc/nereus/ed25519_priv.pem
sudo systemctl restart nereus-backend

# 4. 清理旧密钥
sudo rm /etc/nereus/ed25519_priv_new.pem /etc/nereus/ed25519_pub_new.pem
```

---

## 9. 排障指南

### 9.1 特权代理未启动

```bash
sudo systemctl status nereus-privileged-agent
sudo journalctl -u nereus-privileged-agent -n 50 --no-pager
```

常见原因：
- `.venv/bin/python` 路径不对 → 检查 `ExecStart`
- `WorkingDirectory` 路径不对 → 检查目录是否存在
- 端口冲突 → 检查 `/run/ndlmpanel/privileged-agent.sock` 是否被占用

### 9.2 后端连不上特权代理

错误：`特权代理未启动` 或 `无权访问特权代理`

```bash
# 检查 socket 文件
ls -l /run/ndlmpanel/privileged-agent.sock
# 应显示 srw-rw----  root:backend

# 检查后端进程的 UID
id $(ps -o user= -p $(pgrep -f "uvicorn main"))
# 确保 UID 在 ALLOWED_UIDS 中
# 确保用户属于 socket 的组
```

### 9.3 CLI 报 "admin_token 不可用"

```bash
# 检查 token 文件
ls -l /etc/nereus/admin_token
sudo cat /etc/nereus/admin_token

# 如果不存在
sudo nereus init

# 如果路径自定义了
echo $NDLM_ADMIN_TOKEN_PATH
```

### 9.4 CLI 报 "无法连接后端"

```bash
# 检查后端是否在运行
curl -s http://127.0.0.1:8000/docs | head -5

# 检查端口
sudo ss -tlnp | grep 8000

# 如果后端端口不是 8000
sudo NDLM_ADMIN_URL=http://127.0.0.1:8080 nereus list-pending
```

### 9.5 签名验证失败

特权代理日志中看到 `SIGNATURE_INVALID`：

```bash
sudo journalctl -u nereus-privileged-agent --no-pager | grep SIGNATURE
```

原因排查：
1. **密钥不匹配**：后端用的私钥和特权代理用的公钥不是一对
   ```bash
   # 检查两个文件的修改时间
   ls -l /etc/nereus/ed25519_*.pem
   ```
2. **时间偏差**：服务器时间不正确（偏差超过 30 秒）
   ```bash
   date
   ```
3. **公钥未配置**：特权代理日志中会显示 `pubkey=none (dev mode)`

### 9.6 命令被注册表拒绝

特权代理日志中看到 `COMMAND_NOT_REGISTERED` 或 `ARGS_INVALID`：

```bash
sudo journalctl -u nereus-privileged-agent --no-pager | grep -E "not_registered|args_invalid"
```

原因：
- 命令不在 `conf/privileged_commands.yaml` 中
- 参数路径不在白名单内
- SQL 前缀不匹配
- 服务名不匹配

修改 `conf/privileged_commands.yaml` 后**不需要重启特权代理**——但是当前实现启动时加载一次，所以需要重启：
```bash
sudo systemctl restart nereus-privileged-agent
```

---

## 附录：文件路径速查

| 用途 | 路径 | 默认值 |
|------|------|--------|
| Ed25519 私钥 | `NDLM_ELEVATION_PRIVKEY` | `/etc/nereus/ed25519_priv.pem` |
| Ed25519 公钥 | `NDLM_PRIVILEGED_AGENT_PUBKEY` | `/etc/nereus/ed25519_pub.pem` |
| admin_token | `NDLM_ADMIN_TOKEN_PATH` | `/etc/nereus/admin_token` |
| 特权代理 socket | `NDLM_PRIVILEGED_AGENT_SOCKET` | `/run/ndlmpanel/privileged-agent.sock` |
| 命令注册表 | 硬编码 | `conf/privileged_commands.yaml` |
