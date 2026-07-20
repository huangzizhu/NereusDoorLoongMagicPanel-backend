# 特权代理与 CLI 部署文档

本文档描述 Nereus 运维平台中特权代理 `privileged_agent` 与管理员 CLI `nereus` 的生产部署方式。目标是让主后端保持普通用户权限运行，将 root 级操作收敛到本机特权代理，并通过 CLI 审批、Ed25519 签名、Unix Socket 权限和命令注册表完成安全闭环。

## 1. 部署目标

部署完成后应满足以下目标：

- 主后端以普通系统用户 `backend` 运行。
- 特权代理以 `root` 运行，但只监听本机 Unix Domain Socket。
- 后端只能通过受控 socket 调用特权代理。
- 管理员通过 `sudo nereus approve <CODE>` 审批特权请求。
- `/etc/nereus` 下的关键源文件保持 `root:root` 与 `0400` 权限。
- 特权请求带 Ed25519 签名、timestamp、nonce 与参数 hash，防止伪造、篡改和重放。

## 2. 推荐路径与用户模型

本文使用以下生产路径作为示例：

| 项 | 推荐值 |
|---|---|
| 项目目录 | `/opt/nereus/backend` |
| 后端用户 | `backend` |
| 后端用户组 | `backend` |
| 特权代理服务名 | `nereus-privileged-agent.service` |
| 特权代理 socket | `/run/ndlmpanel/privileged-agent.sock` |
| 密钥与审批 token 目录 | `/etc/nereus` |
| CLI 路径 | `/usr/local/sbin/nereus` |
| 临时脚本目录 | `/opt/ndlmpanel/tmp_scripts` |

生产环境必须将代码部署在 `/opt/nereus/backend` 这类系统服务目录下。不要从部署人员的 `/home/<user>/workspace` 目录直接运行 systemd 服务；`ProtectHome`、目录遍历权限和 `PYTHONPATH` 都可能导致 `ModuleNotFoundError` 或 `Permission denied`。

权限边界如下：

```text
backend 用户
  -> 运行 FastAPI 后端
  -> 连接 /run/ndlmpanel/privileged-agent.sock
  -> 不拥有 root 权限

root 特权代理
  -> 读取 Ed25519 公钥
  -> 验证签名、timestamp、nonce、命令注册表、参数 hash
  -> 执行白名单特权动作

sudo 管理员 CLI
  -> 读取 root-only admin_token
  -> 调用 localhost Admin API
  -> 批准、拒绝、吊销特权码
```

## 3. 创建系统用户与目录

创建专用后端用户和组：

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

如果系统没有 `/usr/sbin/nologin`，可使用 `/sbin/nologin`：

```bash
getent passwd backend
```

如果用户已经用 `--no-create-home` 创建过，必须补齐 home 目录，否则 `pip`、`cargo`、缓存目录和 `sudo -u backend -H` 可能报错：

```bash
sudo install -d -o backend -g backend -m 0750 /var/lib/nereus/backend-home
sudo usermod -d /var/lib/nereus/backend-home backend
```

创建关键目录：

```bash
sudo install -d -o root -g root -m 0750 /etc/nereus
sudo install -d -o root -g root -m 0750 /run/ndlmpanel
sudo install -d -o root -g root -m 0750 /opt/ndlmpanel
sudo install -d -o root -g root -m 0750 /opt/ndlmpanel/tmp_scripts
sudo install -d -o backend -g backend -m 0750 /opt/nereus/backend
sudo install -d -o root -g root -m 0755 /etc/nginx /var/www /etc/docker /etc/letsencrypt /etc/mysql
```

确认后端用户 UID，后续 systemd 会用到：

```bash
id -u backend
id backend
```

## 4. 准备项目代码与 Python 环境

特权代理使用同一份后端代码运行。本文假设后端代码已放在：

```text
/opt/nereus/backend
```

且 Python 虚拟环境已存在：

```text
/opt/nereus/backend/.venv
```

如果尚未部署后端环境，请先完成前后端部署文档中的后端 Python 环境步骤，再回到本文继续。

检查特权代理入口是否可导入：

```bash
sudo -u backend -H bash -lc '
cd /opt/nereus/backend
PYTHONPATH=/opt/nereus/backend .venv/bin/python -c "import privileged_agent.server; print(\"ok\")"
'
```

## 5. 生成 Ed25519 密钥

### 5.1 特权代理签名密钥

后端持有私钥，用于签名特权请求；特权代理持有公钥，用于验签。

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
```

私钥必须保持 root-only：

```bash
sudo ls -l /etc/nereus/ed25519_priv.pem /etc/nereus/ed25519_pub.pem
```

期望结果：

```text
-r-------- root root /etc/nereus/ed25519_priv.pem
-r--r--r-- root root /etc/nereus/ed25519_pub.pem
```

### 5.2 后端内部 RPC 密钥

AgentCore 与后端内部 RPC 通信也支持 Ed25519 签名。建议一并生成：

```bash
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
```

## 6. 生成 root-only admin_token

`admin_token` 是 CLI 调用本机 Admin API 的 Bearer Token。该文件必须由 root 持有，不应被普通用户直接读取。

```bash
sudo -i bash -c '
install -o root -g root -m 0400 /dev/null /etc/nereus/admin_token
openssl rand -hex 32 > /etc/nereus/admin_token
chown root:root /etc/nereus/admin_token
chmod 0400 /etc/nereus/admin_token
ls -l /etc/nereus/admin_token
'
```

期望结果：

```text
-r-------- root root /etc/nereus/admin_token
```

注意：后端进程需要读取 token 和私钥。为了同时满足“源文件 root-only”和“后端非 root 运行”，推荐在后端 systemd 服务中使用 `LoadCredential`。后端读取的是 systemd 注入到 `/run/credentials/<unit>/` 的临时凭据副本，而不是直接读取 `/etc/nereus` 源文件。

## 7. 安装 CLI

将 CLI 安装到系统路径：

```bash
sudo install -o root -g root -m 0755 \
  /opt/nereus/backend/deploy/cli/nereus \
  /usr/local/sbin/nereus

sudo ln -sf /usr/local/sbin/nereus /usr/local/bin/nereus
```

检查：

```bash
which nereus
sudo nereus help
```

CLI 默认读取：

```text
NDLM_ADMIN_TOKEN_PATH=/etc/nereus/admin_token
NDLM_ADMIN_URL=http://127.0.0.1:8000
```

如后端端口不是 `8000`，执行 CLI 时可指定：

```bash
sudo NDLM_ADMIN_URL=http://127.0.0.1:8080 nereus list-pending
```

## 8. 配置特权代理环境变量

推荐将特权代理配置写入 `/etc/nereus/privileged-agent.env`。该文件由 root 管理，避免把可变配置散落在命令行中。

获取后端用户 UID：

```bash
BACKEND_UID="$(id -u backend)"
echo "$BACKEND_UID"
```

创建配置文件：

```bash
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

部署人员需要根据现场环境确认：

| 变量 | 说明 |
|---|---|
| `NDLM_PRIVILEGED_AGENT_SOCKET_GROUP` | 必须是后端用户所属组，推荐 `backend` |
| `NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS` | 必须包含后端进程 UID |
| `NDLM_PRIVILEGED_AGENT_PUBKEY` | 必须指向 Ed25519 公钥 |
| `NDLM_PRIVILEGED_AGENT_SOCKET` | 必须与后端 `NDLM_PRIVILEGED_AGENT_SOCKET` 保持一致 |

## 9. 配置特权代理 systemd 服务

创建 systemd unit：

```bash
sudo tee /etc/systemd/system/nereus-privileged-agent.service >/dev/null <<EOF
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
RuntimeDirectory=ndlmpanel
RuntimeDirectoryMode=0750
RemoveIPC=yes
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_SYS_ADMIN
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW
MemoryMax=256M
MemoryHigh=192M

[Install]
WantedBy=multi-user.target
EOF
```

说明：

- `NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS` 在 `/etc/nereus/privileged-agent.env` 中配置，必须包含后端进程 UID。
- `NDLM_PRIVILEGED_AGENT_SOCKET_GROUP=backend` 让后端用户所在组可连接 socket。
- `ReadWritePaths` 应按实际运维能力收敛。不使用的目录应删除；保留的目录必须提前存在，否则 systemd 会在启动前报 `status=226/NAMESPACE`。
- `ProtectSystem=strict` 会阻止特权代理写未声明路径，这是安全边界的一部分。

## 10. 启动特权代理

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nereus-privileged-agent
sudo systemctl status nereus-privileged-agent --no-pager
```

检查 socket：

```bash
ls -l /run/ndlmpanel/privileged-agent.sock
id backend
```

期望结果：

```text
srw-rw---- root backend /run/ndlmpanel/privileged-agent.sock
```

## 11. 后端服务中的凭据注入要求

后端 systemd 服务需要读取以下文件：

- `admin_token`
- `ed25519_priv.pem`
- `backend_rpc_ed25519_priv.pem`
- `backend_rpc_ed25519_pub.pem`

推荐在后端 unit 中使用：

```ini
LoadCredential=admin_token:/etc/nereus/admin_token
LoadCredential=ed25519_priv.pem:/etc/nereus/ed25519_priv.pem
LoadCredential=backend_rpc_ed25519_priv.pem:/etc/nereus/backend_rpc_ed25519_priv.pem
LoadCredential=backend_rpc_ed25519_pub.pem:/etc/nereus/backend_rpc_ed25519_pub.pem

Environment=NDLM_ADMIN_TOKEN_PATH=/run/credentials/nereus-backend.service/admin_token
Environment=NDLM_ELEVATION_PRIVKEY=/run/credentials/nereus-backend.service/ed25519_priv.pem
Environment=NDLM_BACKEND_RPC_PRIVKEY=/run/credentials/nereus-backend.service/backend_rpc_ed25519_priv.pem
Environment=NDLM_BACKEND_RPC_PUBKEY=/run/credentials/nereus-backend.service/backend_rpc_ed25519_pub.pem
```

如果后端 unit 名不是 `nereus-backend.service`，需要把 `/run/credentials/nereus-backend.service/` 改为实际 unit 名。

不推荐将 `/etc/nereus/admin_token` 或私钥直接 `chown backend:backend`。这种方式虽然能让后端读取，但不再满足源文件 root-only 要求。

## 12. CLI 环境变量配置

CLI 默认读取 `/etc/nereus/admin_token` 并访问 `http://127.0.0.1:8000`。如果后端端口或 token 路径有变化，可以在执行时显式传入：

```bash
sudo NDLM_ADMIN_URL=http://127.0.0.1:8080 \
  NDLM_ADMIN_TOKEN_PATH=/etc/nereus/admin_token \
  nereus list-pending
```

也可以创建一个仅供管理员参考的配置文件：

```bash
sudo tee /etc/nereus/nereus-cli.env >/dev/null <<'EOF'
NDLM_ADMIN_URL=http://127.0.0.1:8000
NDLM_ADMIN_TOKEN_PATH=/etc/nereus/admin_token
EOF

sudo chown root:root /etc/nereus/nereus-cli.env
sudo chmod 0600 /etc/nereus/nereus-cli.env
```

使用时：

```bash
sudo env $(sudo grep -v '^#' /etc/nereus/nereus-cli.env | xargs) nereus list-pending
```

注意：`sudo` 默认会清理大部分环境变量，所以不要假设普通用户 shell 中的环境变量会自动传递给 CLI。

## 13. 联调验证

### 13.1 验证特权代理状态

```bash
sudo systemctl status nereus-privileged-agent --no-pager
sudo journalctl -u nereus-privileged-agent -n 100 --no-pager
ls -l /run/ndlmpanel/privileged-agent.sock
```

### 13.2 验证 CLI 与后端 Admin API

该步骤要求后端服务已启动。

```bash
sudo nereus list-pending
```

也可直接验证 Admin API：

```bash
TOKEN="$(sudo cat /etc/nereus/admin_token)"
curl -sS \
  -H "Authorization: Bearer ${TOKEN}" \
  http://127.0.0.1:8000/admin/elevation/pending
```

期望返回项目统一响应结构，且 `code` 为 `1`。

### 13.3 验证 root-only 文件

```bash
sudo namei -l /etc/nereus/admin_token
sudo ls -l /etc/nereus
```

关键文件建议权限：

| 文件 | 权限 |
|---|---|
| `/etc/nereus/admin_token` | `root:root 0400` |
| `/etc/nereus/ed25519_priv.pem` | `root:root 0400` |
| `/etc/nereus/ed25519_pub.pem` | `root:root 0444` |
| `/etc/nereus/backend_rpc_ed25519_priv.pem` | `root:root 0400` |
| `/etc/nereus/backend_rpc_ed25519_pub.pem` | `root:root 0444` |

## 14. 常见问题

### 14.1 后端提示“admin_token 不可用”

原因通常是后端服务没有通过 `LoadCredential` 获得 token，或 `NDLM_ADMIN_TOKEN_PATH` 指向错误。

检查：

```bash
sudo systemctl cat nereus-backend
sudo systemctl show nereus-backend -p LoadCredential
sudo journalctl -u nereus-backend -n 100 --no-pager
```

### 14.2 特权代理提示“无权访问特权代理”

检查 socket 权限与后端 UID：

```bash
id backend
ls -l /run/ndlmpanel/privileged-agent.sock
systemctl show nereus-privileged-agent -p Environment
```

确认：

- socket group 是 `backend`。
- socket mode 是 `660`。
- `NDLM_PRIVILEGED_AGENT_ALLOWED_UIDS` 包含 `id -u backend`。
- 后端服务已重启，拿到了最新用户组。

### 14.3 签名验证失败

检查后端私钥与特权代理公钥是否匹配：

```bash
sudo ls -l /etc/nereus/ed25519_*.pem
sudo systemctl show nereus-privileged-agent -p Environment
sudo journalctl -u nereus-privileged-agent -n 200 --no-pager
```

如果重新生成了密钥，必须同时重启后端和特权代理：

```bash
sudo systemctl restart nereus-backend
sudo systemctl restart nereus-privileged-agent
```

### 14.4 CLI 无法连接后端

确认后端监听本机端口：

```bash
ss -lntp | grep 8000
curl -sS http://127.0.0.1:8000/system/health --max-time 3
```

如果后端端口不是 `8000`：

```bash
sudo NDLM_ADMIN_URL=http://127.0.0.1:<PORT> nereus list-pending
```

## 15. 安全检查清单

上线前至少确认：

- `/etc/nereus/admin_token` 是 `root:root 0400`。
- `/etc/nereus/*_priv.pem` 是 `root:root 0400`。
- `/etc/nereus/privileged-agent.env` 是 `root:root 0600`，且 `ALLOWED_UIDS` 已填写真实后端 UID。
- `/etc/nereus/nereus-cli.env` 如存在，应为 `root:root 0600`。
- 后端通过 systemd `LoadCredential` 读取凭据。
- 后端服务不以 root 运行。
- 特权代理 socket 是 `root:backend 660`。
- 特权代理只允许后端 UID 连接。
- `ReadWritePaths` 已按实际业务收敛。
- 未给 `backend` 用户配置宽泛 sudo 权限。
- CLI 审批必须通过 `sudo` 执行。
- 生产环境定期轮换 `admin_token` 与 Ed25519 密钥。
