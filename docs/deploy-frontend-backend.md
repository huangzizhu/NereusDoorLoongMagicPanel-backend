# 前端与后端部署文档

本文档描述 Nereus 运维平台的前端与后端部署方式。前端使用已经编译好的 `dist` 静态文件，通过 Nginx 发布；后端使用 Python 运行 FastAPI 应用，生产环境建议以 systemd 服务托管。

文档分为两条后端安装路径：

- **LoongArch 架构 + 麒麟高级服务器版 V11**：使用系统 Python / 自编译 Python + `pip` 安装依赖，提前安装 Rust 与 C/C++ 编译环境，以便编译 `cryptography`、`pydantic-core`、`greenlet` 等扩展。
- **普通 x86 Linux，以 Ubuntu 为例**：使用 `uv` 创建 Python 3.13 环境并安装依赖。

## 1. 目录规划

推荐生产路径：

| 项 | 路径 |
|---|---|
| 后端代码 | `/opt/nereus/backend` |
| 后端虚拟环境 | `/opt/nereus/backend/.venv` |
| 前端 dist | `/opt/nereus/frontend/dist` |
| Nginx 站点配置 | `/etc/nginx/conf.d/nereus-panel.conf` |
| systemd 后端服务 | `/etc/systemd/system/nereus-backend.service` |
| 关键凭据 | `/etc/nereus` |
| 运行 socket | `/run/ndlmpanel` |

建议使用专用后端用户。`backend` 需要自己的 home 目录，否则 `pip`、`cargo`、`.cache`、`.local` 和 `sudo -u backend -H` 都可能报错：

```bash
sudo groupadd --system backend || true
sudo useradd \
  --system \
  --home-dir /var/lib/nereus/backend-home \
  --create-home \
  --gid backend \
  --shell /usr/sbin/nologin \
  backend 2>/dev/null || true
```

创建目录：

```bash
sudo install -d -o backend -g backend -m 0750 /var/lib/nereus/backend-home
sudo install -d -o backend -g backend -m 0750 /opt/nereus/backend
sudo install -d -o root -g root -m 0755 /opt/nereus/frontend
sudo install -d -o root -g root -m 0755 /opt/nereus/frontend/dist
sudo install -d -o root -g root -m 0750 /etc/nereus
sudo install -d -o root -g root -m 0750 /run/ndlmpanel
sudo install -d -o backend -g backend -m 0750 /var/log/nereus
sudo install -d -o root -g root -m 0755 /etc/nginx /var/www /etc/docker /etc/letsencrypt /etc/mysql
```

## 2. 发布项目文件

### 2.1 后端代码

将后端代码发布到 `/opt/nereus/backend`。示例：

```bash
sudo rsync -a --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  --exclude 'runtime' \
  ./ /opt/nereus/backend/

sudo chown -R backend:backend /opt/nereus/backend
```

不要把本地虚拟环境、第三方依赖缓存、`node_modules`、`site-packages` 等目录打包进安装包。依赖应在目标机器上通过 `pip` 或 `uv` 安装。

如果你拿到的是后端代码压缩包，先在临时目录解压，再同步到 `/opt/nereus/backend`：

```bash
mkdir -p /tmp/nereus-backend
unzip backend.zip -d /tmp/nereus-backend
sudo rsync -a --delete /tmp/nereus-backend/ /opt/nereus/backend/
sudo chown -R backend:backend /opt/nereus/backend
sudo chmod 0750 /opt/nereus/backend
```

### 2.2 前端 dist

本文假设前端已经在构建机编译完成，产物目录为 `dist/`。将其发布到服务器：

```bash
sudo rsync -a --delete ./dist/ /opt/nereus/frontend/dist/
sudo chown -R root:root /opt/nereus/frontend/dist
sudo find /opt/nereus/frontend/dist -type d -exec chmod 0755 {} \;
sudo find /opt/nereus/frontend/dist -type f -exec chmod 0644 {} \;
```

## 3. 配置文件与环境变量

生产环境必须由部署人员按现场环境编辑配置文件。不要把真实 API Key、Token、私钥或 `.env` 文件提交到代码仓库。

### 3.1 后端环境变量文件

推荐使用 `/etc/nereus/backend.env` 管理后端运行参数。该文件由 systemd 读取后注入进程环境，文件本身可保持 root-only。

```bash
sudo tee /etc/nereus/backend.env >/dev/null <<'EOF'
# ── LLM 配置 ──
# 可选 provider: deepseek / qwen / openai_compat / mock
NDLM_LLM_PROVIDER=deepseek
NDLM_LLM_ENDPOINT=https://api.deepseek.com/anthropic
NDLM_LLM_MODEL=deepseek-v4-pro
NDLM_LLM_API_KEY=请替换为真实大模型APIKey
NDLM_LLM_MAX_TOKENS=65536
NDLM_LLM_CONTEXT_WINDOW=1048576
NDLM_LLM_TEMPERATURE=0.1
NDLM_LLM_RETRY_COUNT=3
NDLM_LLM_RETRY_DELAY=2

# ── Web 搜索工具配置，可不用时留空或删除 ──
TAVILY_API_KEY=请替换为真实TavilyKey

# ── Agent 运行配置 ──
NDLM_SAFETY_POLICY=default
NDLM_EXECUTION_USER=backend
# trace 审计已合并到主库 agent_trace_logs 表，无需 NDLM_TRACE_DB_PATH
NDLM_TOOL_TIMEOUT_SECONDS=60
NDLM_MAX_TOOL_ROUNDS=0
NDLM_MAX_TOOL_CALLS_PER_ROUND=0

# ── 终端配置 ──
NDLM_TERMINAL_NORMAL_CONTAINER=app-container
NDLM_TERMINAL_NORMAL_LINUX_USER=appuser
NDLM_TERMINAL_NORMAL_SHELL=bash
NDLM_TERMINAL_IDLE_TIMEOUT_SECONDS=1800
NDLM_TERMINAL_ADMIN_MAX_FAILED_ATTEMPTS=5

# ── SQL 日志，生产默认关闭 ──
NDLM_SQLALCHEMY_ECHO=false
EOF

sudo chown root:root /etc/nereus/backend.env
sudo chmod 0600 /etc/nereus/backend.env
```

部署人员必须重点修改：

| 变量 | 必填 | 说明 |
|---|---|---|
| `NDLM_LLM_PROVIDER` | 是 | 模型供应商类型，常用 `deepseek`、`qwen`、`openai_compat` |
| `NDLM_LLM_ENDPOINT` | 是 | 大模型 API endpoint |
| `NDLM_LLM_MODEL` | 是 | 模型名称 |
| `NDLM_LLM_API_KEY` | 是 | 大模型 API Key，生产环境必须替换 |
| `TAVILY_API_KEY` | 否 | Web 搜索工具 Key，不使用 Web 搜索可不配置 |
| `NDLM_SAFETY_POLICY` | 是 | 安全策略名称，默认 `default` |
| `NDLM_TERMINAL_NORMAL_CONTAINER` | 按需 | 普通 Web Terminal 绑定的业务容器名 |

如果没有配置 `NDLM_LLM_API_KEY`，Agent 会回退到 MockProvider，只适合离线联调，不适合正式演示。

### 3.2 JWT 密钥配置

当前代码中的 JWT `SECRET_KEY` 位于：

```text
utils/JWTTokenTool.py
```

上线前必须将默认值：

```python
SECRET_KEY = "test_secret_key_change_to_real_key"
```

替换为生产随机密钥。生成示例：

```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

修改后应重新发布后端代码并重启服务。后续建议将该值改造为环境变量读取，避免密钥进入源代码。

### 3.3 前端运行配置

本文假设前端 dist 已经编译完成。部署前需要确认前端请求后端的 API Base URL。

推荐前端统一使用：

```text
/api
```

对应 Nginx 配置会将：

```text
/api/agent/ws -> http://127.0.0.1:8000/agent/ws
/api/file/list -> http://127.0.0.1:8000/file/list
```

如果前端 dist 中存在运行时配置文件，例如 `config.js`、`env.js` 或类似文件，需要部署人员按实际文件名修改 API Base：

```bash
sudo grep -R "API\\|BASE\\|VITE\\|BACKEND" -n /opt/nereus/frontend/dist | head -50
```

若前端 API 地址在构建阶段已固化，则必须在前端构建时设置为 `/api` 后再生成 dist。

如果你拿到的是 `dist.zip`，先解压再发布：

```bash
mkdir -p /tmp/nereus-dist
unzip dist.zip -d /tmp/nereus-dist
sudo rsync -a --delete /tmp/nereus-dist/dist/ /opt/nereus/frontend/dist/
sudo chown -R root:root /opt/nereus/frontend/dist
sudo find /opt/nereus/frontend/dist -type d -exec chmod 0755 {} \;
sudo find /opt/nereus/frontend/dist -type f -exec chmod 0644 {} \;
```

## 4. 后端部署：LoongArch + 麒麟高级服务器版 V11

LoongArch 环境上，Python 包可能缺少预编译 wheel，因此需要准备完整编译工具链。以下命令以 `dnf` 为例；如果系统使用 `yum`，将 `dnf` 替换为 `yum`。

### 4.1 安装系统编译依赖

```bash
sudo dnf makecache || sudo yum makecache

sudo dnf install -y \
  gcc gcc-c++ make cmake pkgconfig \
  openssl-devel libffi-devel zlib-devel bzip2-devel xz-devel \
  sqlite-devel readline-devel ncurses-devel gdbm-devel uuid-devel \
  rust cargo \
  nginx \
  tar gzip curl wget rsync git \
  firewalld policycoreutils-python-utils || \
sudo yum install -y \
  gcc gcc-c++ make cmake pkgconfig \
  openssl-devel libffi-devel zlib-devel bzip2-devel xz-devel \
  sqlite-devel readline-devel ncurses-devel gdbm-devel uuid-devel \
  rust cargo \
  nginx \
  tar gzip curl wget rsync git \
  firewalld policycoreutils-python-utils
```

确认 Rust 与编译器：

```bash
gcc --version
rustc --version
cargo --version
```

如果系统源中的 Rust 版本过旧，可使用 rustup 安装新版本：

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustc --version
```

### 4.2 准备 Python 3.13

项目要求 Python `>=3.13`。如果系统已有 Python 3.13，可直接使用：

```bash
python3.13 --version
```

如果没有，建议编译安装 CPython。以下以 `3.13.9` 为例：

```bash
cd /usr/local/src
sudo curl -LO https://www.python.org/ftp/python/3.13.9/Python-3.13.9.tgz
sudo tar xf Python-3.13.9.tgz
cd Python-3.13.9

sudo ./configure \
  --prefix=/opt/python/3.13.9 \
  --enable-optimizations \
  --with-ensurepip=install

sudo make -j"$(nproc)"
sudo make altinstall

/opt/python/3.13.9/bin/python3.13 --version
```

### 4.3 创建虚拟环境并安装依赖

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
/opt/python/3.13.9/bin/python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
'
```

如果 LoongArch 上部分包没有 wheel，`pip` 会自动进入源码编译。若遇到 Rust 相关错误，确认 `rustc` 和 `cargo` 在 PATH 中：

```bash
sudo -u backend -H bash -lc '
export PATH="$HOME/.cargo/bin:$PATH"
cd /opt/nereus/backend
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
'
```

如果 `backend` 用户没有可用 home 目录，先修正 home 再执行上面的命令。推荐的 home 是 `/var/lib/nereus/backend-home`。

如需强制源码构建，可在排障时使用：

```bash
sudo -u backend -H bash -lc '
export PATH="$HOME/.cargo/bin:$PATH"
cd /opt/nereus/backend
.venv/bin/python -m pip install --no-cache-dir --no-binary :all: -r requirements.txt
'
```

该方式会明显增加安装时间，只建议在 wheel 不兼容时使用。

### 4.4 验证后端依赖

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
.venv/bin/python -c "import fastapi, uvicorn, cryptography, pydantic; print(\"backend deps ok\")"
PYTHONPATH=/opt/nereus/backend .venv/bin/python -c "from gateway.app import Application; print(\"app import ok\")"
'
```

## 5. 后端部署：x86 Linux / Ubuntu + uv

以下以 Ubuntu 为例。

### 5.1 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y \
  curl ca-certificates build-essential pkg-config \
  libssl-dev libffi-dev zlib1g-dev libbz2-dev liblzma-dev \
  libsqlite3-dev libreadline-dev \
  nginx rsync git
```

### 5.2 安装 uv

推荐给 `backend` 用户安装 uv：

```bash
sudo -u backend -H bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh'
```

确认：

```bash
sudo -u backend -H bash -lc 'export PATH="$HOME/.local/bin:$PATH"; uv --version'
```

### 5.3 创建虚拟环境并安装依赖

```bash
sudo -u backend -H bash -lc '
export PATH="$HOME/.local/bin:$PATH"
cd /opt/nereus/backend
uv python install 3.13.9
uv venv --python 3.13.9
uv sync --frozen
'
```

如果 `uv.lock` 与当前平台不兼容，可使用：

```bash
sudo -u backend -H bash -lc '
export PATH="$HOME/.local/bin:$PATH"
cd /opt/nereus/backend
uv sync
'
```

### 5.4 验证后端依赖

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
PYTHONPATH=/opt/nereus/backend .venv/bin/python -c "from gateway.app import Application; print(\"app import ok\")"
'
```

## 6. 后端 systemd 服务

本文推荐后端服务名固定为：

```text
nereus-backend.service
```

该名称会影响 systemd 凭据目录：

```text
/run/credentials/nereus-backend.service/
```

### 6.1 前置要求

在创建后端服务前，请先完成特权代理与 CLI 文档中的密钥和 token 准备，确保以下文件存在：

```bash
sudo ls -l /etc/nereus/admin_token
sudo ls -l /etc/nereus/ed25519_priv.pem
sudo ls -l /etc/nereus/backend_rpc_ed25519_priv.pem
sudo ls -l /etc/nereus/backend_rpc_ed25519_pub.pem
```

这些源文件应保持 `root:root` 与 `0400` 或 `0444` 权限。后端通过 `LoadCredential` 读取 systemd 注入副本。

### 6.2 创建 systemd unit

获取后端 UID：

```bash
BACKEND_UID="$(id -u backend)"
echo "$BACKEND_UID"
```

创建服务文件：

```bash
sudo tee /etc/systemd/system/nereus-backend.service >/dev/null <<EOF
[Unit]
Description=Nereus Door Loong Magic Panel Backend
After=network.target nereus-privileged-agent.service
Requires=nereus-privileged-agent.service

[Service]
Type=simple
User=backend
Group=backend
WorkingDirectory=/opt/nereus/backend

Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/etc/nereus/backend.env
Environment=NDLM_PRIVILEGED_AGENT_SOCKET=/run/ndlmpanel/privileged-agent.sock
Environment=NDLM_PRIVILEGED_AGENT_TIMEOUT_SECONDS=5
Environment=NDLM_ADMIN_TOKEN_PATH=/run/credentials/nereus-backend.service/admin_token
Environment=NDLM_ELEVATION_PRIVKEY=/run/credentials/nereus-backend.service/ed25519_priv.pem
Environment=NDLM_BACKEND_RPC_PRIVKEY=/run/credentials/nereus-backend.service/backend_rpc_ed25519_priv.pem
Environment=NDLM_BACKEND_RPC_PUBKEY=/run/credentials/nereus-backend.service/backend_rpc_ed25519_pub.pem
Environment=NDLM_BACKEND_RPC_SOCKET=/run/ndlmpanel/backend-rpc.sock
Environment=NDLM_BACKEND_RPC_SOCKET_GROUP=backend
Environment=NDLM_BACKEND_RPC_SOCKET_MODE=660
Environment=NDLM_BACKEND_RPC_ALLOWED_UIDS=${BACKEND_UID}
Environment=NDLM_BACKEND_RPC_NONCE_TTL=300
Environment=NDLM_BACKEND_RPC_TIMESTAMP_TOLERANCE=30

LoadCredential=admin_token:/etc/nereus/admin_token
LoadCredential=ed25519_priv.pem:/etc/nereus/ed25519_priv.pem
LoadCredential=backend_rpc_ed25519_priv.pem:/etc/nereus/backend_rpc_ed25519_priv.pem
LoadCredential=backend_rpc_ed25519_pub.pem:/etc/nereus/backend_rpc_ed25519_pub.pem

ExecStart=/opt/nereus/backend/.venv/bin/python -m uvicorn main:fastApiInstance --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=3

NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ReadWritePaths=/opt/nereus/backend /run/ndlmpanel /var/log/nereus

[Install]
WantedBy=multi-user.target
EOF
```

如果系统 systemd 不支持 `LoadCredential`，不要直接把 root-only 文件改成全局可读。可作为降级方案将凭据 owner 改为 `backend:backend` 且权限保持 `0400`，但这不再是严格 root-only：

```bash
sudo chown backend:backend /etc/nereus/admin_token /etc/nereus/ed25519_priv.pem
sudo chmod 0400 /etc/nereus/admin_token /etc/nereus/ed25519_priv.pem
```

生产环境优先使用 `LoadCredential`。

### 6.3 启动后端

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nereus-backend
sudo systemctl status nereus-backend --no-pager
```

查看日志：

```bash
sudo journalctl -u nereus-backend -f
```

验证后端本机端口：

```bash
ss -lntp | grep 8000
timeout 3 curl -N http://127.0.0.1:8000/system/health || true
```

## 7. Nginx 部署前端 dist

### 7.1 安装 Nginx

Ubuntu：

```bash
sudo apt-get install -y nginx
```

Kylin：

```bash
sudo dnf install -y nginx || sudo yum install -y nginx
```

### 7.2 配置 WebSocket Upgrade

在 `/etc/nginx/conf.d/nereus-map.conf` 写入：

```bash
sudo tee /etc/nginx/conf.d/nereus-map.conf >/dev/null <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
EOF
```

### 7.3 配置站点

本文默认前端 API 前缀为 `/api/`，Nginx 会将 `/api/agent/ws` 代理到后端 `/agent/ws`，即自动去掉 `/api` 前缀。

```bash
sudo tee /etc/nginx/conf.d/nereus-panel.conf >/dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    root /opt/nereus/frontend/dist;
    index index.html;

    client_max_body_size 3g;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_connect_timeout 30s;
        proxy_buffering off;
    }
}
EOF
```

如果前端不是以 `/api/` 作为后端前缀，而是直接请求 `/agent/ws`、`/file/list` 等后端路径，可以将代理规则改为显式路径代理，或调整前端 API Base URL。推荐统一使用 `/api/`，避免与前端路由冲突。

### 7.4 检查并启动 Nginx

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

访问：

```bash
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/api/agent/sessions
```

第二个请求如果未登录，可能返回认证错误，这是正常的；关键是请求应到达后端而不是 404 静态文件。

## 8. 前后端联调检查

### 8.1 服务状态

```bash
sudo systemctl status nereus-privileged-agent --no-pager
sudo systemctl status nereus-backend --no-pager
sudo systemctl status nginx --no-pager
```

### 8.2 端口与 socket

```bash
ss -lntp | grep ':80'
ss -lntp | grep ':8000'
ls -l /run/ndlmpanel/privileged-agent.sock
ls -l /run/ndlmpanel/backend-rpc.sock 2>/dev/null || true
```

### 8.3 后端 API

```bash
timeout 3 curl -N http://127.0.0.1:8000/system/health || true
timeout 3 curl -N http://127.0.0.1/api/system/health || true
```

### 8.4 CLI 审批链路

```bash
sudo nereus list-pending
```

如无法连接，确认：

```bash
sudo systemctl status nereus-backend --no-pager
sudo journalctl -u nereus-backend -n 100 --no-pager
sudo cat /etc/nereus/admin_token >/dev/null && echo "admin_token readable by root"
```

## 9. 升级发布流程

### 9.1 后端升级

```bash
sudo systemctl stop nereus-backend

sudo rsync -a --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  --exclude 'runtime' \
  ./ /opt/nereus/backend/

sudo chown -R backend:backend /opt/nereus/backend
```

LoongArch / Kylin：

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
'
```

x86 / Ubuntu：

```bash
sudo -u backend -H bash -lc '
export PATH="$HOME/.local/bin:$PATH"
cd /opt/nereus/backend
uv sync --frozen || uv sync
'
```

重启：

```bash
sudo systemctl start nereus-backend
sudo systemctl status nereus-backend --no-pager
```

### 9.2 前端升级

```bash
sudo rsync -a --delete ./dist/ /opt/nereus/frontend/dist/
sudo chown -R root:root /opt/nereus/frontend/dist
sudo find /opt/nereus/frontend/dist -type d -exec chmod 0755 {} \;
sudo find /opt/nereus/frontend/dist -type f -exec chmod 0644 {} \;
sudo nginx -t
sudo systemctl reload nginx
```

## 10. 排障指南

### 10.1 后端无法启动

```bash
sudo journalctl -u nereus-backend -n 200 --no-pager
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
PYTHONPATH=/opt/nereus/backend .venv/bin/python -c "from gateway.app import Application; print(\"ok\")"
'
```

常见原因：

- Python 版本低于 3.13。
- LoongArch 上缺少 Rust 或 C 编译依赖。
- systemd `LoadCredential` 路径错误。
- `/opt/nereus/backend` 不可写，导致 SQLite `panel.db` 无法创建。

### 10.2 前端白屏

检查 dist：

```bash
ls -la /opt/nereus/frontend/dist
sudo nginx -t
sudo tail -n 100 /var/log/nginx/error.log
```

确认 `index.html` 存在，且 Nginx `root` 指向 `/opt/nereus/frontend/dist`。

### 10.3 WebSocket 连接失败

检查 Nginx 是否配置 Upgrade：

```bash
grep -R "proxy_set_header Upgrade" /etc/nginx/conf.d /etc/nginx/sites-enabled 2>/dev/null
```

检查后端 WebSocket 路由是否可达：

```bash
sudo journalctl -u nereus-backend -f
```

如果前端使用 `/api/agent/ws`，Nginx 需要使用：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
}
```

注意 `proxy_pass` 末尾的 `/` 会去掉 `/api/` 前缀。

### 10.4 LoongArch pip 编译失败

检查：

```bash
gcc --version
rustc --version
cargo --version
/opt/nereus/backend/.venv/bin/python -m pip --version
```

常见缺失：

- `openssl-devel`：导致 `cryptography` 或 Python `_ssl` 构建失败。
- `libffi-devel`：导致 CFFI 构建失败。
- `rust` / `cargo`：导致 `cryptography`、`pydantic-core` 构建失败。
- `sqlite-devel`：导致 Python sqlite 模块不可用。

补齐后重新安装：

```bash
sudo -u backend -H bash -lc '
export PATH="$HOME/.cargo/bin:$PATH"
cd /opt/nereus/backend
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
'
```

## 11. 上线检查清单

- 后端以 `backend` 用户运行，不以 root 运行。
- `/etc/nereus/backend.env` 已由部署人员填写真实 LLM Key，并设置为 `root:root 0600`。
- JWT 默认 `SECRET_KEY` 已替换为生产随机密钥。
- `/etc/nereus/admin_token` 与私钥源文件保持 root-only。
- 后端通过 systemd `LoadCredential` 获取凭据。
- 特权代理服务已启动，socket 为 `root:backend 660`。
- Nginx 只向公网暴露 `80/443`，后端 `8000` 仅监听 `127.0.0.1`。
- 前端 dist 文件属于 `root:root`，普通用户不可写。
- 上传限制 `client_max_body_size 3g` 与后端文件限制匹配。
- WebSocket proxy headers 已配置。
- `sudo nereus list-pending` 可正常访问本机 Admin API。
- LoongArch 环境已保留编译工具链或已完成依赖构建。
