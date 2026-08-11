# 麒麟 + LoongArch 部署全流程

本文档面向麒麟高级服务器版 V11 + LoongArch 环境，描述如何把前端静态包 `dist.zip`、后端代码压缩包、Nginx、后端 FastAPI、特权代理 `privileged_agent` 和管理员 CLI 一次性部署起来。

核心约束：

- 所有生产代码必须放在 `/opt` 下。
- `backend` 用户必须有 home 目录，否则 `pip`、`cargo`、`sudo -u backend -H` 会出问题。
- LoongArch 上的 C / Rust 依赖必须给 `backend` 用户可用，不能只给 root 装。
- 运行 `backend` 的命令要显式 `cd /opt/nereus/backend`，必要时加 `PYTHONPATH=/opt/nereus/backend`。
- 特权代理的 `ReadWritePaths` 中列出的目录必须提前创建，否则 systemd 会直接报 `226/NAMESPACE`。

## 1. 目录规划

推荐目录：

| 项 | 路径 |
|---|---|
| 后端代码 | `/opt/nereus/backend` |
| 后端虚拟环境 | `/opt/nereus/backend/.venv` |
| 前端 dist | `/opt/nereus/frontend/dist` |
| Nginx 配置 | `/etc/nginx/conf.d/nereus-panel.conf` |
| 后端服务 | `/etc/systemd/system/nereus-backend.service` |
| 特权代理服务 | `/etc/systemd/system/nereus-privileged-agent.service` |
| root-only 密钥目录 | `/etc/nereus` |
| 特权 socket 目录 | `/run/ndlmpanel` |
| 临时脚本目录 | `/opt/ndlmpanel/tmp_scripts` |

创建用户和目录：

```bash
sudo groupadd --system backend || true
sudo useradd \
  --system \
  --home-dir /var/lib/nereus/backend-home \
  --create-home \
  --gid backend \
  --shell /usr/sbin/nologin \
  backend 2>/dev/null || true

sudo install -d -o backend -g backend -m 0750 /var/lib/nereus/backend-home
sudo install -d -o backend -g backend -m 0750 /opt/nereus/backend
sudo install -d -o root -g root -m 0755 /opt/nereus/frontend
sudo install -d -o root -g root -m 0755 /opt/nereus/frontend/dist
sudo install -d -o root -g root -m 0750 /etc/nereus
sudo install -d -o root -g backend -m 0770 /run/ndlmpanel
sudo install -d -o root -g root -m 0750 /opt/ndlmpanel
sudo install -d -o root -g root -m 0750 /opt/ndlmpanel/tmp_scripts
sudo install -d -o backend -g backend -m 0750 /var/log/nereus
sudo install -d -o root -g root -m 0755 /etc/nginx /var/www /etc/docker /etc/letsencrypt /etc/mysql
```

> **`/run/ndlmpanel` 必须允许后端用户进入并写入**：后端要在其中创建 `backend-rpc.sock`，特权代理创建的 `privileged-agent.sock` 也要能被后端读取，所以目录属组必须是 `backend`、权限 `0770`（不是 `0750 root:root`，否则后端启动直接 `PermissionError`）。建议同时用 tmpfiles 声明，保证重启后依然正确：

```bash
sudo tee /etc/tmpfiles.d/nereus.conf >/dev/null <<'EOF'
d /run/ndlmpanel 0770 root backend -
EOF
sudo systemd-tmpfiles --create /etc/tmpfiles.d/nereus.conf
```

> **backend 的 home 目录必须真实存在**：`useradd` 的 `--home-dir` 只是登记路径，实际目录可能落在别处（例如默认 `/home/backend`）。部署后务必确认：

```bash
getent passwd backend   # 看 home 字段
sudo ls -ld /home/backend /var/lib/nereus/backend-home 2>/dev/null  # 至少一个存在
```

> 若目标机未安装 `rsync`（麒麟 V11 默认不带），`dnf install -y rsync` 未执行时可用 `cp -a` 替代：`sudo cp -a /tmp/nereus-backend/. /opt/nereus/backend/`。

## 2. 解压并发布文件

### 2.1 后端代码

假设你拿到的是 `backend.zip`：

```bash
mkdir -p /tmp/nereus-backend
unzip backend.zip -d /tmp/nereus-backend
sudo rsync -a --delete /tmp/nereus-backend/ /opt/nereus/backend/
sudo chown -R backend:backend /opt/nereus/backend
sudo chmod 0750 /opt/nereus/backend
```

### 2.2 前端静态包

假设你拿到的是 `dist.zip`：

```bash
mkdir -p /tmp/nereus-dist
unzip dist.zip -d /tmp/nereus-dist
sudo rsync -a --delete /tmp/nereus-dist/dist/ /opt/nereus/frontend/dist/
sudo chown -R root:root /opt/nereus/frontend/dist
sudo find /opt/nereus/frontend/dist -type d -exec chmod 0755 {} \;
sudo find /opt/nereus/frontend/dist -type f -exec chmod 0644 {} \;
```

## 3. 安装系统依赖

```bash
sudo dnf makecache || sudo yum makecache
sudo dnf install -y \
  gcc gcc-c++ make cmake pkgconfig \
  openssl-devel libffi-devel zlib-devel bzip2-devel xz-devel \
  sqlite-devel readline-devel ncurses-devel gdbm-devel uuid-devel \
  rust cargo \
  nginx \
  tar gzip curl wget rsync git unzip \
  firewalld policycoreutils-python-utils || \
sudo yum install -y \
  gcc gcc-c++ make cmake pkgconfig \
  openssl-devel libffi-devel zlib-devel bzip2-devel xz-devel \
  sqlite-devel readline-devel ncurses-devel gdbm-devel uuid-devel \
  rust cargo \
  nginx \
  tar gzip curl wget rsync git unzip \
  firewalld policycoreutils-python-utils
```

确认工具链：

```bash
gcc --version
rustc --version
cargo --version
```

如果系统 Rust 太旧，可以再给 `backend` 用户装一份 `rustup`：

```bash
sudo -u backend -H bash -lc 'curl -LsSf https://sh.rustup.rs | sh -s -- -y'
sudo -u backend -H bash -lc 'export PATH="$HOME/.cargo/bin:$PATH"; rustc --version; cargo --version'
```

## 4. 准备 Python 3.13

如果系统已有 Python 3.13，可直接使用；否则自行编译安装。示例：

```bash
cd /usr/local/src
sudo curl -LO https://www.python.org/ftp/python/3.13.9/Python-3.13.9.tgz
sudo tar xf Python-3.13.9.tgz
cd Python-3.13.9
sudo ./configure --prefix=/opt/python/3.13.9 --enable-optimizations --with-ensurepip=install
sudo make -j"$(nproc)"
sudo make altinstall
```

## 5. 安装后端依赖

### 5.1 创建虚拟环境

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
/opt/python/3.13.9/bin/python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
'
```

如果 LoongArch 上部分包没有 wheel，`pip` 会自动源码编译。若报 Rust 错误，再补一次：

```bash
sudo -u backend -H bash -lc '
export PATH="$HOME/.cargo/bin:$PATH"
cd /opt/nereus/backend
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
'
```

### 5.2 验证导入

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
PYTHONPATH=/opt/nereus/backend .venv/bin/python -c "import privileged_agent.server; print(\"ok\")"
'
```

## 6. 生成密钥和 token

先保证 `/etc/nereus` 已存在，然后执行：

```bash
sudo -i bash -c '
cd /opt/nereus/backend
PYTHONPATH=/opt/nereus/backend /opt/nereus/backend/.venv/bin/python -m privileged_agent.crypto generate \
  --priv /etc/nereus/ed25519_priv.pem \
  --pub /etc/nereus/ed25519_pub.pem
chown root:root /etc/nereus/ed25519_priv.pem /etc/nereus/ed25519_pub.pem
chmod 0400 /etc/nereus/ed25519_priv.pem
chmod 0444 /etc/nereus/ed25519_pub.pem
ls -l /etc/nereus/ed25519_priv.pem /etc/nereus/ed25519_pub.pem
'

sudo -i bash -c '
cd /opt/nereus/backend
PYTHONPATH=/opt/nereus/backend /opt/nereus/backend/.venv/bin/python -m privileged_agent.crypto generate \
  --priv /etc/nereus/backend_rpc_ed25519_priv.pem \
  --pub /etc/nereus/backend_rpc_ed25519_pub.pem
chown root:root /etc/nereus/backend_rpc_ed25519_priv.pem /etc/nereus/backend_rpc_ed25519_pub.pem
chmod 0400 /etc/nereus/backend_rpc_ed25519_priv.pem
chmod 0444 /etc/nereus/backend_rpc_ed25519_pub.pem
ls -l /etc/nereus/backend_rpc_ed25519_priv.pem /etc/nereus/backend_rpc_ed25519_pub.pem
'

sudo -i bash -c '
install -o root -g root -m 0400 /dev/null /etc/nereus/admin_token
openssl rand -hex 32 > /etc/nereus/admin_token
chown root:root /etc/nereus/admin_token
chmod 0400 /etc/nereus/admin_token
ls -l /etc/nereus/admin_token
'
```

## 7. 配置特权代理

先写环境文件：

```bash
BACKEND_UID="$(id -u backend)"
sudo tee /etc/nereus/privileged-agent.env >/dev/null <<EOF
NDLM_PRIVILEGED_AGENT_SOCKET=/run/ndlmpanel/privileged-agent.sock
NDLM_PRIVILEGED_AGENT_SOCKET_GROUP=backend
NDLM_PRIVILEGED_AGENT_SOCKET_MODE=660
NDLM_PRIVILEGED_AGENT_PUBKEY=/etc/nereus/ed25519_pub.pem
NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS=${BACKEND_UID}
NDLM_PRIVILEGED_AGENT_NONCE_TTL=300
NDLM_PRIVILEGED_AGENT_TIMESTAMP_TOLERANCE=30
EOF
sudo chown root:root /etc/nereus/privileged-agent.env
sudo chmod 0600 /etc/nereus/privileged-agent.env
```

`ReadWritePaths` 里的目录必须先创建：

- `/run/ndlmpanel`（由 `/etc/tmpfiles.d/nereus.conf` 创建，见第 1 节）
- `/opt/ndlmpanel`
- `/etc/nginx`
- `/var/www`
- `/etc/docker`
- `/etc/letsencrypt`
- `/etc/mysql`

如果不需要某项能力，可以从 `ReadWritePaths` 中删掉，但保留的路径必须真实存在。

> **CapabilityBoundingSet 坑（必看）**：上面的 `CapabilityBoundingSet` 必须包含 `CAP_DAC_OVERRIDE CAP_DAC_READ_SEARCH CAP_CHOWN`，缺了会导致两个典型故障：
> - 缺 `CAP_DAC_OVERRIDE` / `CAP_DAC_READ_SEARCH`：`/opt/nereus/backend` 权限是 `750 backend:backend`，systemd 服务进程即使 UID=0 也读不了代码目录，`python -m privileged_agent.server` 报 `ModuleNotFoundError`（手动跑却正常）；
> - 缺 `CAP_CHOWN`：代理无法把 socket `chown` 成 `root:backend`，报 `PermissionError: [Errno 1] Operation not permitted`。
> 排查时可对比：`sudo systemctl status nereus-privileged-agent` 若在 `activating (auto-restart)` 循环且日志是上述错误，基本就是这个原因。

systemd unit：

```bash
sudo tee /etc/systemd/system/nereus-privileged-agent.service >/dev/null <<'EOF'
[Unit]
Description=Nereus Privileged Agent
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/nereus/backend
EnvironmentFile=/etc/nereus/privileged-agent.env
ExecStart=/opt/nereus/backend/.venv/bin/python -m privileged_agent.server
Restart=always
RestartSec=2
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
ProtectHome=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/run/ndlmpanel /opt/ndlmpanel /etc/nginx /var/www /etc/docker /etc/letsencrypt /etc/mysql
NoNewPrivileges=yes
# 注意：/run/ndlmpanel 由 /etc/tmpfiles.d/nereus.conf 创建（0770 root:backend），
# 不要再写 RuntimeDirectory=ndlmpanel，否则 systemd 会在每次启动时把它重置为 root:root 0750，
# 导致后端无法进入目录（PermissionError）。若一定要用 RuntimeDirectory，请把模式设为 0775 以上并保证 backend 组可写。
RemoveIPC=yes
CapabilityBoundingSet=CAP_DAC_OVERRIDE CAP_DAC_READ_SEARCH CAP_CHOWN CAP_NET_ADMIN CAP_NET_RAW CAP_SYS_ADMIN
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW
MemoryMax=256M
MemoryHigh=192M

[Install]
WantedBy=multi-user.target
EOF
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nereus-privileged-agent
sudo systemctl status nereus-privileged-agent --no-pager
```

检查 socket：

```bash
ls -l /run/ndlmpanel/privileged-agent.sock
```

## 8. 配置后端

后端服务建议使用 `LoadCredential`。如果暂时只想命令行启动，也至少要显式 `PYTHONPATH=/opt/nereus/backend`。

启动前先创建后端运行目录（agent 需要 workspace，日志需要 runtime/logs）：

```bash
sudo install -d -o backend -g backend -m 0750 /opt/nereus/backend/workspace
sudo install -d -o backend -g backend -m 0750 /opt/nereus/backend/runtime/logs
sudo install -d -o backend -g backend -m 0750 /var/log/nereus
```

> `NDLM_TRACE_DB_PATH` 无需配置：trace 审计已并入主库 `panel.db` 的 `agent_trace_logs` 表，部署不需要 `runtime/sqlite/traces.db`。

`/etc/nereus/backend.env` 由部署人员按现场填写。**LLM 配置（provider / endpoint / api_key / model）由数据库管理**——在面板的"配置 → API Key / LLM Profiles"里维护，后端通过默认 profile 读取，**不要**在 `backend.env` 里设 `NDLM_LLM_PROVIDER` / `NDLM_LLM_MODEL`（会覆盖数据库配置，且 mock 只用于兜底）。`backend.env` 里只需要安全/运行时配置（模板见 `docs/deploy-frontend-backend.md` 第 3.1 节，删去 LLM 相关行即可）；文件须 `root:root 0600`。

systemd unit：

```bash
BACKEND_UID="$(id -u backend)"
sudo tee /etc/systemd/system/nereus-backend.service >/dev/null <<EOF
[Unit]
Description=Nereus Backend
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
Environment=NDLM_ADMIN_TOKEN_PATH=/run/credentials/nereus-backend.service/admin_token
Environment=NDLM_ELEVATION_PRIVKEY=/run/credentials/nereus-backend.service/ed25519_priv.pem
Environment=NDLM_BACKEND_RPC_PRIVKEY=/run/credentials/nereus-backend.service/backend_rpc_ed25519_priv.pem
Environment=NDLM_BACKEND_RPC_PUBKEY=/run/credentials/nereus-backend.service/backend_rpc_ed25519_pub.pem
Environment=NDLM_BACKEND_RPC_SOCKET=/run/ndlmpanel/backend-rpc.sock
Environment=NDLM_BACKEND_RPC_SOCKET_GROUP=backend
Environment=NDLM_BACKEND_RPC_SOCKET_MODE=660
Environment=NDLM_BACKEND_RPC_ALLOWED_UIDS=${BACKEND_UID}
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

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nereus-backend
sudo systemctl status nereus-backend --no-pager
```

如果命令行先验证：

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
PYTHONPATH=/opt/nereus/backend .venv/bin/python -m uvicorn main:fastApiInstance \
  --host 127.0.0.1 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips=127.0.0.1
'
```

## 9. 配置 Nginx

`/api` 重写规则的关键是末尾的 `/`。`location /api/` 配合 `proxy_pass http://127.0.0.1:8000/;` 会自动去掉 `/api/` 前缀，所以：

- `/api/agent/ws` -> `/agent/ws`
- `/api/file/list` -> `/file/list`

配置文件：

```bash
sudo tee /etc/nginx/conf.d/nereus-map.conf >/dev/null <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
EOF

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

启动：

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

## 10. 验证

```bash
sudo systemctl status nereus-privileged-agent --no-pager
sudo systemctl status nereus-backend --no-pager
sudo systemctl status nginx --no-pager

ls -l /run/ndlmpanel/privileged-agent.sock
ls -l /run/ndlmpanel/backend-rpc.sock
ss -lntp | grep ':8000'
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/api/agent/sessions
sudo nereus list-pending
```

期望结果：

- 三个服务均为 `active (running)` / `enabled`
- `/run/ndlmpanel/` 目录权限 `drwxrwx--- root backend`
- `privileged-agent.sock` 为 `srw-rw---- root backend`
- `backend-rpc.sock` 为 `srw-rw---- backend backend`
- `curl http://127.0.0.1/` 返回前端页面（200）
- `curl http://127.0.0.1/api/agent/sessions` 返回 401（后端存活、鉴权生效，说明 `/api/` 前缀重写与转发成功）
- `sudo nereus list-pending` 输出"没有待审批的特权码"（CLI → admin_token → 后端 → 特权代理全链路打通）

## 11. 常见坑

- 代码没放到 `/opt` 下，systemd 或 `ProtectHome` 会直接卡住。
- `backend` 没有 home 目录，`pip` 和 `cargo` 找不到写缓存的位置。
- `privileged-agent.env` 里列出的 `ReadWritePaths` 有路径不存在，直接 `226/NAMESPACE`。
- `panel.db` 不属于 `backend:backend` 或目录不可写，SQLite 启动时会失败。
- 前端 API 前缀不是 `/api`，但 Nginx 还按 `/api/` 去重写。
- `proxy_pass` 末尾少了 `/`，导致 `/api` 前缀没有被剥掉。
- 从开发机打包代码时，检查 `pyproject.toml` 的 `[tool.ndlmpanel-agent] workspace_dir` 不能是开发机绝对路径（应为空，自动推断到项目根 `workspace/`），并确认 `/opt/nereus/backend/workspace` 已创建且属主 `backend:backend`。
- `CapabilityBoundingSet` 缺 `CAP_DAC_OVERRIDE` / `CAP_DAC_READ_SEARCH` / `CAP_CHOWN`：特权代理 `python -m privileged_agent.server` 报 `ModuleNotFoundError` 或 `chown` 报 `Operation not permitted`，服务在 `activating (auto-restart)` 无限循环（手动运行却正常）。这是最隐蔽的坑。
- `/run/ndlmpanel` 目录是 `root:root 0750`：后端启动报 `PermissionError: ... '/run/ndlmpanel/backend-rpc.sock'`（进不去目录、写不了）。目录必须是 `0770 root:backend` 且不能用 `RuntimeDirectory` 覆盖成 `0750`。
- 目标机没有 `rsync`：文档示例命令会静默失败（`&&` 不执行、目录为空），先 `dnf install -y rsync`，或改用 `cp -a`。

