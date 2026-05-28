# 项目名称
> 项目正在开发中 🚧

一个基于 **Linux + uv** 管理的 Python 项目

## 快速开始（Linux 环境）
**⚠️ 仅支持 Linux 系统**，请确保你的运行环境为 Linux

### 1. Fork 并克隆仓库
1. 点击本仓库右上角的 **Fork**，将项目复刻到你的 GitHub 账号下
2. 克隆你 fork 后的仓库到本地：
```bash
git clone https://github.com/你的用户名/项目名.git
cd 项目名
```

### 2. 安装 uv 包管理器
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. 安装指定 Python 版本
```bash
uv python install 3.13.9
```

### 4. 创建虚拟环境
```bash
uv venv
```

### 5. 安装项目依赖
```bash
uv sync
```

### 6. 运行项目
```bash
python main.py
```

## 开发状态
✅ 环境配置流程已完成
🔄 核心功能开发中...

---

## Web Terminal 备忘

本次新增了一套 Web Terminal 后端能力，采用现有 `controller / service / dao` 三层结构实现。

### 已新增的接口

- `GET /terminal/available`
  - 检查普通终端是否可用
  - 会检查宿主机是否安装 Docker，以及默认业务容器是否存在且正在运行
  - 如果不可用，会抛出业务异常并走全局异常处理，前端应据此禁止打开终端

- `WS /terminal/ws`
  - WebSocket 终端主入口
  - 支持普通终端实时输入输出
  - 支持窗口 resize
  - 支持通过 `admin_login` 切换到管理员真实宿主机终端

- `POST /terminal/session/log`
  - 查询终端会话审计日志
  - 当前首版只记录会话元数据，不记录全量输入输出

### 已新增的消息协议

前端发送：

```json
{ "type": "input", "data": "ls -la\n" }
```

```json
{ "type": "resize", "cols": 120, "rows": 30 }
```

```json
{ "type": "admin_login", "username": "he", "password": "******" }
```

后端发送：

```json
{ "type": "output", "data": "..." }
```

```json
{ "type": "state", "sessionId": "xxx", "mode": "normal", "linuxUser": "appuser", "title": "user@app-container" }
```

```json
{ "type": "admin_login_result", "success": true, "mode": "admin", "msg": "管理员终端创建成功" }
```

```json
{ "type": "error", "code": "terminal_error", "msg": "..." }
```

### 模式说明

#### 1. 普通终端

默认进入普通终端，当前实现为固定容器：

```bash
docker exec -it app-container bash
```

普通终端用于：

- 项目调试
- 日志查看
- 常规 Linux 命令操作

普通终端不应直接暴露真实宿主机。

#### 2. 管理员真实终端

在普通终端会话内，前端可发送：

```json
{ "type": "admin_login", "username": "he", "password": "******" }
```

后端会先调用 Linux PAM 认证，认证成功后重新创建 PTY，进入：

```bash
sudo -u he -i
```

此时终端能力等价于该 Linux 用户直接 SSH 登录宿主机。

### 当前依赖

本次为管理员模式新增了 PAM Python 依赖：

```text
python-pam==2.0.2
```

安装方式：

```bash
uv sync
```

### 宿主机前置条件

要让终端功能真正可用，运行后端的 Linux 宿主机至少要满足：

- 已安装 Docker
- 普通终端对应的业务容器已存在且正在运行
- 已安装 `sudo`
- PAM 环境可用
- 后端运行用户具备执行管理员 shell 的 sudo 权限

### Docker 不可用时的行为

系统会在打开终端前做普通终端可用性检查：

- 没有安装 Docker
- 默认容器不存在
- 默认容器未运行

以上任一情况都会直接报业务错误，前端不应允许用户继续使用终端功能。

### sudoers 配置说明

管理员模式不是项目内权限配置，而是 Linux 宿主机权限配置。

当前代码执行的是：

```bash
sudo -u <linux_username> -i
```

因此必须给“运行 FastAPI 后端的 Linux 用户”配置 `sudoers`。

例如：

- 后端服务运行用户：`backend`
- 普通终端用户：`appuser`
- 管理员 Linux 用户：`he`

建议在宿主机上编辑：

```bash
sudo visudo -f /etc/sudoers.d/nereus-terminal
```

然后写入类似配置：

```sudoers
backend ALL=(he) NOPASSWD: ALL
```

上面这条最容易跑通，但权限过大，只建议临时验证。

更推荐后续收敛成固定脚本白名单，例如：

```sudoers
backend ALL=(he) NOPASSWD: /usr/local/bin/enter-real-shell
```

不要直接手改 `/etc/sudoers`，优先使用 `/etc/sudoers.d/` 并通过 `visudo` 校验语法。

### 当前可配置环境变量

终端服务当前支持以下环境变量：

```text
NDLM_TERMINAL_NORMAL_CONTAINER=app-container
NDLM_TERMINAL_NORMAL_LINUX_USER=appuser
NDLM_TERMINAL_NORMAL_SHELL=bash
NDLM_TERMINAL_IDLE_TIMEOUT_SECONDS=1800
NDLM_TERMINAL_ADMIN_MAX_FAILED_ATTEMPTS=5
```

### 审计说明

当前版本会记录终端会话元数据，包括：

- `sessionId`
- 面板用户 ID 和用户名
- 客户端 IP
- 当前模式
- 普通终端容器名
- 管理员 Linux 用户名
- 管理员认证是否尝试/是否成功/失败次数
- 开始时间、结束时间、关闭原因、退出码

当前版本不记录：

- 全量终端输入
- 全量终端输出
- 命令级回放

### 额外注意事项

- `admin_login` 的密码不会进入普通终端输入流，也不会落库
- WebSocket 鉴权不走现有 HTTP 中间件，而是在终端控制器里单独校验 `accessToken`
- 如果前端直接连 `WS /terminal/ws` 且普通终端不可用，连接会被直接拒绝
- 如果需要真正上线管理员模式，必须先在目标机器完成 `sudoers` 和 PAM 环境验证
