# Privileged Agent 部署说明

本文档说明如何部署本项目的本机 root 特权代理 `privileged_agent`。

这个代理负责承接需要宿主机高权限的操作，例如：

- 读取防火墙状态
- 获取防火墙规则
- 新增放行端口规则
- 开关 `firewalld` / `ufw`
- 开关 `ssh` / `sshd`

主 FastAPI 后端继续以普通用户运行，通过 Unix socket 与代理通信。

## 一、整体结构

- 主后端：普通用户运行
- 特权代理：`root` 运行
- 通信方式：本机 Unix Domain Socket
- 默认 socket 路径：`/run/ndlmpanel/privileged-agent.sock`

当前 systemd 示例文件：

- [deploy/systemd/nereus-privileged-agent.service](/home/he/workspace/python/NereusDoorLoongMagicPanel-backend/deploy/systemd/nereus-privileged-agent.service)

## 二、生产环境部署

下面假设：

- 项目部署目录：`/opt/nereus/backend`
- 后端运行用户：`backend`
- Python 虚拟环境：`/opt/nereus/backend/.venv`
- 允许访问 socket 的组名：`backend`

### 1. 准备组和用户

如果后端用户还没有专门的组，可以执行：

```bash
sudo groupadd backend
sudo usermod -aG backend backend
```

如果组已经存在，只执行 `usermod -aG` 即可。

### 2. 调整 systemd unit

编辑：

```bash
sudo cp /opt/nereus/backend/deploy/systemd/nereus-privileged-agent.service /etc/systemd/system/
sudo vim /etc/systemd/system/nereus-privileged-agent.service
```

重点确认这几项：

```ini
WorkingDirectory=/opt/nereus/backend
Environment=NDLM_PRIVILEGED_AGENT_SOCKET=/run/ndlmpanel/privileged-agent.sock
Environment=NDLM_PRIVILEGED_AGENT_SOCKET_GROUP=backend
Environment=NDLM_PRIVILEGED_AGENT_SOCKET_MODE=660
ExecStart=/opt/nereus/backend/.venv/bin/python -m privileged_agent.server
```

### 3. 启动特权代理

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nereus-privileged-agent
```

### 4. 检查运行状态

```bash
sudo systemctl status nereus-privileged-agent
ls -l /run/ndlmpanel/privileged-agent.sock
```

正常情况下应看到：

- service 状态为 `active (running)`
- socket 文件存在
- socket 属主为 `root`
- socket 属组为你设置的组，例如 `backend`
- socket 权限为 `srw-rw----`

### 5. 重启主后端

如果你刚把后端用户加入了新的组，必须重启后端进程，否则旧进程不会拿到新的组权限。

```bash
sudo systemctl restart <你的后端服务名>
```

## 三、主后端 service 依赖

建议让主后端在代理之后启动。

如果你的后端也使用 systemd，可以在它自己的 unit 中加入：

```ini
[Unit]
After=nereus-privileged-agent.service
Requires=nereus-privileged-agent.service
```

如果后端也要显式指定 socket 路径，可在后端 unit 中增加：

```ini
Environment=NDLM_PRIVILEGED_AGENT_SOCKET=/run/ndlmpanel/privileged-agent.sock
Environment=NDLM_PRIVILEGED_AGENT_TIMEOUT_SECONDS=5
```

## 四、开发环境推荐方案

假设你本机有一个 sudo 用户 `he`。

### 方案 A：宿主机直接开发

这是最推荐的开发方式。最简单，和生产形态也最接近。

假设你的代码目录是：

```text
/home/he/workspace/python/NereusDoorLoongMagicPanel-backend
```

#### 1. 为开发环境准备一个组

可以继续沿用 `he` 组，或者单独建一个组。为了简单，这里直接用 `he`：

```bash
id he
```

如果 `he` 用户存在，就把代理 socket 组也配置成 `he`。

#### 2. 临时启动代理

先确保虚拟环境已安装依赖，然后执行：

```bash
cd /home/he/workspace/python/NereusDoorLoongMagicPanel-backend
sudo env \
  NDLM_PRIVILEGED_AGENT_SOCKET=/run/ndlmpanel/privileged-agent.sock \
  NDLM_PRIVILEGED_AGENT_SOCKET_GROUP=he \
  NDLM_PRIVILEGED_AGENT_SOCKET_MODE=660 \
  /home/he/workspace/python/NereusDoorLoongMagicPanel-backend/.venv/bin/python -m privileged_agent.server
```

这个命令会前台运行，适合先验证链路。

然后另开一个终端，以 `he` 身份启动后端：

```bash
cd /home/he/workspace/python/NereusDoorLoongMagicPanel-backend
uv run python main.py
```

如果 `he` 是当前开发用户，并且 socket 组也是 `he`，那后端就可以直接访问代理。

#### 3. 开发环境做成 systemd user + root agent

如果你想更接近生产，可以：

- root 代理走系统级 systemd
- 后端继续手工运行，或者走你自己的开发脚本

建议把 `deploy/systemd/nereus-privileged-agent.service` 复制到 `/etc/systemd/system/`，并把组改成 `he`：

```ini
Environment=NDLM_PRIVILEGED_AGENT_SOCKET_GROUP=he
WorkingDirectory=/home/he/workspace/python/NereusDoorLoongMagicPanel-backend
ExecStart=/home/he/workspace/python/NereusDoorLoongMagicPanel-backend/.venv/bin/python -m privileged_agent.server
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl restart nereus-privileged-agent
sudo systemctl status nereus-privileged-agent
```

### 方案 B：后端跑在 Docker 容器里开发

这种方式更麻烦，不推荐作为第一选择。

原因是：

- root 代理运行在宿主机
- 后端运行在容器内
- 容器必须能访问宿主机的 Unix socket
- 容器内进程的 gid 还必须匹配 socket 组权限

如果确实要这么做，至少要满足：

1. 把宿主机 socket 挂进容器，例如：

```bash
-v /run/ndlmpanel/privileged-agent.sock:/run/ndlmpanel/privileged-agent.sock
```

2. 容器内后端进程要有对应 gid 的访问权限

3. 容器内环境变量要指向同一个 socket 路径

```text
NDLM_PRIVILEGED_AGENT_SOCKET=/run/ndlmpanel/privileged-agent.sock
```

如果你只是本地开发调试防火墙能力，不建议先走这条路。

## 五、排查方法

### 1. 看代理服务日志

```bash
sudo journalctl -u nereus-privileged-agent -f
```

### 2. 看 socket 权限

```bash
ls -l /run/ndlmpanel/privileged-agent.sock
id <后端运行用户>
```

确认后端运行用户属于 socket 对应组。

### 3. 常见错误

#### `特权代理未启动`

说明主后端连不到 socket。

检查：

- `nereus-privileged-agent.service` 是否已启动
- `NDLM_PRIVILEGED_AGENT_SOCKET` 路径是否一致
- socket 文件是否真的存在

#### `无权访问特权代理`

说明 socket 权限不匹配。

检查：

- `NDLM_PRIVILEGED_AGENT_SOCKET_GROUP`
- 后端运行用户是否在该组中
- 后端进程是否已重启并拿到新组权限

#### `系统命令执行失败`

说明代理已连通，但宿主机命令本身失败。

检查：

- `ufw` / `firewall-cmd` 是否已安装
- `systemctl` 对目标服务是否有效
- 当前宿主机是否真的使用对应防火墙后端

## 六、当前限制

- 代理目前只允许白名单动作，不支持任意 shell 命令
- 当前允许操作的 systemd 服务只有：
  - `ssh`
  - `sshd`
  - `firewalld`
- SSH 配置文件写入逻辑目前仍在主服务里，尚未迁入代理
- 如果将来把 Docker、文件权限、更多系统服务迁入代理，建议继续保持“动作白名单 + 参数校验”的模式，不要退化成通用 root 执行器
