# Terminal Apifox 测试说明

## 1. 测试前准备

- 后端服务已启动，例如 `http://127.0.0.1:8000`
- 先通过登录接口拿到 `accessToken`，并在 Apifox 中以 Cookie 方式携带
- 普通终端测试需要：
  - 宿主机已安装 Docker
  - `NDLM_TERMINAL_NORMAL_CONTAINER` 对应容器存在且正在运行
- 管理员终端测试需要：
  - 宿主机已安装 `sudo`
  - 宿主机已安装 `su`
  - 目标 Linux 用户可以本地登录
  - 运行后端的 Linux 用户已配置好 `sudo -u <linux_username> -i` 权限

## 2. 登录并携带 Cookie

先调用登录接口，成功后取响应里的 `accessToken`。

Apifox HTTP 与 WebSocket 请求都要携带：

```text
Cookie: accessToken=你的token
```

如果不带这个 Cookie，HTTP 会返回鉴权失败，WebSocket 会直接关闭连接。

## 3. HTTP 接口测试

### 3.1 检查普通终端是否可用

- 方法：`GET`
- 地址：`/terminal/available`

成功示例：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "normalTerminalAvailable": true,
    "normalContainerName": "app-container"
  }
}
```

失败场景：

- 没有安装 Docker
- 容器不存在
- 容器未运行

这时会返回业务错误，表示普通终端不可用。

### 3.2 查询终端会话日志

- 方法：`POST`
- 地址：`/terminal/session/log`
- Body:

```json
{
  "page": 1,
  "pageSize": 10
}
```

成功示例：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "total": 1,
    "items": [
      {
        "sessionId": "xxx",
        "userId": 1,
        "panelUsername": "admin",
        "clientIp": "127.0.0.1",
        "mode": "admin",
        "normalContainerName": "app-container",
        "adminLinuxUsername": "he",
        "adminAuthAttempted": true,
        "adminAuthSucceeded": true,
        "adminAuthFailedCount": 0,
        "startTime": "2026-05-28T10:00:00",
        "endTime": "2026-05-28T10:10:00",
        "closeReason": "client_disconnect",
        "exitCode": 0,
        "logId": 1
      }
    ]
  }
}
```

## 4. WebSocket 普通终端测试

### 4.1 建立连接

- 方法：`WS`
- 地址：`/terminal/ws?cols=120&rows=30`
- Header 或 Cookie 中携带 `accessToken`

说明：

- `cols`：终端列数，范围 `1-500`
- `rows`：终端行数，范围 `1-500`

连接成功后，服务端先返回一条 `state`：

```json
{
  "type": "state",
  "sessionId": "xxx",
  "mode": "normal",
  "linuxUser": "appuser",
  "title": "admin@app-container"
}
```

如果普通终端不可用，这个连接会直接关闭，原因是 `terminal_unavailable`。

### 4.2 发送输入

客户端发送：

```json
{
  "type": "input",
  "data": "ls -la\n"
}
```

服务端返回：

```json
{
  "type": "output",
  "data": "..."
}
```

### 4.3 调整窗口大小

客户端发送：

```json
{
  "type": "resize",
  "cols": 160,
  "rows": 40
}
```

### 4.4 在普通终端内切管理员

客户端发送：

```json
{
  "type": "admin_login",
  "username": "he",
  "password": "你的Linux密码"
}
```

成功返回：

```json
{
  "type": "admin_login_result",
  "success": true,
  "mode": "admin",
  "msg": "管理员终端创建成功"
}
```

随后还会收到新的 `state`：

```json
{
  "type": "state",
  "sessionId": "xxx",
  "mode": "admin",
  "linuxUser": "he",
  "title": "he@host"
}
```

密码错误时返回：

```json
{
  "type": "admin_login_result",
  "success": false,
  "mode": "normal",
  "msg": "Linux 用户名或密码错误"
}
```

## 5. WebSocket 管理员直连测试

### 5.1 建立连接

- 方法：`WS`
- 地址：`/terminal/admin/ws?cols=120&rows=30`
- Header 或 Cookie 中携带 `accessToken`

这个入口不检查 Docker，所以即使普通终端不可用，也可以继续测管理员模式。

### 5.2 首条消息必须发 admin_login

客户端首条消息发送：

```json
{
  "type": "admin_login",
  "username": "he",
  "password": "你的Linux密码"
}
```

成功返回：

```json
{
  "type": "admin_login_result",
  "success": true,
  "mode": "admin",
  "msg": "管理员终端创建成功"
}
```

随后服务端再发送：

```json
{
  "type": "state",
  "sessionId": "xxx",
  "mode": "admin",
  "linuxUser": "he",
  "title": "he@host"
}
```

之后就可以继续发送普通终端消息：

```json
{
  "type": "input",
  "data": "whoami\n"
}
```

```json
{
  "type": "resize",
  "cols": 150,
  "rows": 45
}
```

### 5.3 首条消息不是 admin_login

如果首条消息发的是：

```json
{
  "type": "input",
  "data": "pwd\n"
}
```

会返回：

```json
{
  "type": "error",
  "code": "invalid_message",
  "msg": "管理员直连首条消息必须为admin_login"
}
```

## 6. 重点失败场景

### 6.1 未携带 accessToken

- HTTP：返回 token 鉴权失败
- WebSocket：直接关闭，原因通常是 `unauthorized`

### 6.2 普通终端无 Docker

- `GET /terminal/available` 返回业务错误
- `WS /terminal/ws` 无法建立普通终端
- `WS /terminal/admin/ws` 仍可以测试管理员模式

### 6.3 Linux 用户密码错误

普通终端切管理员和管理员直连都会返回：

```json
{
  "type": "admin_login_result",
  "success": false,
  "mode": "normal",
  "msg": "Linux 用户名或密码错误"
}
```

管理员直连在认证成功前，`mode` 也会保持 `normal`。

### 6.4 管理员认证失败次数过多

默认上限由环境变量控制：

```text
NDLM_TERMINAL_ADMIN_MAX_FAILED_ATTEMPTS=5
```

达到上限后再发 `admin_login`，返回：

```json
{
  "type": "admin_login_result",
  "success": false,
  "mode": "normal",
  "msg": "管理员认证失败次数过多，请重新创建终端"
}
```
