---
title: 默认模块
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
code_clipboard: true
highlight_theme: darkula
headingLevel: 2
generator: "@tarslib/widdershins v4.0.30"

---

# 默认模块

Base URLs:

# Authentication

# 用户

## POST 登录

POST /user/login

用户登录接口，免鉴权。请求体中的 account 支持用户名或邮箱，hashedPassword 为前端提交的密码字符串。登录成功后服务端会同时写入 HttpOnly Cookie：accessToken（5 分钟）与 refreshToken（7 天），并在响应体 data 中返回 token 对。常见失败场景包括账号不存在、密码错误或数据库异常。

> Body 请求参数

```json
{
    "account": "admin",
    "hashedPassword": "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» account|body|string| 是 |用户名 或 邮箱（二合一字段）|
|» hashedPassword|body|string| 是 |哈西后密码|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImV4cCI6MTc3NjI1ODIyNH0.JZERii_XC3lPPG_pHDT9B-BAaH21Q6PaDlGFtzVyYMY",
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImV4cCI6MTc3Njg2MTIyNH0.SJnzixLCUbsR-A31CLLamL12eF-O3tJ_093P_jtPvJk"
    }
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImV4cCI6MTc3NjI2MDI2MX0.Nz7Z8GUmz3Wh_8IYSceb0D-TNnvIc3D24Rqq7pDQSq4",
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImV4cCI6MTc3Njg2MzI2MX0.4OuhEBlREmB73o5n5jT_e4-Ls-ckRdKXE_wGP1AJxzM"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» accessToken|string|true|none||none|
|»» refreshToken|string|true|none||none|

## DELETE 登出

DELETE /user/logout

用户登出接口。请求时会从 Cookie 中读取 refreshToken，并要求当前请求已通过 accessToken 鉴权。服务端会删除 refreshToken 对应的持久化记录，同时清理 accessToken 和 refreshToken 两个 Cookie。若 refreshToken 缺失、无效或已失效，会返回对应业务错误。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|null|true|none||none|

## POST 刷新访问令牌

POST /user/refresh

刷新 accessToken，接口本身免 accessToken 鉴权，但必须携带有效的 refreshToken Cookie。服务端会校验 refreshToken 对应用户及有效期，成功后生成新的 accessToken，并重新写入 accessToken / refreshToken Cookie；响应体 data 中也会返回新的 token 对。若 refreshToken 无效、过期或已被注销，会返回 401 相关错误。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImV4cCI6MTc3NjI1OTQ2OX0.P2s6PY2oG4exihuZJrFUT_BAYlDaPal1KuRR_fsYysU",
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImV4cCI6MTc3Njg2MzI2MX0.4OuhEBlREmB73o5n5jT_e4-Ls-ckRdKXE_wGP1AJxzM"
    }
}
```

> 401 Response

```json
{
    "code": 40104,
    "msg": "token无效",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» accessToken|string|true|none||none|
|»» refreshToken|string|true|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|null|true|none||none|

# 系统信息

## GET 系统健康 SSE

GET /system/health

SSE 实时推送系统健康状态。接口返回 `text/event-stream`，每约 2 秒推送一次，单条事件内容为 `data: <json>\n\n`。无需请求体；建立连接后服务端会持续输出当前主机的 `hostname`、`cpuUsage`、`memoryUsage`、`diskUsage`、`healthScore`、`status`，以及 `cpuInfo`、`memoryInfo`、`gpuInfos`、`diskInfos`、`networkInfos` 等详细结构。该接口已在全局中间件中豁免常规日志记录，客户端断开连接后服务端会自动停止推送。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|

> 返回示例

> 200 Response

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 查询告警列表

POST /system/alerts/all

分页查询系统告警事件。请求体继承 `PageSearchRequest`，需要提供 `page`、`pageSize`，并可通过 `excludeProcessed` 控制是否排除已处理告警。响应 `data` 为 `{ total, items }`，每条告警包含 `id`、`level`、`message`、`status`、`createTime`。其中 `status` 取值为 `0=未读`、`1=未处理`、`2=已处理`。

> Body 请求参数

```json
{
    "page": 0,
    "pageSize": 0,
    "excludeProcessed": true
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» page|body|integer| 是 |页码|
|» pageSize|body|integer| 是 |每页数量|
|» excludeProcessed|body|boolean| 是 |是否排除已处理的告警|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 3,
        "items": [
            {
                "level": 1,
                "message": "CPU使用率超过80%，请检查",
                "status": 0,
                "id": 1,
                "createTime": "2026-04-15T11:34:59"
            },
            {
                "level": 2,
                "message": "数据库连接失败",
                "status": 1,
                "id": 2,
                "createTime": "2026-04-15T11:39:59"
            },
            {
                "level": 0,
                "message": "系统重启完成",
                "status": 2,
                "id": 3,
                "createTime": "2026-04-15T11:29:59"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» items|[object]|true|none||none|
|»»» level|integer|true|none||none|
|»»» message|string|true|none||none|
|»»» status|integer|true|none||none|
|»»» id|integer|true|none||none|
|»»» createTime|string|true|none||none|

## PUT 标记告警已读

PUT /system/alerts/{id}/read

将指定告警标记为已读。通过路径参数 `id` 指定告警记录，成功后返回更新后的 `AlertEvent`。如果 `id` 不存在，服务端会返回业务错误。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|id|path|integer| 是 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "level": 1,
        "message": "CPU使用率超过80%，请检查",
        "createTime": "2026-04-15T11:34:59",
        "id": 1,
        "status": 1
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» level|integer|true|none||none|
|»» message|string|true|none||none|
|»» createTime|string|true|none||none|
|»» id|integer|true|none||none|
|»» status|integer|true|none||none|

## PUT 标记告警已处理

PUT /system/alerts/{id}/process

将指定告警标记为已处理。通过路径参数 `id` 指定告警记录，成功后返回更新后的 `AlertEvent`。如果 `id` 不存在，服务端会返回业务错误。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|id|path|integer| 是 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "level": 2,
        "message": "数据库连接失败",
        "createTime": "2026-04-15T11:39:59",
        "id": 2,
        "status": 2
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» level|integer|true|none||none|
|»» message|string|true|none||none|
|»» createTime|string|true|none||none|
|»» id|integer|true|none||none|
|»» status|integer|true|none||none|

## GET Agent 状态查询

GET /agents/status

获取所有 Agent 的最新状态。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|

> 返回示例

> 200 Response

```json
{
  "total": 0,
  "list": [
    {
      "id": 0,
      "agentId": 0,
      "currentTask": "string",
      "status": 2,
      "createTime": "2019-08-24T14:15:22Z"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» total|integer|false|none||总记录数|
|» list|[object]|false|none||none|
|»» id|integer|false|none||主键ID|
|»» agentId|integer|false|none||Agent ID|
|»» currentTask|string|false|none||正在执行的任务名称|
|»» status|integer|false|none||状态: 0离线 1在线 2忙碌|
|»» createTime|string(date-time)|false|none||上报时间|

# 文件管理

## POST 查询目录内容

POST /file/list

分页查询指定路径下的直接子项列表。请求体包含 `path`、`page`、`pageSize`；当 `page=0` 且 `pageSize=0` 时，服务端会返回该目录下全部条目，否则按页切片返回。单条数据为 `FileItem`，包含名称、绝对路径、类型、大小、修改时间、所有者、用户组和权限。若目录不存在、不可访问或不是合法路径，会返回相应业务错误。

> Body 请求参数

```json
{
    "path": "/etc/",
    "page": 2,
    "pageSize": 10
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |目标路径|
|» page|body|integer| 否 |页码，默认1，如果page和pageSize都为0表示获取全部|
|» pageSize|body|integer| 否 |每页数量，默认20，如果page和pageSize都为0表示获取全部|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 239,
        "items": [
            {
                "name": "avahi",
                "path": "/etc/avahi",
                "type": 1,
                "size": 4096,
                "createdTime": "2026-03-12T13:53:00.774738",
                "modifiedTime": "2026-03-12T13:53:00.774738",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "bash_completion.d",
                "path": "/etc/bash_completion.d",
                "type": 1,
                "size": 4096,
                "createdTime": "2026-03-12T13:52:57.693588",
                "modifiedTime": "2026-03-12T13:52:57.693588",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "binfmt.d",
                "path": "/etc/binfmt.d",
                "type": 1,
                "size": 4096,
                "createdTime": "2022-04-08T03:28:15",
                "modifiedTime": "2022-04-08T03:28:15",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "bluetooth",
                "path": "/etc/bluetooth",
                "type": 1,
                "size": 4096,
                "createdTime": "2025-12-12T23:54:59.533369",
                "modifiedTime": "2025-12-12T23:54:59.533369",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "brltty",
                "path": "/etc/brltty",
                "type": 1,
                "size": 4096,
                "createdTime": "2024-09-11T22:20:50",
                "modifiedTime": "2024-09-11T22:20:50",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "ca-certificates",
                "path": "/etc/ca-certificates",
                "type": 1,
                "size": 4096,
                "createdTime": "2024-09-11T22:18:54",
                "modifiedTime": "2024-09-11T22:18:54",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "chatscripts",
                "path": "/etc/chatscripts",
                "type": 1,
                "size": 4096,
                "createdTime": "2024-09-11T22:21:02",
                "modifiedTime": "2024-09-11T22:21:02",
                "owner": "测试阶段",
                "permissions": "rwxr-x---"
            },
            {
                "name": "console-setup",
                "path": "/etc/console-setup",
                "type": 1,
                "size": 4096,
                "createdTime": "2025-12-13T07:40:05.404462",
                "modifiedTime": "2025-12-13T07:40:05.404462",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "cracklib",
                "path": "/etc/cracklib",
                "type": 1,
                "size": 4096,
                "createdTime": "2024-09-11T22:21:11",
                "modifiedTime": "2024-09-11T22:21:11",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            },
            {
                "name": "cron.d",
                "path": "/etc/cron.d",
                "type": 1,
                "size": 4096,
                "createdTime": "2025-12-13T07:41:23.412468",
                "modifiedTime": "2025-12-13T07:41:23.412468",
                "owner": "测试阶段",
                "permissions": "rwxr-xr-x"
            }
        ],
        "page": 2
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» items|[object]|true|none||none|
|»»» name|string|true|none||none|
|»»» path|string|true|none||none|
|»»» type|integer|true|none||none|
|»»» size|integer|true|none||none|
|»»» createdTime|string|true|none||none|
|»»» modifiedTime|string|true|none||none|
|»»» owner|string|true|none||none|
|»»» permissions|string|true|none||none|
|»» page|integer|true|none||none|

## POST 获取目录树

POST /file/tree

按指定深度获取目录树。请求体包含 `rootPath` 和 `depth`，其中 `depth >= 1`。服务端会校验根路径存在且必须是目录，然后返回递归的目录树结构；若目标路径不是目录、路径不存在或权限不足，会返回相应业务错误。

> Body 请求参数

```json
{
  "rootPath": "string",
  "depth": 1
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» rootPath|body|string| 是 |根路径|
|» depth|body|integer| 否 |递归深度|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "rootPath": "/home",
        "maxDepth": 2,
        "tree": {
            "fileName": "home",
            "fileType": "directory",
            "absolutePath": "/home",
            "children": [
                {
                    "fileName": "hxz",
                    "fileType": "directory",
                    "absolutePath": "/home/hxz",
                    "children": []
                },
                {
                    "fileName": "hzz",
                    "fileType": "directory",
                    "absolutePath": "/home/hzz",
                    "children": [
                        {
                            "fileName": ".ai_completion",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.ai_completion",
                            "children": []
                        },
                        {
                            "fileName": ".cache",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.cache",
                            "children": []
                        },
                        {
                            "fileName": ".config",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.config",
                            "children": []
                        },
                        {
                            "fileName": ".java",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.java",
                            "children": []
                        },
                        {
                            "fileName": ".local",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.local",
                            "children": []
                        },
                        {
                            "fileName": ".npm",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.npm",
                            "children": []
                        },
                        {
                            "fileName": ".nvm",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.nvm",
                            "children": []
                        },
                        {
                            "fileName": ".pki",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.pki",
                            "children": []
                        },
                        {
                            "fileName": ".ssh",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.ssh",
                            "children": []
                        },
                        {
                            "fileName": ".trae-cn",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.trae-cn",
                            "children": []
                        },
                        {
                            "fileName": ".trae-cn-server",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/.trae-cn-server",
                            "children": []
                        },
                        {
                            "fileName": "clionProject",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/clionProject",
                            "children": []
                        },
                        {
                            "fileName": "pycharm",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/pycharm",
                            "children": []
                        },
                        {
                            "fileName": "PycharmProjects",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/PycharmProjects",
                            "children": []
                        },
                        {
                            "fileName": "WebstormProjects",
                            "fileType": "directory",
                            "absolutePath": "/home/hzz/WebstormProjects",
                            "children": []
                        }
                    ]
                },
                {
                    "fileName": "raix",
                    "fileType": "directory",
                    "absolutePath": "/home/raix",
                    "children": []
                },
                {
                    "fileName": "tzj",
                    "fileType": "directory",
                    "absolutePath": "/home/tzj",
                    "children": []
                },
                {
                    "fileName": "www",
                    "fileType": "directory",
                    "absolutePath": "/home/www",
                    "children": []
                }
            ]
        },
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» name|string|false|none||文件夹名称|
|» path|string|false|none||文件夹路径|
|» children|[[#](#schema#)]|false|none||子文件夹列表|

## POST 上传文件

POST /file/upload

上传文件到指定目录。该接口使用 `multipart/form-data`，表单字段包括 `destinationPath` 和文件字段 `file`。服务端会先确保目标目录存在或尝试创建，再将上传内容按 1MB 分块写入磁盘。成功时返回保存后的绝对路径；若未提供文件、目录不可写或写盘失败，会返回业务错误。

> Body 请求参数

```yaml
destinationPath: ""
file: ""

```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» destinationPath|body|string| 是 |none|
|» file|body|string(binary)| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 下载文件

GET /file/download/{filePath}

下载指定文件。通过路径参数 `filePath` 指定实际文件路径，服务端会校验该路径存在且必须是文件，然后以 `application/octet-stream` 直接返回文件流。若目标不存在或不是文件，会返回业务错误而不是文件流。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|filePath|path|string| 是 |none|

> 返回示例

> 200 Response

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 删除路径

DELETE /file

删除单个文件或目录。请求体包含 `path`，服务端会先判断目标是文件还是目录，再分别执行删除逻辑；目录删除使用强制删除。若路径不存在、权限不足或目标类型异常，会返回对应业务错误。成功时返回统一成功响应，`data` 通常为空。

> Body 请求参数

```json
{
  "path": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": null
}
```

```json
{
    "code": 0,
    "msg": "路径不存在或不合法: /home/he/test",
    "data": null
}
```

```json
{
    "code": 0,
    "msg": "路径不存在或不合法: lalalw",
    "data": null
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|null|true|none||none|

## POST 创建文件

POST /file

创建一个新的空文件。请求体仅包含 `path`，必须是目标文件的完整路径。若目标已存在、父路径不可写或路径不合法，会返回业务错误；成功时返回底层文件操作结果。

> Body 请求参数

```json
{
    "path": "/tmp/test1.txt"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "absolutePath": "/tmp/test1.txt",
        "errorMessage": null
    }
}
```

```json
{
    "code": 0,
    "msg": "文件已存在: /tmp/test1.txt",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## PUT 重命名或移动路径

PUT /file

重命名文件/目录，或将其移动到新位置。请求体包含 `sourcePath` 和 `destinationPath`。服务端要求源路径存在、目标路径不能已存在；成功时返回文件操作结果，失败时会区分源不存在、目标已存在、权限不足和底层执行失败等场景。

> Body 请求参数

```json
{
  "sourcePath": "string",
  "destinationPath": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» sourcePath|body|string| 是 |none|
|» destinationPath|body|string| 是 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "absolutePath": "/tmp/file2.txt",
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 批量删除路径

DELETE /file/batch

批量删除多个文件或目录。请求体中的 `paths` 为待删除路径数组，服务端会逐项执行并收集结果，不会因为单条失败而中断整个批次。响应 `data` 为 `{ total, items }`，其中每条 item 都会标记 success 或失败原因，适合前端逐条展示删除结果。

> Body 请求参数

```json
{
  "paths": [
    "string"
  ]
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» paths|body|[string]| 是 |none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 4,
        "items": [
            {
                "success": true,
                "absolutePath": "/tmp/mock_data/file1.txt",
                "errorMessage": null
            },
            {
                "success": true,
                "absolutePath": "/tmp/mock_data/file2.log",
                "errorMessage": null
            },
            {
                "success": true,
                "absolutePath": "/tmp/mock_data/folder1/file3.txt",
                "errorMessage": null
            },
            {
                "success": true,
                "absolutePath": "/tmp/mock_data/folder2/subfolder1/file4.txt",
                "errorMessage": null
            }
        ]
    }
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 8,
        "items": [
            {
                "success": false,
                "absolutePath": "/tmp/mock_data",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data"
            },
            {
                "success": false,
                "absolutePath": "/tmp/mock_data/file1.txt",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data/file1.txt"
            },
            {
                "success": false,
                "absolutePath": "/tmp/mock_data/file2.log",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data/file2.log"
            },
            {
                "success": false,
                "absolutePath": "/tmp/mock_data/folder1",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data/folder1"
            },
            {
                "success": false,
                "absolutePath": "/tmp/mock_data/folder1/file3.txt",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data/folder1/file3.txt"
            },
            {
                "success": false,
                "absolutePath": "/tmp/mock_data/folder2",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data/folder2"
            },
            {
                "success": false,
                "absolutePath": "/tmp/mock_data/folder2/subfolder1",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data/folder2/subfolder1"
            },
            {
                "success": false,
                "absolutePath": "/tmp/mock_data/folder2/subfolder1/file4.txt",
                "errorMessage": "路径不存在或不合法: /tmp/mock_data/folder2/subfolder1/file4.txt"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» items|[object]|true|none||none|
|»»» success|boolean|true|none||none|
|»»» absolutePath|string|true|none||none|
|»»» errorMessage|null|true|none||none|

## PUT 修改路径权限

PUT /file/permissions

修改文件或目录权限。请求体包含 `path` 和 `permissions`，权限值通常使用 Unix 风格权限字符串。服务端会校验目标存在后调用底层权限修改工具；若路径不存在、权限不足或参数非法，会返回业务错误。

> Body 请求参数

```json
{
    "path": "/tmp/testfile1.txt",
    "permissions": "644"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |文件路径|
|» permissions|body|string| 是 |新权限值|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "newPermissions": "644",
        "errorMessage": null
    }
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "newPermissions": "755",
        "errorMessage": null
    }
}
```

```json
{
    "code": 0,
    "msg": "路径不存在或不合法: /tmp/nonexistentfile.txt",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 获取路径详情（历史资源）

GET /file/info/{path}

历史遗留资源，语义与 `/file/info/{filePath}` 一致，均用于获取文件或目录的元信息。当前后端代码实际使用的路径参数名为 `filePath`；此资源保留用于兼容旧文档阅读，新增调用建议优先参考 `/file/info/{filePath}`。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|path|path|string| 是 |none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "name": "hzz",
        "path": "/home/hzz",
        "type": 1,
        "size": 4096,
        "createdTime": "2026-04-22T14:42:08.521385",
        "modifiedTime": "2026-04-22T14:42:08.521385",
        "owner": "hzz",
        "group": "hzz",
        "permissions": "rwxr-x---"
    }
}
```

```json
{
    "code": 0,
    "msg": "路径不存在: /1",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» path|string|false|none||none|
|» permissions|string|false|none||none|
|» owner|string|false|none||none|
|» group|string|false|none||none|

## POST 搜索文件

POST /file/search

在指定目录下按表达式搜索文件。请求体包含 `path`、`expression`、`recursive`、`ignoreCase`、`invertMatch`。当前实现会按文件名维度搜索并返回匹配到的 `FileItem` 列表，而不是返回文件内容片段。若搜索起点不存在、不是目录或底层工具执行失败，会返回业务错误。

> Body 请求参数

```json
{
  "path": "string",
  "recursive": true,
  "expression": "string",
  "ignoreCase": true,
  "invertMatch": true
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |搜索起始路径|
|» recursive|body|boolean| 是 |默认false|
|» expression|body|string| 是 |搜索正则|
|» ignoreCase|body|boolean| 是 |是否忽略大小写|
|» invertMatch|body|boolean| 是 |是否反向查找|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 1,
        "items": [
            {
                "name": "hzz",
                "path": "/home/hzz",
                "type": 1,
                "size": 4096,
                "createdTime": "2026-04-22T14:42:08.521385",
                "modifiedTime": "2026-04-22T14:42:08.521385",
                "owner": "hzz",
                "group": "hzz",
                "permissions": "rwxr-x---"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» total|integer|false|none||文件总数|
|» fileList|[object]|false|none||文件列表|
|»» name|string|false|none||文件名|
|»» path|string|false|none||文件路径|
|»» type|integer|false|none||文件类型: 0=文件夹, 1=文本文件, 2=二进制文件|
|»» size|integer|false|none||文件大小|
|»» createdTime|string(date-time)|false|none||创建时间|
|»» modifiedTime|string(date-time)|false|none||修改时间|
|»» owner|string|false|none||所有者|
|»» permissions|string|false|none||权限标识|

#### 枚举值

|属性|值|
|---|---|
|type|0|
|type|1|
|type|2|

## POST 创建目录

POST /file/dir

创建目录。请求体包含目标 `path`，如果目录已存在会直接报错。成功时返回底层文件操作结果；若父目录无权限或路径不合法，会返回业务错误。

> Body 请求参数

```json
{
  "path": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "absolutePath": "/tmp/test-folder",
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 复制文件

POST /file/copy

复制单个文件。请求体包含 `sourcePath` 和 `destinationPath`，源路径必须存在且必须是文件。成功时返回文件操作结果；若源路径不是文件、目标不可写或权限不足，会返回业务错误。

> Body 请求参数

```json
{
  "sourcePath": "string",
  "destinationPath": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» sourcePath|body|string| 是 |none|
|» destinationPath|body|string| 是 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "absolutePath": "/tmp/test/3/2/1.md",
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 压缩路径

POST /file/zip

将指定文件或目录压缩为压缩包。请求体包含 `path`，目标路径必须存在。成功时返回压缩结果；若路径不存在、权限不足或底层压缩失败，会返回业务错误。

> Body 请求参数

```json
{
  "path": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "sourcePath": "/tmp/test",
        "archivePath": "/tmp/test.tar.gz",
        "archiveSizeBytes": 3487,
        "errorMessage": null
    }
}
```

```json
{
    "code": 0,
    "msg": "路径不存在: /temp/test",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 读取文本文件

GET /file/read/{path}

读取文本文件内容。通过路径参数 `path` 指定目标文件，服务端会校验目标存在且必须是文件，并额外检查它是否为文本文件。当前后端限制文件大小不能超过 10MB，超过即返回错误，不支持在线读取；对于二进制文件也会直接报错。成功时响应 `data` 为文本读取结果，适合网页编辑器或预览场景。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|path|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "targetPath": "/tmp/test1/test/3/1.md",
        "content": "test",
        "encoding": "utf-8",
        "sizeBytes": 4,
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 写入文本文件

POST /file/write

覆盖写入文本文件内容。请求体包含 `path` 和 `content`，目标路径必须已存在且必须是文件。成功时返回文本写入结果；若路径不存在、不是文件或权限不足，会返回业务错误。

> Body 请求参数

```json
{
  "path": "string",
  "context": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |none|
|» context|body|string| 是 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "targetPath": "/tmp/test1/test/3/1.md",
        "sizeBytes": 4,
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 解压压缩包

POST /file/unzip

解压压缩文件。请求体包含 `zipFilePath` 和 `dstPath`；`zipFilePath` 必须存在，`dstPath` 不能指向文件。成功时返回解压结果；若压缩包不存在、目标路径非法、权限不足或底层解压失败，会返回业务错误。

> Body 请求参数

```json
{
  "zipFilePath": "string",
  "dstPath": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» zipFilePath|body|string| 是 |none|
|» dstPath|body|string| 否 |默认当前目录|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "archivePath": "/tmp/test.tar.gz",
        "targetPath": "/tmp/test1",
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## PUT 修改文件所有者

PUT /file/owner

修改文件或目录的 owner/group。请求体包含 `targetPath`、`owner`、`group`、`recursive`。服务端会校验目标存在后执行所有者变更；若路径不存在、权限不足或底层命令执行失败，会返回业务错误。

> Body 请求参数

```json
{
    "targetPath": "/tmp/test1/test/3/1.md",
    "owner": "hxz",
    "group": "hxz",
    "recursive": true
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» targetPath|body|string| 是 |none|
|» owner|body|string| 是 |none|
|» group|body|string| 是 |none|
|» recursive|body|boolean| 否 |none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "newOwner": "hzz",
        "newGroup": "hzz",
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

<a id="opIdgetFileInfo_file_info__filePath__get"></a>

## GET 获取路径详情

GET /file/info/{filePath}

获取文件或目录的元信息。通过路径参数 `filePath` 指定目标路径，成功后返回 `FileItem`，包含名称、绝对路径、类型、大小、时间、所有者、用户组和权限信息。若路径不存在或无权访问，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|filePath|path|string| 是 | Filepath|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

# 防火墙

## GET 查询安全开关状态

GET /firewall/switch

查询当前防火墙与 SSH 服务的整体开关状态。响应 `data` 为 `SecuritySwitchState`，包含 `firewallEnabled` 和 `sshServiceEnabled` 两个布尔字段。防火墙状态通过特权代理读取，SSH 服务状态会优先检查 `sshd`，失败时回退检查 `ssh`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "firewallEnabled": false,
        "sshServiceEnabled": true
    }
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "firewallEnabled": false,
        "sshServiceEnabled": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» firewallEnabled|boolean|true|none||none|
|»» sshServiceEnabled|boolean|true|none||none|

## PUT 更新安全开关状态

PUT /firewall/switch

更新防火墙或 SSH 服务的启停状态。请求体可单独提供 `firewallEnabled`、`sshServiceEnabled` 中的任意一个字段，未提供的字段保持现状。服务端会调用特权代理执行启停操作，成功后返回最新的 `SecuritySwitchState`。如果权限不足或服务状态修改失败，会返回业务错误。

> Body 请求参数

```json
{"sshServiceEnabled": true}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» firewallEnabled|body|boolean| 否 ||防火墙是否开启|
|» sshServiceEnabled|body|boolean| 否 ||SSH服务是否开启|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "firewallEnabled": false,
        "sshServiceEnabled": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» firewallEnabled|boolean|true|none||none|
|»» sshServiceEnabled|boolean|true|none||none|

## GET 查询端口规则列表

GET /firewall/port-rules

查询当前防火墙端口规则列表。响应 `data` 为 `{ total, list }`，其中每条规则包含端口、协议、IP 版本、来源/目标 IP、优先级、动作以及时间戳。该接口适合配合端口规则管理页直接展示。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 4,
        "list": [
            {
                "port": 22,
                "protocol": 1,
                "ipVersion": 4,
                "sourceIp": "0.0.0.0/0",
                "destinationIp": "0.0.0.0/0",
                "priority": 100,
                "action": 1,
                "id": 1,
                "createdTime": "2026-06-03T15:53:26.101963",
                "updatedTime": "2026-06-03T15:53:26.101963"
            },
            {
                "port": 8088,
                "protocol": 1,
                "ipVersion": 4,
                "sourceIp": "0.0.0.0/0",
                "destinationIp": "0.0.0.0/0",
                "priority": 100,
                "action": 1,
                "id": 2,
                "createdTime": "2026-06-03T15:53:26.101963",
                "updatedTime": "2026-06-03T15:53:26.101963"
            },
            {
                "port": 22,
                "protocol": 1,
                "ipVersion": 6,
                "sourceIp": "::/0",
                "destinationIp": "::/0",
                "priority": 100,
                "action": 1,
                "id": 3,
                "createdTime": "2026-06-03T15:53:26.101963",
                "updatedTime": "2026-06-03T15:53:26.101963"
            },
            {
                "port": 8088,
                "protocol": 1,
                "ipVersion": 6,
                "sourceIp": "::/0",
                "destinationIp": "::/0",
                "priority": 100,
                "action": 1,
                "id": 4,
                "createdTime": "2026-06-03T15:53:26.101963",
                "updatedTime": "2026-06-03T15:53:26.101963"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» list|[object]|true|none||none|
|»»» port|integer|false|none||none|
|»»» protocol|integer|false|none||none|
|»»» sourceIp|string|false|none||none|
|»»» destinationIp|string|false|none||none|
|»»» priority|integer|false|none||none|
|»»» action|integer|false|none||none|
|»»» id|integer|false|none||none|
|»»» createdTime|string|false|none||none|
|»»» updatedTime|string|false|none||none|

## POST 创建端口规则

POST /firewall/port-rules

新增一条防火墙端口规则。请求体包含 `port`、`protocol`、`ipVersion`、`sourceIp`、`destinationIp`、`priority`、`action`。当前后端实现仅支持 `action=1` 的允许规则，不支持新增拒绝规则；创建成功后响应会返回最新的端口规则总数和完整列表。若权限不足或规则参数不被当前实现支持，会返回业务错误。

> Body 请求参数

```json
{
  "port": 22,
  "protocol": 1,
  "ipVersion": 4,
  "sourceIp": "0.0.0.0/0",
  "destinationIp": "0.0.0.0/0",
  "priority": 100,
  "action": 1
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» port|body|integer| 是 ||端口号|
|» ipVersion|body|integer| 是 ||4或者6|
|» protocol|body|integer| 是 ||协议类型：0=UDP, 1=TCP|
|» sourceIp|body|string| 是 ||来源IP，支持CIDR|
|» destinationIp|body|string| 是 ||目标IP，支持CIDR|
|» priority|body|integer| 否 ||规则优先级，默认100|
|» action|body|integer| 是 ||动作：0=拒绝, 1=允许|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 4,
        "list": [
            {
                "port": 22,
                "protocol": 1,
                "ipVersion": 4,
                "sourceIp": "0.0.0.0/0",
                "destinationIp": "0.0.0.0/0",
                "priority": 100,
                "action": 1,
                "id": 1,
                "createdTime": "2026-06-03T15:56:40.520412",
                "updatedTime": "2026-06-03T15:56:40.520412"
            },
            {
                "port": 8088,
                "protocol": 1,
                "ipVersion": 4,
                "sourceIp": "0.0.0.0/0",
                "destinationIp": "0.0.0.0/0",
                "priority": 100,
                "action": 1,
                "id": 2,
                "createdTime": "2026-06-03T15:56:40.520412",
                "updatedTime": "2026-06-03T15:56:40.520412"
            },
            {
                "port": 22,
                "protocol": 1,
                "ipVersion": 6,
                "sourceIp": "::/0",
                "destinationIp": "::/0",
                "priority": 100,
                "action": 1,
                "id": 3,
                "createdTime": "2026-06-03T15:56:40.520412",
                "updatedTime": "2026-06-03T15:56:40.520412"
            },
            {
                "port": 8088,
                "protocol": 1,
                "ipVersion": 6,
                "sourceIp": "::/0",
                "destinationIp": "::/0",
                "priority": 100,
                "action": 1,
                "id": 4,
                "createdTime": "2026-06-03T15:56:40.520412",
                "updatedTime": "2026-06-03T15:56:40.520412"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» total|integer|false|none||列表总数|
|» list|[object]|false|none||规则列表|
|»» id|integer|false|none||ID|
|»» port|integer|false|none||端口号|
|»» protocol|integer|false|none||协议类型：0=UDP, 1=TCP|
|»» sourceIp|string|false|none||来源IP，支持CIDR|
|»» destinationIp|string|false|none||目标IP，支持CIDR|
|»» priority|integer|false|none||规则优先级，默认100|
|»» action|integer|false|none||动作：0=拒绝, 1=允许|
|»» createdTime|string(date-time)|false|none||创建时间|
|»» updatedTime|string(date-time)|false|none||更新时间|

## DELETE 删除端口规则

DELETE /firewall/port-rules

删除符合条件的防火墙端口规则。请求体至少需要 `port` 和 `protocol`，也可带上 `ipVersion`、`sourceIp`、`destinationIp` 缩小删除范围。成功时响应 `data` 会返回 `{ deleted, total, list }`，其中 `deleted` 表示实际删除结果，`list` 为删除后的剩余规则列表。

> Body 请求参数

```json
 {
    "port": 8088,
    "protocol": 1,
    "sourceIp": "0.0.0.0/0",
    "destinationIp":"0.0.0.0/0",
    "ipVersion": 4
  }
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» port|body|integer| 是 ||none|
|» protocol|body|integer| 是 ||none|
|» sourceIp|body|string| 是 ||none|
|» destinationIp|body|null| 是 ||none|
|» ipVersion|body|integer| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "deleted": {
            "success": true,
            "port": 8088,
            "protocol": 1,
            "ipVersion": 4,
            "sourceIp": "0.0.0.0/0",
            "destinationIp": "0.0.0.0/0",
            "policy": "removed"
        },
        "total": 3,
        "list": [
            {
                "port": 22,
                "protocol": 1,
                "ipVersion": 4,
                "sourceIp": "0.0.0.0/0",
                "destinationIp": "0.0.0.0/0",
                "priority": 100,
                "action": 1,
                "id": 1,
                "createdTime": "2026-06-09T16:33:18.575217",
                "updatedTime": "2026-06-09T16:33:18.575217"
            },
            {
                "port": 22,
                "protocol": 1,
                "ipVersion": 6,
                "sourceIp": "::/0",
                "destinationIp": "::/0",
                "priority": 100,
                "action": 1,
                "id": 2,
                "createdTime": "2026-06-09T16:33:18.575217",
                "updatedTime": "2026-06-09T16:33:18.575217"
            },
            {
                "port": 8088,
                "protocol": 1,
                "ipVersion": 6,
                "sourceIp": "::/0",
                "destinationIp": "::/0",
                "priority": 100,
                "action": 1,
                "id": 3,
                "createdTime": "2026-06-09T16:33:18.575217",
                "updatedTime": "2026-06-09T16:33:18.575217"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» deleted|object|true|none||none|
|»»» success|boolean|true|none||none|
|»»» port|integer|true|none||none|
|»»» protocol|integer|true|none||none|
|»»» ipVersion|integer|true|none||none|
|»»» sourceIp|string|true|none||none|
|»»» destinationIp|string|true|none||none|
|»»» policy|string|true|none||none|
|»» total|integer|true|none||none|
|»» list|[object]|true|none||none|
|»»» port|integer|true|none||none|
|»»» protocol|integer|true|none||none|
|»»» ipVersion|integer|true|none||none|
|»»» sourceIp|string|true|none||none|
|»»» destinationIp|string|true|none||none|
|»»» priority|integer|true|none||none|
|»»» action|integer|true|none||none|
|»»» id|integer|true|none||none|
|»»» createdTime|string|true|none||none|
|»»» updatedTime|string|true|none||none|

## GET 获取 SSH 配置

GET /firewall/ssh/config

读取当前 SSH 服务配置。响应 `data` 为 `SshConfig`，包含端口、root 登录策略、密码登录开关、允许用户/用户组、监听地址、协议版本、登录宽限时间、最大认证次数，以及配置的创建/更新时间。服务端会优先解析 `/etc/ssh/sshd_config`，并跟随 `Include` 指令合并附加配置。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "port": 22,
        "permitRootLogin": "no",
        "passwordAuthentication": "yes",
        "allowUsers": [],
        "allowGroups": [],
        "listenAddress": [
            "0.0.0.0"
        ],
        "protocol": 2,
        "loginGraceTime": 120,
        "maxAuthTries": 8,
        "id": 1,
        "createdTime": "2026-04-20T21:43:02.119280",
        "updatedTime": "2026-04-20T21:43:02.119280"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» id|integer|false|none||配置项唯一标识|
|» port|integer|false|none||SSH监听端口|
|» permitRootLogin|string|false|none||root登录允许情况|
|» passwordAuthentication|string|false|none||是否允许密码登录|
|» allowUsers|[string]|false|none||允许登录的用户列表|
|» allowGroups|[string]|false|none||允许登录的用户组列表|
|» listenAddress|[string]|false|none||监听地址|
|» protocol|integer|false|none||SSH协议版本|
|» loginGraceTime|integer|false|none||登录宽限时间(秒)|
|» maxAuthTries|integer|false|none||最大认证尝试次数|
|» createdTime|string(date-time)|false|none||创建时间|
|» updatedTime|string(date-time)|false|none||更新时间|

## PUT 修改 SSH 配置

PUT /firewall/ssh/config

更新 SSH 服务配置。请求体支持按字段局部覆盖，例如 `port`、`permitRootLogin`、`passwordAuthentication`、`allowUsers`、`allowGroups`、`listenAddress`、`protocol`、`loginGraceTime`、`maxAuthTries`。服务端会基于当前配置生成托管配置块，写入后执行 `sshd -t` 语法检查；如果检查失败会自动回滚原配置。成功时返回更新后的完整 `SshConfig`。

> Body 请求参数

```json
{
  "permitRootLogin": "no",
  "passwordAuthentication": "no",
  "maxAuthTries": 3,
  "loginGraceTime": 60
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» port|body|integer| 否 ||The port number for SSH connections.|
|» permitRootLogin|body|string| 否 ||Specifies whether root login is allowed via SSH.|
|» passwordAuthentication|body|string| 否 ||Specifies whether password authentication is allowed for SSH.|
|» allowUsers|body|[string]| 否 ||A list of users allowed to connect via SSH.|
|» allowGroups|body|[string]| 否 ||A list of groups allowed to connect via SSH.|
|» listenAddress|body|[string]| 否 ||A list of addresses to listen for SSH connections.|
|» protocol|body|integer| 否 ||The SSH protocol version.|
|» loginGraceTime|body|integer| 否 ||Time allowed for login before disconnection.|
|» maxAuthTries|body|integer| 否 ||The maximum number of authentication attempts.|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "port": 22,
        "permitRootLogin": "no",
        "passwordAuthentication": "no",
        "allowUsers": [],
        "allowGroups": [],
        "listenAddress": [
            "0.0.0.0"
        ],
        "protocol": 2,
        "loginGraceTime": 60,
        "maxAuthTries": 3,
        "id": 1,
        "createdTime": "2026-04-23T23:15:13.473507",
        "updatedTime": "2026-04-23T23:15:13.473507"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» id|integer|false|none||配置项唯一标识|
|» port|integer|false|none||SSH监听端口|
|» permitRootLogin|string|false|none||root登录允许情况|
|» passwordAuthentication|string|false|none||是否允许密码登录|
|» allowUsers|[string]|false|none||允许登录的用户列表|
|» allowGroups|[string]|false|none||允许登录的用户组列表|
|» listenAddress|[string]|false|none||监听地址|
|» protocol|integer|false|none||SSH协议版本|
|» loginGraceTime|integer|false|none||登录宽限时间(秒)|
|» maxAuthTries|integer|false|none||最大认证尝试次数|
|» createdTime|string(date-time)|false|none||创建时间|
|» updatedTime|string(date-time)|false|none||更新时间|

## GET 查询 SSH 登录日志

GET /firewall/ssh/logs

查询 SSH 登录日志列表。响应 `data` 为 SSH 登录事件数组，每条记录通常包含 `timestamp`、`user`、`sourceIp`、`port`、`status`、`reason` 等字段，可用于排查成功/失败登录尝试与来源地址。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 0,
        "list": []
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» total|integer|false|none||列表总数|
|» list|[object]|false|none||规则列表|
|»» timestamp|string(date-time)|false|none||登录时间|
|»» user|string|false|none||登录用户名|
|»» sourceIp|string|false|none||来源IP|
|»» port|integer|false|none||登录端口|
|»» status|string|false|none||登录状态: SUCCESS / FAILURE|
|»» reason|string|false|none||失败原因|

# 设置/apikey

## POST 创建凭证

POST /config/apikey

新增上游模型 API 凭证配置，用于保存 OpenAI、Azure、Anthropic 或 Custom 提供商的访问凭证。请求体必须包含 apiKey，其他字段用于控制启用状态、备注、额度限制与自定义 baseUrl。创建成功后返回 credentialId 和 maskedKey，只返回脱敏后的 Key，不会回显完整 apiKey。

> Body 请求参数

```json
{
  "name": "string",
  "provider": "OpenAI",
  "baseUrl": "string",
  "isActive": true,
  "description": "string",
  "quotaLimit": 0,
  "apiKey": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» name|body|string| 否 ||凭证别名|
|» provider|body|string| 否 ||服务商类型|
|» baseUrl|body|string| 否 ||自定义请求地址|
|» isActive|body|boolean| 否 ||是否启用|
|» description|body|string| 否 ||备注说明|
|» quotaLimit|body|integer| 否 ||预算额度限制，0表示没有|
|» apiKey|body|string| 是 ||完整的API Key|

#### 枚举值

|属性|值|
|---|---|
|» provider|OpenAI|
|» provider|Azure|
|» provider|Anthropic|
|» provider|Custom|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "name": "apiKey1",
        "provider": "Custom",
        "baseUrl": "https://both-hello.com/",
        "isActive": true,
        "description": "六效西头我重地在步。快历取好见值龙圆造产。重器部机确周。点素事却者近。",
        "quotaLimit": 69.0,
        "credentialId": 17,
        "maskedKey": "sk-*********************************************312",
        "usedQuota": 0.0,
        "expireAt": null,
        "lastUsedAt": null,
        "createTime": "2026-04-19T16:07:36.562958",
        "updateTime": "2026-04-19T16:07:36.562965"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» name|string|true|none||none|
|»» provider|string|true|none||none|
|»» baseUrl|string|true|none||none|
|»» isActive|boolean|true|none||none|
|»» description|string|true|none||none|
|»» quotaLimit|integer|true|none||none|
|»» credentialId|integer|true|none||none|
|»» maskedKey|string|true|none||none|
|»» usedQuota|integer|true|none||none|
|»» expireAt|null|true|none||none|
|»» lastUsedAt|null|true|none||none|
|»» createTime|string|true|none||none|
|»» updateTime|string|true|none||none|

## GET 查询凭证列表

GET /config/apikey

查询当前系统保存的全部模型 API 凭证。响应 data 为 { total, items }，items 中包含 credentialId、provider、isActive、quotaLimit、usedQuota、maskedKey 等展示字段，但不返回原始 apiKey，适合设置页直接渲染列表。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 4,
        "items": [
            {
                "name": "言呈轩",
                "provider": "Custom",
                "baseUrl": "https://winged-tribe.net/",
                "isActive": false,
                "description": "石资角克。书算照比级证酸应。消在他始示能大记。个因边学局多难。内极任什上。原备始持行基。克会动整。什价运万精问地林行。",
                "quotaLimit": 69.0,
                "credentialId": 1,
                "maskedKey": "sk-*********************************************312",
                "usedQuota": 0.0,
                "expireAt": null,
                "lastUsedAt": null,
                "createTime": "2026-04-20T14:29:14.509514",
                "updateTime": "2026-04-20T14:48:31.639942"
            },
            {
                "name": "apiKey1",
                "provider": "Custom",
                "baseUrl": "https://both-hello.com/",
                "isActive": true,
                "description": "六效西头我重地在步。快历取好见值龙圆造产。重器部机确周。点素事却者近。",
                "quotaLimit": 69.0,
                "credentialId": 2,
                "maskedKey": "sk-*********************************************312",
                "usedQuota": 0.0,
                "expireAt": null,
                "lastUsedAt": null,
                "createTime": "2026-04-20T14:49:27.477739",
                "updateTime": "2026-04-20T14:49:27.477745"
            },
            {
                "name": "apiKey1",
                "provider": "Custom",
                "baseUrl": "https://both-hello.com/",
                "isActive": true,
                "description": "六效西头我重地在步。快历取好见值龙圆造产。重器部机确周。点素事却者近。",
                "quotaLimit": 69.0,
                "credentialId": 3,
                "maskedKey": "sk-*********************************************312",
                "usedQuota": 0.0,
                "expireAt": null,
                "lastUsedAt": null,
                "createTime": "2026-04-20T14:49:28.303467",
                "updateTime": "2026-04-20T14:49:28.303472"
            },
            {
                "name": "apiKey1",
                "provider": "Custom",
                "baseUrl": "https://both-hello.com/",
                "isActive": true,
                "description": "六效西头我重地在步。快历取好见值龙圆造产。重器部机确周。点素事却者近。",
                "quotaLimit": 69.0,
                "credentialId": 4,
                "maskedKey": "sk-*********************************************312",
                "usedQuota": 0.0,
                "expireAt": null,
                "lastUsedAt": null,
                "createTime": "2026-04-20T14:49:29.200166",
                "updateTime": "2026-04-20T14:49:29.200170"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» items|[object]|true|none||none|
|»»» name|string|true|none||none|
|»»» provider|string|true|none||none|
|»»» baseUrl|string|true|none||none|
|»»» isActive|boolean|true|none||none|
|»»» description|string|true|none||none|
|»»» quotaLimit|integer|true|none||none|
|»»» credentialId|integer|true|none||none|
|»»» maskedKey|string|true|none||none|
|»»» usedQuota|integer|true|none||none|
|»»» expireAt|null|true|none||none|
|»»» lastUsedAt|null|true|none||none|
|»»» createTime|string|true|none||none|
|»»» updateTime|string|true|none||none|

## PUT 更新凭证

PUT /config/apikey

更新已存在的模型 API 凭证。通过请求体中的 credentialId 指定目标记录，可修改名称、baseUrl、是否启用、备注与额度限制。更新成功后返回最新的脱敏凭证信息，不会回显完整 apiKey；若 credentialId 不存在，会返回业务错误。

> Body 请求参数

```json
{
  "name": "string",
  "provider": "OpenAI",
  "baseUrl": "string",
  "isActive": true,
  "description": "string",
  "quotaLimit": 0,
  "credentialId": 0
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» name|body|string| 否 ||凭证别名|
|» provider|body|string| 否 ||服务商类型|
|» baseUrl|body|string¦null| 否 ||自定义请求地址|
|» isActive|body|boolean| 否 ||是否启用|
|» description|body|string¦null| 否 ||备注说明|
|» quotaLimit|body|number¦null| 否 ||预算额度限制|
|» credentialId|body|integer| 是 ||none|

#### 枚举值

|属性|值|
|---|---|
|» provider|OpenAI|
|» provider|Azure|
|» provider|Anthropic|
|» provider|Custom|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "name": "言呈轩",
        "provider": "Custom",
        "baseUrl": "https://winged-tribe.net/",
        "isActive": false,
        "description": "石资角克。书算照比级证酸应。消在他始示能大记。个因边学局多难。内极任什上。原备始持行基。克会动整。什价运万精问地林行。",
        "quotaLimit": 69.0,
        "credentialId": 1,
        "maskedKey": "sk-*********************************************312",
        "usedQuota": 0.0,
        "expireAt": null,
        "lastUsedAt": null,
        "createTime": "2026-04-20T14:29:14.509514",
        "updateTime": "2026-04-20T14:35:48.023500"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» name|string|true|none||none|
|»» provider|string|true|none||none|
|»» baseUrl|string|true|none||none|
|»» isActive|boolean|true|none||none|
|»» description|string|true|none||none|
|»» quotaLimit|integer|true|none||none|
|»» credentialId|integer|true|none||none|
|»» maskedKey|string|true|none||none|
|»» usedQuota|integer|true|none||none|
|»» expireAt|null|true|none||none|
|»» lastUsedAt|null|true|none||none|
|»» createTime|string|true|none||none|
|»» updateTime|string|true|none||none|

## DELETE 删除凭证

DELETE /config/apikey/{credentialId}

删除指定的模型 API 凭证。通过路径参数 credentialId 指定目标记录，删除成功后返回 code=1、data=null。若目标凭证不存在，服务端会返回对应业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|credentialId|path|integer| 是 ||none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": null
}
```

```json
{
    "code": 0,
    "msg": "删除失败，不存在id为9999999999的apikey项",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|null|true|none||none|

# 设置/model

## GET 根据 Credential 拉取官方模型列表

GET /agent/llm/credentials/{credentialId}/models

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "credentialId": 1,
    "credentialName": "deepseek-key",
    "credentialProvider": "Custom",
    "credentialBaseUrl": "https://api.deepseek.com/anthropic",
    "sourceUrl": "https://api.deepseek.com/models",
    "models": [
      {
        "id": "deepseek-chat",
        "name": "deepseek-chat",
        "ownedBy": "deepseek",
        "raw": {
          "id": "deepseek-chat",
          "object": "model",
          "owned_by": "deepseek"
        }
      }
    ]
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|credentialId|path|integer| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "credentialId": 7,
        "credentialName": "my",
        "credentialProvider": "Custom",
        "credentialBaseUrl": "http://38.165.23.223:8317/v1",
        "sourceUrl": "http://38.165.23.223:8317/v1/models",
        "models": [
            {
                "id": "gemini-2.5-flash-lite",
                "name": "gemini-2.5-flash-lite",
                "ownedBy": "google",
                "raw": {
                    "created": 1753142400,
                    "id": "gemini-2.5-flash-lite",
                    "object": "model",
                    "owned_by": "google"
                }
            },
            {
                "id": "GPT-5.4",
                "name": "GPT-5.4",
                "ownedBy": "miao",
                "raw": {
                    "created": 1780934671,
                    "id": "GPT-5.4",
                    "object": "model",
                    "owned_by": "miao"
                }
            },
            {
                "id": "gpt-5.3-codex-spark",
                "name": "gpt-5.3-codex-spark",
                "ownedBy": "openai",
                "raw": {
                    "created": 1770912000,
                    "id": "gpt-5.3-codex-spark",
                    "object": "model",
                    "owned_by": "openai"
                }
            },
            {
                "id": "gpt-5.4-mini",
                "name": "gpt-5.4-mini",
                "ownedBy": "openai",
                "raw": {
                    "created": 1773705600,
                    "id": "gpt-5.4-mini",
                    "object": "model",
                    "owned_by": "openai"
                }
            },
            {
                "id": "gpt-5.5",
                "name": "gpt-5.5",
                "ownedBy": "openai",
                "raw": {
                    "created": 1776902400,
                    "id": "gpt-5.5",
                    "object": "model",
                    "owned_by": "openai"
                }
            },
            {
                "id": "gemini-2.5-flash",
                "name": "gemini-2.5-flash",
                "ownedBy": "google",
                "raw": {
                    "created": 1750118400,
                    "id": "gemini-2.5-flash",
                    "object": "model",
                    "owned_by": "google"
                }
            },
            {
                "id": "gemini-3-pro-preview",
                "name": "gemini-3-pro-preview",
                "ownedBy": "google",
                "raw": {
                    "created": 1737158400,
                    "id": "gemini-3-pro-preview",
                    "object": "model",
                    "owned_by": "google"
                }
            },
            {
                "id": "gpt-5.4",
                "name": "gpt-5.4",
                "ownedBy": "openai",
                "raw": {
                    "created": 1772668800,
                    "id": "gpt-5.4",
                    "object": "model",
                    "owned_by": "openai"
                }
            },
            {
                "id": "codex-auto-review",
                "name": "codex-auto-review",
                "ownedBy": "openai",
                "raw": {
                    "created": 1776902400,
                    "id": "codex-auto-review",
                    "object": "model",
                    "owned_by": "openai"
                }
            },
            {
                "id": "gemini-2.5-pro",
                "name": "gemini-2.5-pro",
                "ownedBy": "google",
                "raw": {
                    "created": 1750118400,
                    "id": "gemini-2.5-pro",
                    "object": "model",
                    "owned_by": "google"
                }
            },
            {
                "id": "gemini-3.1-pro-preview",
                "name": "gemini-3.1-pro-preview",
                "ownedBy": "google",
                "raw": {
                    "created": 1771459200,
                    "id": "gemini-3.1-pro-preview",
                    "object": "model",
                    "owned_by": "google"
                }
            },
            {
                "id": "gemini-3-flash-preview",
                "name": "gemini-3-flash-preview",
                "ownedBy": "google",
                "raw": {
                    "created": 1765929600,
                    "id": "gemini-3-flash-preview",
                    "object": "model",
                    "owned_by": "google"
                }
            },
            {
                "id": "gemini-3.1-flash-lite-preview",
                "name": "gemini-3.1-flash-lite-preview",
                "ownedBy": "google",
                "raw": {
                    "created": 1776288000,
                    "id": "gemini-3.1-flash-lite-preview",
                    "object": "model",
                    "owned_by": "google"
                }
            },
            {
                "id": "GPT-5.5",
                "name": "GPT-5.5",
                "ownedBy": "miao",
                "raw": {
                    "created": 1780934671,
                    "id": "GPT-5.5",
                    "object": "model",
                    "owned_by": "miao"
                }
            },
            {
                "id": "GPT-5.4 Mini",
                "name": "GPT-5.4 Mini",
                "ownedBy": "miao",
                "raw": {
                    "created": 1780934671,
                    "id": "GPT-5.4 Mini",
                    "object": "model",
                    "owned_by": "miao"
                }
            },
            {
                "id": "gpt-image-2",
                "name": "gpt-image-2",
                "ownedBy": "openai",
                "raw": {
                    "created": 1704067200,
                    "id": "gpt-image-2",
                    "object": "model",
                    "owned_by": "openai"
                }
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» credentialId|integer|true|none||none|
|»» credentialName|string|true|none||none|
|»» credentialProvider|string|true|none||none|
|»» credentialBaseUrl|string|true|none||none|
|»» sourceUrl|string|true|none||none|
|»» models|[object]|true|none||none|
|»»» id|string|true|none||none|
|»»» name|string|true|none||none|
|»»» ownedBy|string|true|none||none|
|»»» raw|object|true|none||none|
|»»»» created|integer|true|none||none|
|»»»» id|string|true|none||none|
|»»»» object|string|true|none||none|
|»»»» owned_by|string|true|none||none|

## POST 创建 LLM Profile

POST /agent/llm/profiles

请求体：

```json
{
  "name": "DeepSeek 默认",
  "credentialId": 1,
  "model": "deepseek-v4-pro",
  "maxTokens": 65536,
  "temperature": 0.1,
  "retryCount": 3,
  "retryDelay": 2.0,
  "isDefault": true,
  "isActive": true,
  "description": "比赛演示默认模型"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | Profile 名称 |
| credentialId | integer | 是 | 关联 `api_credentials.credentialId`，provider、endpoint、apiKey 均从该凭证读取 |
| model | string | 是 | 模型名称 |
| maxTokens | integer | 否 | 最大 token 数，默认 `4096` |
| temperature | number | 否 | 温度，默认 `0.1` |
| retryCount | integer | 否 | 重试次数，默认 `3` |
| retryDelay | number | 否 | 重试间隔，默认 `2.0` |
| isDefault | boolean | 否 | 是否默认 |
| isActive | boolean | 否 | 是否启用 |
| description | string | 否 | 描述 |

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "profileId": 1,
    "name": "DeepSeek 默认",
    "credentialId": 1,
    "credentialName": "deepseek-key",
    "credentialProvider": "Custom",
    "credentialBaseUrl": "https://api.deepseek.com/anthropic",
    "model": "deepseek-v4-pro",
    "maxTokens": 65536,
    "temperature": 0.1,
    "retryCount": 3,
    "retryDelay": 2.0,
    "isDefault": true,
    "isActive": true,
    "description": "比赛演示默认模型",
    "createTime": "2026-06-09T13:00:00",
    "updateTime": "2026-06-09T13:00:00"
  }
}
```

注意事项：

- 响应永远不会返回完整 API Key。
- `credentialId` 指向已有的 `/config/apikey` 凭证，Profile 自身不保存 `provider` 和 `endpoint`。
- Agent 实际请求时使用 credential 的 `baseUrl` 作为 endpoint，使用 credential 的 `apiKey` 作为密钥。
- `api_credentials.provider` 当前会映射为 Agent 的 `openai_compat` provider；如果 endpoint 包含 `/anthropic`，现有 LLM 工厂仍会自动使用 Anthropic 兼容请求格式。
- 如果 `isDefault=true`，其他 Profile 会被取消默认。
- 如果只想离线测试，不创建默认 Profile 或停用默认 Profile 时，Agent 会走现有配置 fallback；fallback 仍不可用时会进入 mock 兜底。

> Body 请求参数

```json
{
  "name": "DeepSeek 默认",
  "credentialId": 1,
  "model": "deepseek-v4-pro",
  "maxTokens": 65536,
  "temperature": 0.1,
  "retryCount": 3,
  "retryDelay": 2.0,
  "isDefault": true,
  "isActive": true,
  "description": "比赛演示默认模型"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» name|body|string| 是 ||none|
|» credentialId|body|integer| 是 ||none|
|» model|body|string| 是 ||none|
|» maxTokens|body|integer| 否 ||none|
|» temperature|body|number| 否 ||none|
|» retryCount|body|integer| 否 ||none|
|» retryDelay|body|integer| 否 ||none|
|» isDefault|body|boolean| 否 ||none|
|» isActive|body|boolean| 否 ||none|
|» description|body|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "name": "gpt",
        "credentialId": 7,
        "model": "gpt-5.4-mini",
        "maxTokens": 65536,
        "temperature": 0.1,
        "retryCount": 3,
        "retryDelay": 2.0,
        "isDefault": true,
        "isActive": true,
        "description": "比赛演示默认模型",
        "profileId": 2,
        "createTime": "2026-06-09T15:18:52.752333",
        "updateTime": "2026-06-09T15:18:52.752340",
        "credentialName": "my",
        "credentialProvider": "Custom",
        "credentialBaseUrl": "http://38.165.23.223:8317/v1"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询 LLM Profile 列表

GET /agent/llm/profiles

注意事项：

- 默认 Profile 会排在前面。
- 返回 `credentialName`、`credentialProvider`、`credentialBaseUrl`，不返回 `apiKey`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 3,
        "items": [
            {
                "name": "GPT-5.4",
                "credentialId": 7,
                "model": "GPT-5.4",
                "maxTokens": 65536,
                "temperature": 0.1,
                "retryCount": 3,
                "retryDelay": 2.0,
                "isDefault": true,
                "isActive": true,
                "description": "批量导入模型",
                "profileId": 3,
                "createTime": "2026-06-09T15:21:56.398820",
                "updateTime": "2026-06-09T15:21:56.398826",
                "credentialName": "my",
                "credentialProvider": "Custom",
                "credentialBaseUrl": "http://38.165.23.223:8317/v1"
            },
            {
                "name": "gpt-5.5",
                "credentialId": 7,
                "model": "gpt-5.5",
                "maxTokens": 65536,
                "temperature": 0.1,
                "retryCount": 3,
                "retryDelay": 2.0,
                "isDefault": false,
                "isActive": true,
                "description": "批量导入模型",
                "profileId": 4,
                "createTime": "2026-06-09T15:21:56.410885",
                "updateTime": "2026-06-09T15:21:56.410888",
                "credentialName": "my",
                "credentialProvider": "Custom",
                "credentialBaseUrl": "http://38.165.23.223:8317/v1"
            },
            {
                "name": "gpt",
                "credentialId": 7,
                "model": "gpt-5.4-mini",
                "maxTokens": 65536,
                "temperature": 0.1,
                "retryCount": 3,
                "retryDelay": 2.0,
                "isDefault": false,
                "isActive": true,
                "description": "比赛演示默认模型",
                "profileId": 2,
                "createTime": "2026-06-09T15:18:52.752333",
                "updateTime": "2026-06-09T15:21:56.397866",
                "credentialName": "my",
                "credentialProvider": "Custom",
                "credentialBaseUrl": "http://38.165.23.223:8317/v1"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» items|[object]|true|none||none|
|»»» name|string|true|none||none|
|»»» credentialId|integer|true|none||none|
|»»» model|string|true|none||none|
|»»» maxTokens|integer|true|none||none|
|»»» temperature|number|true|none||none|
|»»» retryCount|integer|true|none||none|
|»»» retryDelay|integer|true|none||none|
|»»» isDefault|boolean|true|none||none|
|»»» isActive|boolean|true|none||none|
|»»» description|string|true|none||none|
|»»» profileId|integer|true|none||none|
|»»» createTime|string|true|none||none|
|»»» updateTime|string|true|none||none|
|»»» credentialName|string|true|none||none|
|»»» credentialProvider|string|true|none||none|
|»»» credentialBaseUrl|string|true|none||none|

## GET 查询默认 LLM Profile

GET /agent/llm/profiles/default

注意事项：

- 只返回 `isDefault=true` 且 `isActive=true` 的 Profile。
- 没有默认 Profile 时，`data` 可能为 `null`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "name": "GPT-5.4",
        "credentialId": 7,
        "model": "GPT-5.4",
        "maxTokens": 65536,
        "temperature": 0.1,
        "retryCount": 3,
        "retryDelay": 2.0,
        "isDefault": true,
        "isActive": true,
        "description": "批量导入模型",
        "profileId": 3,
        "createTime": "2026-06-09T15:21:56.398820",
        "updateTime": "2026-06-09T15:21:56.398826",
        "credentialName": "my",
        "credentialProvider": "Custom",
        "credentialBaseUrl": "http://38.165.23.223:8317/v1"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## PUT 更新 LLM Profile

PUT /agent/llm/profiles/{profileId}

请求体字段均可选：

```json
{
  "name": "DeepSeek 备用",
  "temperature": 0.2,
  "isActive": true,
  "description": "备用模型"
}
```
注意事项：

- 如果更新时传 `isDefault=true`，其他 Profile 会被取消默认。
- 不允许通过此接口直接修改 provider、endpoint 或 API Key；这些字段仍通过 `/config/apikey` 管理。

> Body 请求参数

```json
{
    "name": "gpt-5.4-mini",
    "temperature": 1,
    "isActive": false,
    "description": "列较联群。目技温第公方声。京很时点值位。着选打。适铁整例才。管持构反确求。更采节准年说领。究张离林场己。"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|integer| 是 ||none|
|body|body|object| 是 ||none|
|» name|body|string| 否 ||none|
|» temperature|body|number| 否 ||none|
|» isActive|body|boolean| 否 ||none|
|» description|body|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "name": "gpt-5.4-mini",
        "credentialId": 7,
        "model": "gpt-5.4-mini",
        "maxTokens": 65536,
        "temperature": 1.0,
        "retryCount": 3,
        "retryDelay": 2.0,
        "isDefault": false,
        "isActive": false,
        "description": "列较联群。目技温第公方声。京很时点值位。着选打。适铁整例才。管持构反确求。更采节准年说领。究张离林场己。",
        "profileId": 2,
        "createTime": "2026-06-09T15:18:52.752333",
        "updateTime": "2026-06-09T15:31:13.724435",
        "credentialName": "my",
        "credentialProvider": "Custom",
        "credentialBaseUrl": "http://38.165.23.223:8317/v1"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 删除 LLM Profile

DELETE /agent/llm/profiles/{profileId}

注意事项：

- 如果已有历史 Session 绑定了该 Profile，删除后这些 Session 后续运行可能无法通过该 `profileId` 找到配置。
- 找不到 Profile 时会返回参数错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 批量创建 LLM Profile

POST /agent/llm/profiles/batch

  "description": "批量导入模型"
}
```

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "total": 2,
    "items": [
      {
        "profileId": 1,
        "name": "DeepSeek-deepseek-chat",
        "credentialId": 1,
        "credentialName": "deepseek-key",
        "credentialProvider": "Custom",
        "credentialBaseUrl": "https://api.deepseek.com/anthropic",
        "model": "deepseek-chat",
        "maxTokens": 65536,
        "temperature": 0.1,
        "retryCount": 3,
        "retryDelay": 2.0,
        "isDefault": true,
        "isActive": true,
        "description": "批量导入模型",
        "createTime": "2026-06-09T13:00:00",
        "updateTime": "2026-06-09T13:00:00"
      }
    ]
  }
}
```

注意事项：

- `models` 传模型 ID 字符串数组，通常来自 `GET /agent/llm/credentials/{credentialId}/models` 的 `models[].id`。
- 后端会去掉空字符串并对模型名去重。
- `namePrefix` 不传时，Profile 名称直接使用模型 ID。
- `namePrefix` 传入时，Profile 名称格式为 `{namePrefix}-{model}`，最长保留 100 字符。
- `isDefaultFirst=true` 时，只会把第一个创建成功的 Profile 设为默认；其他 Profile 为非默认。
- 批量创建不会直接修改 provider、endpoint 或 API Key，这些字段仍来自 credential。

> Body 请求参数

```json
{
  "credentialId": 7,
  "models": [
    "GPT-5.4",
    "gpt-5.5"
  ],
  "maxTokens": 65536,
  "temperature": 0.1,
  "retryCount": 3,
  "retryDelay": 2.0,
  "isDefaultFirst": true,
  "isActive": true,
  "description": "批量导入模型"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» credentialId|body|integer| 是 ||none|
|» models|body|[string]| 是 ||none|
|» namePrefix|body|string| 是 ||none|
|» maxTokens|body|integer| 是 ||none|
|» temperature|body|number| 是 ||none|
|» retryCount|body|integer| 是 ||none|
|» retryDelay|body|integer| 是 ||none|
|» isDefaultFirst|body|boolean| 是 ||none|
|» isActive|body|boolean| 是 ||none|
|» description|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 2,
        "items": [
            {
                "name": "GPT-5.4",
                "credentialId": 7,
                "model": "GPT-5.4",
                "maxTokens": 65536,
                "temperature": 0.1,
                "retryCount": 3,
                "retryDelay": 2.0,
                "isDefault": true,
                "isActive": true,
                "description": "批量导入模型",
                "profileId": 3,
                "createTime": "2026-06-09T15:21:56.398820",
                "updateTime": "2026-06-09T15:21:56.398826",
                "credentialName": "my",
                "credentialProvider": "Custom",
                "credentialBaseUrl": "http://38.165.23.223:8317/v1"
            },
            {
                "name": "gpt-5.5",
                "credentialId": 7,
                "model": "gpt-5.5",
                "maxTokens": 65536,
                "temperature": 0.1,
                "retryCount": 3,
                "retryDelay": 2.0,
                "isDefault": false,
                "isActive": true,
                "description": "批量导入模型",
                "profileId": 4,
                "createTime": "2026-06-09T15:21:56.410885",
                "updateTime": "2026-06-09T15:21:56.410888",
                "credentialName": "my",
                "credentialProvider": "Custom",
                "credentialBaseUrl": "http://38.165.23.223:8317/v1"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## PUT 设置默认 LLM Profile

PUT /agent/llm/profiles/{profileId}/default

注意事项：

- 目标 Profile 必须存在且 `isActive=true`。
- 设置成功后，其他 Profile 会被取消默认。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "name": "GPT-5.4",
        "credentialId": 7,
        "model": "GPT-5.4",
        "maxTokens": 65536,
        "temperature": 0.1,
        "retryCount": 3,
        "retryDelay": 2.0,
        "isDefault": true,
        "isActive": true,
        "description": "批量导入模型",
        "profileId": 3,
        "createTime": "2026-06-09T15:21:56.398820",
        "updateTime": "2026-06-09T15:32:36.028018",
        "credentialName": "my",
        "credentialProvider": "Custom",
        "credentialBaseUrl": "http://38.165.23.223:8317/v1"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 测试 LLM Profile 连通性

POST /agent/llm/profiles/{profileId}/test

对指定 LLM Profile 发起一次最小化连通性测试，用于验证凭证、Base URL 和模型名是否可正常调用。

执行逻辑：
- 后端会读取 Profile 对应的凭证与模型配置。
- 发送固定测试消息：`This is a connectivity test. Reply with exactly: OK`。
- 成功时返回 `available=true`、耗时 `latencyMs`、模型原始回复 `content`、`finishReason` 与 `usage`。
- 失败时不会抛 500；仍返回成功外层结构，但 `data.available=false`，并在 `error` 中给出错误原因。

前置条件：
- Profile 必须存在且 `isActive=true`。
- 绑定的凭证必须存在、已启用且 `baseUrl` 不为空。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "profileId": 2,
        "credentialId": 7,
        "model": "gpt-5.4-mini",
        "available": true,
        "latencyMs": 1647.15,
        "content": "OK",
        "finishReason": "stop",
        "usage": {
            "completion_tokens": 15,
            "total_tokens": 328,
            "prompt_tokens": 313,
            "prompt_tokens_details": {
                "cached_tokens": 0
            },
            "completion_tokens_details": {
                "reasoning_tokens": 8
            }
        },
        "error": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# 设置/模型价格

## POST 新增定价

POST /agent/model-pricing

创建一条模型定价记录。`credentialId` 不传或传 `null` 表示官方全局价；传入具体值表示该凭证的自定义价。**同一个 `(model, credentialId)` 组合不能重复。**

### Request Body

```json
{
  "model": "gpt-4o",
  "inputPrice": 1.0,
  "cachedInputPrice": 0.2,
  "outputPrice": 5.0,
  "multiplier": 1.0,
  "credentialId": null
}
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `model` | string | ✅ | - | 模型名称，1-100 字符 |
| `inputPrice` | float | ❌ | 1.0 | 非缓存输入价格（¥/百万 tokens），≥0 |
| `cachedInputPrice` | float | ❌ | 0.1 | 缓存命中输入价格（¥/百万 tokens），≥0 |
| `outputPrice` | float | ❌ | 3.0 | 输出价格（¥/百万 tokens），≥0 |
| `multiplier` | float | ❌ | 1.0 | 倍率，≥0 |
| `credentialId` | int / null | ❌ | null | `null` = 官方全局价；整数 = 用户凭证自定义价，需引用 `api_credentials` 表中存在的 id |

### Response `200 OK`

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "pricingId": 1,
    "model": "gpt-4o",
    "inputPrice": 1.0,
    "cachedInputPrice": 0.2,
    "outputPrice": 5.0,
    "multiplier": 1.0,
    "credentialId": null,
    "isActive": 1,
    "createdAt": "2026-06-10T14:00:00",
    "updatedAt": "2026-06-10T14:00:00"
  }
}
```

### Error `409 Conflict`

当 `(model, credentialId)` 组合已存在时返回唯一约束冲突。

> Body 请求参数

```json
{
  "model": "gpt-4o",
  "inputPrice": 1.0,
  "cachedInputPrice": 0.2,
  "outputPrice": 5.0,
  "multiplier": 1.0,
  "credentialId": null
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» model|body|string| 是 ||none|
|» inputPrice|body|integer| 是 ||none|
|» cachedInputPrice|body|number| 是 ||none|
|» outputPrice|body|integer| 是 ||none|
|» multiplier|body|integer| 是 ||none|
|» credentialId|body|integer| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询定价列表

GET /agent/model-pricing

支持按 `model`、`credentialId`、`isActive` 筛选。

### Query Parameters

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `model` | string | ❌ | - | 模型名模糊搜索（LIKE %xxx%） |
| `credentialId` | int | ❌ | - | 按凭证筛选，不传返回全部 |
| `isActive` | int | ❌ | - | 1=启用，0=禁用，不传返回全部 |

### 示例请求

```http
GET /agent/model-pricing?model=deepseek&isActive=1
```

### Response `200 OK`

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 3,
    "items": [
      {
        "pricingId": 1,
        "model": "deepseek-v4-flash",
        "inputPrice": 1.0,
        "cachedInputPrice": 0.02,
        "outputPrice": 2.0,
        "multiplier": 1.0,
        "credentialId": null,
        "isActive": 1,
        "createdAt": "2026-06-10T14:00:00",
        "updatedAt": "2026-06-10T14:00:00"
      },
      {
        "pricingId": 2,
        "model": "deepseek-v4-pro",
        "inputPrice": 3.0,
        "cachedInputPrice": 0.025,
        "outputPrice": 6.0,
        "multiplier": 1.0,
        "credentialId": null,
        "isActive": 1,
        "createdAt": "2026-06-10T14:00:00",
        "updatedAt": "2026-06-10T14:00:00"
      },
      {
        "pricingId": 10,
        "model": "deepseek-chat",
        "inputPrice": 1.0,
        "cachedInputPrice": 0.02,
        "outputPrice": 2.0,
        "multiplier": 1.0,
        "credentialId": null,
        "isActive": 1,
        "createdAt": "2026-06-10T14:00:00",
        "updatedAt": "2026-06-10T14:00:00"
      }
    ]
  }
}
```

结果按 `credentialId NULLS LAST` + `model 升序` 排列，即官方全局价排在前面，用户自定义价排在后面。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|model|query|string| 否 ||none|
|isActive|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 获取单条定价

GET /agent/model-pricing/{pricingId}

### Path Parameters

| 参数 | 类型 | 说明 |
|---|---|---|
| `pricingId` | int | 定价记录 ID |

### Response `200 OK`

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "pricingId": 1,
    "model": "deepseek-v4-flash",
    "inputPrice": 1.0,
    "cachedInputPrice": 0.02,
    "outputPrice": 2.0,
    "multiplier": 1.0,
    "credentialId": null,
    "isActive": 1,
    "createdAt": "2026-06-10T14:00:00",
    "updatedAt": "2026-06-10T14:00:00"
  }
}
```

### Error `400 Bad Request`

```json
{
  "code": 400,
  "message": "不存在 id 为 999 的定价记录",
  "data": null
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|pricingId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## PUT 更新定价

PUT /agent/model-pricing/{pricingId}

部分更新，只传需要修改的字段即可。

### Path Parameters

| 参数 | 类型 | 说明 |
|---|---|---|
| `pricingId` | int | 定价记录 ID |

### Request Body

```json
{
  "inputPrice": 2.0,
  "cachedInputPrice": 0.5
}
```

所有字段均为可选：

| 参数 | 类型 | 说明 |
|---|---|---|
| `model` | string | 模型名称 |
| `inputPrice` | float | 非缓存输入价格，≥0 |
| `cachedInputPrice` | float | 缓存命中输入价格，≥0 |
| `outputPrice` | float | 输出价格，≥0 |
| `multiplier` | float | 倍率，≥0 |
| `credentialId` | int / null | 传 `0` 或 `null` 都不更新该字段；传具体值更新 |
| `isActive` | int | 0=禁用，1=启用 |

### Response `200 OK`

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "pricingId": 1,
    "model": "deepseek-v4-flash",
    "inputPrice": 2.0,
    "cachedInputPrice": 0.5,
    "outputPrice": 2.0,
    "multiplier": 1.0,
    "credentialId": null,
    "isActive": 1,
    "createdAt": "2026-06-10T14:00:00",
    "updatedAt": "2026-06-10T14:00:00"
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|pricingId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 删除定价

DELETE /agent/model-pricing/{pricingId}

删除后该模型的价格将按优先级回退到官方全局价或代码默认值。

### Path Parameters

| 参数 | 类型 | 说明 |
|---|---|---|
| `pricingId` | int | 定价记录 ID |

### Response `200 OK`

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

### Error `400 Bad Request`

```json
{
  "code": 400,
  "message": "不存在 id 为 999 的定价记录",
  "data": null
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|pricingId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# 进程管理

## GET 进程列表 SSE

GET /process/sse/

SSE 实时推送进程列表。接口返回 `text/event-stream`，需要查询参数 `sortedBy`，可选查询参数 `keyword`。`sortedBy` 取值为 `0=按 CPU`、`1=按内存`、`2=按 PID`；`keyword` 会用于进程名或命令关键字过滤。服务端约每 4 秒推送一次完整进程数组，单条事件内容为 `data: <json-array>\n\n`，数组元素为 `ProcessInfo`，包含 `pid`、`processName`、`userName`、`cpuPercent`、`memoryPercent`、`status`、`command`，以及可选的监听端口信息 `ports`。客户端断开连接后，服务端会自动停止推送。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sortedBy|query|integer| 是 ||排序关键词，cpu0,mem1,pid2，默认0|
|keyword|query|string| 否 ||命令或者进程名的查询关键词|

> 返回示例

> 200 Response

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 温和杀进程

DELETE /process/kill

向指定进程发送 SIGTERM（15）进行温和终止。请求体包含 `pid` 和可选 `reason`。成功时返回 `ProcessKillResult`；同时服务端会将操作写入进程操作日志。若 PID 不存在或没有权限结束该进程，会返回业务错误。

> Body 请求参数

```json
{
    "pid": 3752463,
    "reason": "test"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» pid|body|integer| 是 ||none|
|» reason|body|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "pid": 3752463,
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 强制杀进程

DELETE /process/force-kill

向指定进程发送 SIGKILL（9）进行强制终止。请求体与温和杀进程一致，包含 `pid` 和可选 `reason`。成功时返回 `ProcessKillResult`，并写入进程操作日志；若 PID 不存在或权限不足，会返回业务错误。

> Body 请求参数

```json
{
    "pid": 3752570,
    "reason": "test"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» pid|body|integer| 是 ||none|
|» reason|body|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "success": true,
        "pid": 3752570,
        "errorMessage": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询进程详情

GET /process/{pid}

根据 PID 查询单个进程详情。路径参数 `pid` 必须大于 0。成功后返回 `ProcessDetailInfo`，除基础进程信息外，还包含 `parentPid`、`startTime`、`exePath`、`threadCount`、`fdCount`、`workDir`、`rss`、`vms` 等细节。若 PID 不存在或无权限访问进程详情，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|pid|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "pid": 2183146,
        "processName": "pycharm",
        "userName": "hzz",
        "cpuPercent": 0.0,
        "memoryPercent": 17.87,
        "status": "sleeping",
        "command": "/home/hzz/.cache/JetBrains/RemoteDev/dist/4032e34cf1066_pycharm-261.23567.80/bin/pycharm serverMode",
        "ports": [
            {
                "listenAddress": "::ffff:127.0.0.1",
                "protocol": "TCP",
                "port": 5990
            },
            {
                "listenAddress": "::ffff:127.0.0.1",
                "protocol": "TCP",
                "port": 63342
            },
            {
                "listenAddress": "::ffff:127.0.0.1",
                "protocol": "TCP",
                "port": 61553
            }
        ],
        "parentPid": 1,
        "startTime": "2026-04-24T14:41:30.370000Z",
        "exePath": "/home/hzz/.cache/JetBrains/RemoteDev/dist/4032e34cf1066_pycharm-261.23567.80/bin/pycharm",
        "threadCount": 135,
        "fdCount": 428,
        "workDir": "/home/hzz",
        "rss": 2996695040,
        "vms": 8181956608
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 自动清理高负载进程

POST /process/auto-clean

按阈值自动扫描并清理高负载进程。请求体包含 `cpuThreshold` 和 `memoryThreshold`，两者都必须大于 30。服务端会扫描当前进程列表，清理超阈值目标，并返回 `ProcessAutoCleanResult`，其中包含 `killedProcesses`、`totalScanned`、`totalKilled`。执行结果会写入进程操作日志。

> Body 请求参数

```json
{
    "cpuThreshold": 90 ,
    "memoryThreshold": 90 
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» cpuThreshold|body|integer| 否 ||none|
|» memoryThreshold|body|integer| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "killedProcesses": [],
        "totalScanned": 292,
        "totalKilled": 0
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询僵尸/孤儿进程

GET /process/get/zombies

查询当前系统中的僵尸进程或孤儿进程列表。成功时返回 `ProcessInfo[]`；若底层工具执行失败，会返回统一业务错误。该接口适合配合批量清理或人工排障使用。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 批量温和杀进程

DELETE /process/batch-kill

批量向多个进程发送 SIGTERM。请求体包含 `pids` 数组和可选 `reason`。成功时返回 `BatchKillResult`，其中包含逐 PID 的执行结果以及 `totalRequested`、`totalSuccess`、`totalFailed` 汇总信息；执行摘要会写入进程操作日志。

> Body 请求参数

```json
{
    "pids": [3753328,3753331,3753332],
    "reason": "tyest"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» pids|body|[integer]| 是 ||none|
|» reason|body|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "results": [
            {
                "success": true,
                "pid": 3753328,
                "errorMessage": null
            },
            {
                "success": true,
                "pid": 3753331,
                "errorMessage": null
            },
            {
                "success": true,
                "pid": 3753332,
                "errorMessage": null
            }
        ],
        "totalRequested": 3,
        "totalSuccess": 3,
        "totalFailed": 0
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 批量强制杀进程

DELETE /process/batch-force-kill

批量向多个进程发送 SIGKILL。请求体包含 `pids` 数组和可选 `reason`。成功时返回 `BatchKillResult`，其中会逐项给出每个 PID 的处理结果，并记录成功/失败汇总；执行摘要会写入进程操作日志。

> Body 请求参数

```json
{
    "pids": [3753434,3753435],
    "reason": ""
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» pids|body|[integer]| 是 ||none|
|» reason|body|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "results": [
            {
                "success": true,
                "pid": 3753434,
                "errorMessage": null
            },
            {
                "success": true,
                "pid": 3753435,
                "errorMessage": null
            }
        ],
        "totalRequested": 2,
        "totalSuccess": 2,
        "totalFailed": 0
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 查询进程操作日志

POST /process/log

分页查询进程管理相关的操作日志。请求体继承 `PageSearchRequest`，包含 `page` 和 `pageSize`。返回 `data` 为 `{ total, items }`，items 中包含操作类型、目标 PID、操作人、原因、结果、详情和创建时间，可用于审计 kill/auto-clean/batch-kill 等行为。

> Body 请求参数

```json
{
    "page": 1,
    "pageSize": 3
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» page|body|integer| 是 ||none|
|» pageSize|body|integer| 是 ||none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 5,
        "items": [
            {
                "operationType": "normal-kill",
                "targetPids": "3752463",
                "operator": "user",
                "reason": "test",
                "result": "success",
                "detail": null,
                "logId": 1,
                "createTime": "2026-04-26T17:07:13.041639"
            },
            {
                "operationType": "Force-Kill",
                "targetPids": "3752570",
                "operator": "user",
                "reason": "test",
                "result": "success",
                "detail": null,
                "logId": 2,
                "createTime": "2026-04-26T17:08:32.167119"
            },
            {
                "operationType": "autoclean",
                "targetPids": "",
                "operator": "user",
                "reason": "autoclean",
                "result": "totalKilled:0\ntotalS",
                "detail": null,
                "logId": 3,
                "createTime": "2026-04-26T17:10:35.022921"
            },
            {
                "operationType": "batchKillProcess",
                "targetPids": "3753328,3753331,3753332",
                "operator": "user",
                "reason": "tyest",
                "result": "success",
                "detail": "totalRequested:3\ntotalSuccess:3\ntotalFailed:0\n3753328:success\n3753331:success\n3753332:success\n",
                "logId": 4,
                "createTime": "2026-04-26T17:19:43.451310"
            },
            {
                "operationType": "batchForceKillProcess",
                "targetPids": "3753434,3753435",
                "operator": "user",
                "reason": "",
                "result": "success",
                "detail": "totalRequested:2\ntotalSuccess:2\ntotalFailed:0\n3753434:success\n3753435:success\n",
                "logId": 5,
                "createTime": "2026-04-26T17:20:23.679944"
            }
        ]
    }
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 5,
        "items": [
            {
                "operationType": "normal-kill",
                "targetPids": "3752463",
                "operator": "user",
                "reason": "test",
                "result": "success",
                "detail": null,
                "logId": 1,
                "createTime": "2026-04-26T17:07:13.041639"
            },
            {
                "operationType": "Force-Kill",
                "targetPids": "3752570",
                "operator": "user",
                "reason": "test",
                "result": "success",
                "detail": null,
                "logId": 2,
                "createTime": "2026-04-26T17:08:32.167119"
            },
            {
                "operationType": "autoclean",
                "targetPids": "",
                "operator": "user",
                "reason": "autoclean",
                "result": "totalKilled:0\ntotalS",
                "detail": null,
                "logId": 3,
                "createTime": "2026-04-26T17:10:35.022921"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# ssh

## GET 检查普通终端是否可用

GET /terminal/available

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

```json
{"code":0,"msg":"当前服务器未安装 Docker，普通终端功能不可用","data":null}
```

```json
{
    "code": 0,
    "msg": "当前服务器未安装 Docker，普通终端功能不可用",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 查询终端会话日志

POST /terminal/session/log

> Body 请求参数

```json
{
    "page": 1,
    "pageSize": 10 
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» page|body|integer| 是 ||none|
|» pageSize|body|integer| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 3,
        "items": [
            {
                "sessionId": "3ed5786502f949c0b2f6b1274cb63a3a",
                "userId": 1,
                "panelUsername": "admin",
                "clientIp": "127.0.0.1",
                "mode": "admin",
                "normalContainerName": "app-container",
                "adminLinuxUsername": "he",
                "adminAuthAttempted": true,
                "adminAuthSucceeded": true,
                "adminAuthFailedCount": 0,
                "startTime": "2026-05-28T20:03:55.731125",
                "endTime": "2026-05-28T20:05:06.936744",
                "closeReason": "client_disconnect",
                "exitCode": null,
                "logId": 3
            },
            {
                "sessionId": "f30e90f77a1b48eb9df2406328622b7f",
                "userId": 1,
                "panelUsername": "admin",
                "clientIp": "127.0.0.1",
                "mode": "admin",
                "normalContainerName": "app-container",
                "adminLinuxUsername": "he",
                "adminAuthAttempted": true,
                "adminAuthSucceeded": true,
                "adminAuthFailedCount": 0,
                "startTime": "2026-05-28T19:56:37.480197",
                "endTime": "2026-05-28T20:01:56.230762",
                "closeReason": "client_disconnect",
                "exitCode": null,
                "logId": 2
            },
            {
                "sessionId": "29d0c96da7fa47afa0ccd25b45f6ed43",
                "userId": 1,
                "panelUsername": "admin",
                "clientIp": "127.0.0.1",
                "mode": "normal",
                "normalContainerName": "app-container",
                "adminLinuxUsername": null,
                "adminAuthAttempted": true,
                "adminAuthSucceeded": false,
                "adminAuthFailedCount": 1,
                "startTime": "2026-05-28T19:49:03.539905",
                "endTime": "2026-05-28T19:56:16.992250",
                "closeReason": "client_disconnect",
                "exitCode": null,
                "logId": 1
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» items|[object]|true|none||none|
|»»» sessionId|string|true|none||none|
|»»» userId|integer|true|none||none|
|»»» panelUsername|string|true|none||none|
|»»» clientIp|string|true|none||none|
|»»» mode|string|true|none||none|
|»»» normalContainerName|string|true|none||none|
|»»» adminLinuxUsername|string¦null|true|none||none|
|»»» adminAuthAttempted|boolean|true|none||none|
|»»» adminAuthSucceeded|boolean|true|none||none|
|»»» adminAuthFailedCount|integer|true|none||none|
|»»» startTime|string|true|none||none|
|»»» endTime|string|true|none||none|
|»»» closeReason|string|true|none||none|
|»»» exitCode|null|true|none||none|
|»»» logId|integer|true|none||none|

# docker

## GET 查询 Docker 安装信息

GET /docker/install

查询 Docker 的安装状态与相关信息。成功时返回底层安装检测结果；若系统未安装 Docker 或检测失败，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "isInstalled": true,
        "version": "29.1.3"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询运行中容器列表

GET /docker/containers

查询当前处于运行状态的 Docker 容器。响应 `data` 为 `{ total, list }`，只包含运行中的容器，不含已停止容器，适合首页概览或运行态列表页。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 2,
        "list": [
            {
                "containerId": "9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758",
                "imageName": "filebrowser/filebrowser:latest",
                "status": "Up 21 hours (healthy)",
                "ports": "100.105.63.51:8088->80/tcp",
                "cpuPercent": 3.53,
                "memoryUsageMB": 14.43,
                "memoryLimitMB": 31313.92
            },
            {
                "containerId": "6a935990aac02c9705cfc97f1ba871adba08bea2f46d73bc29e754625f4e874f",
                "imageName": "mlikiowa/napcat-docker:latest",
                "status": "Up 2 days",
                "ports": "0.0.0.0:3001->3001/tcp, [::]:3001->3001/tcp, 0.0.0.0:6099->6099/tcp, [::]:6099->6099/tcp",
                "cpuPercent": 1.28,
                "memoryUsageMB": 641.9,
                "memoryLimitMB": 31313.92
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询全部容器列表

GET /docker/container/list

查询全部 Docker 容器，包括运行中和已停止容器。响应 `data` 为 `{ total, list }`，适合容器管理页完整展示。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 2,
        "list": [
            {
                "containerId": "9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758",
                "imageName": "filebrowser/filebrowser:latest",
                "status": "Up 22 hours (healthy)",
                "ports": "100.105.63.51:8088->80/tcp",
                "cpuPercent": 0.0,
                "memoryUsageMB": 13.29,
                "memoryLimitMB": 31313.92
            },
            {
                "containerId": "6a935990aac02c9705cfc97f1ba871adba08bea2f46d73bc29e754625f4e874f",
                "imageName": "mlikiowa/napcat-docker:latest",
                "status": "Up 2 days",
                "ports": "0.0.0.0:3001->3001/tcp, [::]:3001->3001/tcp, 0.0.0.0:6099->6099/tcp, [::]:6099->6099/tcp",
                "cpuPercent": 1.77,
                "memoryUsageMB": 641.3,
                "memoryLimitMB": 31313.92
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询镜像列表

GET /docker/images

查询本机已有 Docker 镜像列表。响应 `data` 为 `{ total, list }`，其中 `list` 为镜像信息数组，适合创建容器前的镜像选择。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

```json
{"code":1,"msg":"success","data":{"total":2,"list":[{"repository":"mlikiowa/napcat-docker","tag":"latest","imageId":"2acfef8952da","createdSince":"11 days ago","createdAt":"2026-05-22 22:40:57 +0800 CST","size":"2.1GB"},{"repository":"filebrowser/filebrowser","tag":"latest","imageId":"aefb0c20de10","createdSince":"12 days ago","createdAt":"2026-05-21 21:56:17 +0800 CST","size":"55MB"}]}}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 2,
        "list": [
            {
                "repository": "mlikiowa/napcat-docker",
                "tag": "latest",
                "imageId": "2acfef8952da",
                "createdSince": "11 days ago",
                "createdAt": "2026-05-22 22:40:57 +0800 CST",
                "size": "2.1GB"
            },
            {
                "repository": "filebrowser/filebrowser",
                "tag": "latest",
                "imageId": "aefb0c20de10",
                "createdSince": "12 days ago",
                "createdAt": "2026-05-21 21:56:17 +0800 CST",
                "size": "55MB"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询容器详情

GET /docker/container/{containerId}

查询指定容器的详细信息。路径参数 `containerId` 可使用容器 ID 或工具支持的标识符。成功时返回单个容器的详细状态、配置与运行信息。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|containerId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "Id": "9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758",
        "Created": "2026-06-02T14:51:04.164821739Z",
        "Path": "tini",
        "Args": [
            "--",
            "/init.sh",
            "--address",
            "0.0.0.0",
            "--port",
            "80",
            "--root",
            "/srv",
            "--database",
            "/database/filebrowser.db"
        ],
        "State": {
            "Status": "running",
            "Running": true,
            "Paused": false,
            "Restarting": false,
            "OOMKilled": false,
            "Dead": false,
            "Pid": 1602108,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2026-06-02T14:51:04.416664158Z",
            "FinishedAt": "0001-01-01T00:00:00Z",
            "Health": {
                "Status": "healthy",
                "FailingStreak": 0,
                "Log": [
                    {
                        "Start": "2026-06-03T20:23:56.811658905+08:00",
                        "End": "2026-06-03T20:23:56.848015855+08:00",
                        "ExitCode": 0,
                        "Output": ""
                    },
                    {
                        "Start": "2026-06-03T20:24:01.84870767+08:00",
                        "End": "2026-06-03T20:24:01.89539127+08:00",
                        "ExitCode": 0,
                        "Output": ""
                    },
                    {
                        "Start": "2026-06-03T20:24:06.895937547+08:00",
                        "End": "2026-06-03T20:24:06.950964948+08:00",
                        "ExitCode": 0,
                        "Output": ""
                    },
                    {
                        "Start": "2026-06-03T20:24:11.951826432+08:00",
                        "End": "2026-06-03T20:24:11.999326044+08:00",
                        "ExitCode": 0,
                        "Output": ""
                    },
                    {
                        "Start": "2026-06-03T20:24:17.000879451+08:00",
                        "End": "2026-06-03T20:24:17.047163667+08:00",
                        "ExitCode": 0,
                        "Output": ""
                    }
                ]
            }
        },
        "Image": "sha256:aefb0c20de10ef8b617995ca5522479ad40d41e6386bd01946a345c6026ff31c",
        "ResolvConfPath": "/var/lib/docker/containers/9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758/resolv.conf",
        "HostnamePath": "/var/lib/docker/containers/9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758/hostname",
        "HostsPath": "/var/lib/docker/containers/9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758/hosts",
        "LogPath": "/var/lib/docker/containers/9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758/9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758-json.log",
        "Name": "/filebrowser",
        "RestartCount": 0,
        "Driver": "overlayfs",
        "Platform": "linux",
        "MountLabel": "",
        "ProcessLabel": "",
        "AppArmorProfile": "docker-default",
        "ExecIDs": null,
        "HostConfig": {
            "Binds": [
                "/home/he/services/filebrowser/config:/config:rw",
                "/home/he/services/filebrowser/database:/database:rw",
                "/home/he:/srv:rw"
            ],
            "ContainerIDFile": "",
            "LogConfig": {
                "Type": "json-file",
                "Config": {}
            },
            "NetworkMode": "filebrowser_default",
            "PortBindings": {
                "80/tcp": [
                    {
                        "HostIp": "100.105.63.51",
                        "HostPort": "8088"
                    }
                ]
            },
            "RestartPolicy": {
                "Name": "unless-stopped",
                "MaximumRetryCount": 0
            },
            "AutoRemove": false,
            "VolumeDriver": "",
            "VolumesFrom": null,
            "ConsoleSize": [
                0,
                0
            ],
            "CapAdd": null,
            "CapDrop": null,
            "CgroupnsMode": "private",
            "Dns": null,
            "DnsOptions": null,
            "DnsSearch": null,
            "ExtraHosts": [],
            "GroupAdd": null,
            "IpcMode": "private",
            "Cgroup": "",
            "Links": null,
            "OomScoreAdj": 0,
            "PidMode": "",
            "Privileged": false,
            "PublishAllPorts": false,
            "ReadonlyRootfs": false,
            "SecurityOpt": null,
            "UTSMode": "",
            "UsernsMode": "",
            "ShmSize": 67108864,
            "Runtime": "runc",
            "Isolation": "",
            "CpuShares": 0,
            "Memory": 0,
            "NanoCpus": 0,
            "CgroupParent": "",
            "BlkioWeight": 0,
            "BlkioWeightDevice": null,
            "BlkioDeviceReadBps": null,
            "BlkioDeviceWriteBps": null,
            "BlkioDeviceReadIOps": null,
            "BlkioDeviceWriteIOps": null,
            "CpuPeriod": 0,
            "CpuQuota": 0,
            "CpuRealtimePeriod": 0,
            "CpuRealtimeRuntime": 0,
            "CpusetCpus": "",
            "CpusetMems": "",
            "Devices": null,
            "DeviceCgroupRules": null,
            "DeviceRequests": null,
            "MemoryReservation": 0,
            "MemorySwap": 0,
            "MemorySwappiness": null,
            "OomKillDisable": null,
            "PidsLimit": null,
            "Ulimits": null,
            "CpuCount": 0,
            "CpuPercent": 0,
            "IOMaximumIOps": 0,
            "IOMaximumBandwidth": 0,
            "MaskedPaths": [
                "/proc/acpi",
                "/proc/asound",
                "/proc/interrupts",
                "/proc/kcore",
                "/proc/keys",
                "/proc/latency_stats",
                "/proc/sched_debug",
                "/proc/scsi",
                "/proc/timer_list",
                "/proc/timer_stats",
                "/sys/devices/virtual/powercap",
                "/sys/firmware",
                "/sys/devices/system/cpu/cpu0/thermal_throttle",
                "/sys/devices/system/cpu/cpu1/thermal_throttle",
                "/sys/devices/system/cpu/cpu2/thermal_throttle",
                "/sys/devices/system/cpu/cpu3/thermal_throttle",
                "/sys/devices/system/cpu/cpu4/thermal_throttle",
                "/sys/devices/system/cpu/cpu5/thermal_throttle",
                "/sys/devices/system/cpu/cpu6/thermal_throttle",
                "/sys/devices/system/cpu/cpu7/thermal_throttle",
                "/sys/devices/system/cpu/cpu8/thermal_throttle",
                "/sys/devices/system/cpu/cpu9/thermal_throttle",
                "/sys/devices/system/cpu/cpu10/thermal_throttle",
                "/sys/devices/system/cpu/cpu11/thermal_throttle",
                "/sys/devices/system/cpu/cpu12/thermal_throttle",
                "/sys/devices/system/cpu/cpu13/thermal_throttle",
                "/sys/devices/system/cpu/cpu14/thermal_throttle",
                "/sys/devices/system/cpu/cpu15/thermal_throttle",
                "/sys/devices/system/cpu/cpu16/thermal_throttle",
                "/sys/devices/system/cpu/cpu17/thermal_throttle",
                "/sys/devices/system/cpu/cpu18/thermal_throttle",
                "/sys/devices/system/cpu/cpu19/thermal_throttle"
            ],
            "ReadonlyPaths": [
                "/proc/bus",
                "/proc/fs",
                "/proc/irq",
                "/proc/sys",
                "/proc/sysrq-trigger"
            ]
        },
        "Storage": {
            "RootFS": {
                "Snapshot": {
                    "Name": "overlayfs"
                }
            }
        },
        "Mounts": [
            {
                "Type": "bind",
                "Source": "/home/he/services/filebrowser/config",
                "Destination": "/config",
                "Mode": "rw",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "bind",
                "Source": "/home/he/services/filebrowser/database",
                "Destination": "/database",
                "Mode": "rw",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "bind",
                "Source": "/home/he",
                "Destination": "/srv",
                "Mode": "rw",
                "RW": true,
                "Propagation": "rprivate"
            }
        ],
        "Config": {
            "Hostname": "9897fd3e4b61",
            "Domainname": "",
            "User": "1000:1000",
            "AttachStdin": false,
            "AttachStdout": true,
            "AttachStderr": true,
            "ExposedPorts": {
                "80/tcp": {}
            },
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "UID=1000",
                "GID=1000"
            ],
            "Cmd": [
                "--address",
                "0.0.0.0",
                "--port",
                "80",
                "--root",
                "/srv",
                "--database",
                "/database/filebrowser.db"
            ],
            "Healthcheck": {
                "Test": [
                    "CMD-SHELL",
                    "/healthcheck.sh"
                ],
                "Interval": 5000000000,
                "Timeout": 3000000000,
                "StartPeriod": 2000000000
            },
            "Image": "filebrowser/filebrowser:latest",
            "Volumes": {
                "/config": {},
                "/database": {},
                "/srv": {}
            },
            "WorkingDir": "",
            "Entrypoint": [
                "tini",
                "--",
                "/init.sh"
            ],
            "Labels": {
                "com.docker.compose.config-hash": "1515ebd844232cfb5c8e9c27cda3407f1df4bcd7f3eba689e3d38aeba3533ff1",
                "com.docker.compose.container-number": "1",
                "com.docker.compose.depends_on": "",
                "com.docker.compose.image": "sha256:aefb0c20de10ef8b617995ca5522479ad40d41e6386bd01946a345c6026ff31c",
                "com.docker.compose.oneoff": "False",
                "com.docker.compose.project": "filebrowser",
                "com.docker.compose.project.config_files": "/home/he/services/filebrowser/compose.yaml",
                "com.docker.compose.project.working_dir": "/home/he/services/filebrowser",
                "com.docker.compose.replace": "filebrowser",
                "com.docker.compose.service": "filebrowser",
                "com.docker.compose.version": "2.40.3",
                "org.opencontainers.image.created": "2026-05-21T13:46:15Z",
                "org.opencontainers.image.name": "filebrowser",
                "org.opencontainers.image.revision": "a1e442ef9e4a14719184bf02c50dbc981ecf8665",
                "org.opencontainers.image.source": "https://github.com/filebrowser/filebrowser",
                "org.opencontainers.image.version": "2.63.5"
            }
        },
        "NetworkSettings": {
            "SandboxID": "4cafc378c27da00dd9cb0195fd7bad0fbc627990323156fdbcf60ed96e0639c1",
            "SandboxKey": "/var/run/docker/netns/4cafc378c27d",
            "Ports": {
                "80/tcp": [
                    {
                        "HostIp": "100.105.63.51",
                        "HostPort": "8088"
                    }
                ]
            },
            "Networks": {
                "filebrowser_default": {
                    "IPAMConfig": null,
                    "Links": null,
                    "Aliases": [
                        "filebrowser",
                        "filebrowser"
                    ],
                    "DriverOpts": null,
                    "GwPriority": 0,
                    "NetworkID": "228021de7eec13392ea649a5ac4300ee3e9e5bd20614dd430df7021f0f827523",
                    "EndpointID": "f3963c751ee779650adcdf176f9b2ea5be553b541c68162c64d040289f03a00d",
                    "Gateway": "172.19.0.1",
                    "IPAddress": "172.19.0.2",
                    "MacAddress": "de:a5:be:f4:4e:fa",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "DNSNames": [
                        "filebrowser",
                        "9897fd3e4b61"
                    ]
                }
            }
        },
        "ImageManifestDescriptor": {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "digest": "sha256:2540ced7c8ced07c8edf8b26f8b66545f3ccd719d51c48a1618aa651251e3eb3",
            "size": 2818,
            "platform": {
                "architecture": "amd64",
                "os": "linux"
            }
        }
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 删除容器

DELETE /docker/container/{containerId}

删除指定容器。路径参数 `containerId` 指定目标容器，成功时返回 `{ containerId, isDeleted: true }`。该操作具有副作用，删除后容器实例不可恢复。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|containerId|path|string| 是 ||none|

> 返回示例

```json
{
    "code": 0,
    "msg": "删除 Docker 容器失败",
    "data": null
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "containerId": "6a935990aac02c9705cfc97f1ba871adba08bea2f46d73bc29e754625f4e874f",
        "isDeleted": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询容器日志

GET /docker/container/{containerId}/logs

读取指定容器的最近日志。路径参数 `containerId` 指定目标容器，查询参数 `tailLines` 控制返回尾部日志行数，默认 200，允许范围 1-5000。成功时返回日志内容；若容器不存在或无权读取，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|containerId|path|string| 是 ||none|
|tailLines|query|integer| 否 ||默认200|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "containerId": "9897fd3e4b61aa7389f3a41419ec0bb4866def3905a51f22031dda8a7a677758",
        "logs": "2026/06/02 14:51:04 Listening on [::]:80\n2026/06/03 05:33:21 /api/renew: 401 172.19.0.1 <nil>\n2026/06/03 05:33:22 /api/renew: 401 172.19.0.1 <nil>",
        "errors": "2026/06/02 14:51:04 Using config file: /config/settings.json\n2026/06/02 14:51:04 Using database: /database/filebrowser.db"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 停止容器

POST /docker/container/{containerId}/stop

停止指定容器。路径参数 `containerId` 指定目标容器，成功时响应会附带 `isStopped=true` 和底层停止结果。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|containerId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "containerId": "e7d4332f2f1f27dcd9369eb67700a296ff916398eff5e616073c947297f7e87a",
        "isStopped": true,
        "success": true,
        "action": "stop",
        "containerName": "my-nginx",
        "previousStatus": "running",
        "currentStatus": "exited",
        "previousRunning": true,
        "currentRunning": false,
        "returnCode": 0,
        "stdout": "e7d4332f2f1f27dcd9369eb67700a296ff916398eff5e616073c947297f7e87a",
        "stderr": ""
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 启动容器

POST /docker/container/{containerId}/start

启动指定容器。路径参数 `containerId` 指定目标容器，成功时响应会附带 `isStarted=true` 和底层启动结果。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|containerId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "containerId": "e7d4332f2f1f27dcd9369eb67700a296ff916398eff5e616073c947297f7e87a",
        "isStarted": true,
        "success": true,
        "action": "start",
        "containerName": "my-nginx",
        "previousStatus": "exited",
        "currentStatus": "running",
        "previousRunning": false,
        "currentRunning": true,
        "returnCode": 0,
        "stdout": "e7d4332f2f1f27dcd9369eb67700a296ff916398eff5e616073c947297f7e87a",
        "stderr": ""
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 重启容器

POST /docker/container/{containerId}/restart

重启指定容器。路径参数 `containerId` 指定目标容器，成功时响应会附带 `isRestarted=true` 和底层重启结果。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|containerId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "containerId": "e7d4332f2f1f27dcd9369eb67700a296ff916398eff5e616073c947297f7e87a",
        "isRestarted": true,
        "success": true,
        "action": "restart",
        "containerName": "my-nginx",
        "previousStatus": "running",
        "currentStatus": "running",
        "previousRunning": true,
        "currentRunning": true,
        "returnCode": 0,
        "stdout": "e7d4332f2f1f27dcd9369eb67700a296ff916398eff5e616073c947297f7e87a",
        "stderr": ""
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 拉取镜像

POST /docker/image/pull

拉取 Docker 镜像。该接口通过查询参数接收 `imageName`、`tag`、`platform`、`registry`；其中 `tag` 默认 `latest`，`platform` 和 `registry` 可选。成功时返回镜像拉取结果，适合容器创建前预拉取镜像。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|imageName|query|string| 是 ||none|
|tag|query|string| 否 ||none|
|platform|query|string| 否 ||none|
|registry|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "image": "nginx:latest",
        "platform": "linux/amd64",
        "isPulled": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 创建容器

POST /docker/container

创建新的 Docker 容器。当前接口主要通过查询参数接收 `imageName`、`containerName`、`ports`、`envVars`、`volumes`、`platform`、`restartPolicy`；其中 `ports`、`envVars`、`volumes` 需要传 JSON 字符串，后端会先解析再调用底层 Docker 创建逻辑。成功时返回新容器的创建结果。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|imageName|query|string| 否 ||none|
|containerName|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "containerId": "e7d4332f2f1f27dcd9369eb67700a296ff916398eff5e616073c947297f7e87a",
        "containerName": "my-nginx",
        "imageName": "nginx",
        "platform": null,
        "ports": {},
        "envVars": {},
        "volumes": {},
        "restartPolicy": null,
        "isCreated": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 搜索 Docker Hub 镜像

GET /docker/search

按关键词搜索可用的 Docker 镜像。查询参数 `q` 为搜索词，`limit` 为返回数量，默认 25，最大 100。响应 `data` 为 `{ total, list }`，适合镜像搜索和推荐选择。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|q|query|string| 否 ||none|
|limit|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 25,
        "list": [
            {
                "name": "nginx",
                "description": "Official build of Nginx.",
                "starCount": "21287",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "nginx/nginx-ingress",
                "description": "NGINX and  NGINX Plus Ingress Controllers fo…",
                "starCount": "120",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "nginx/nginx-prometheus-exporter",
                "description": "NGINX Prometheus Exporter for NGINX and NGIN…",
                "starCount": "51",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "nginx/nginx-ingress-operator",
                "description": "NGINX Ingress Operator for NGINX and NGINX P…",
                "starCount": "4",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "nginx/unit",
                "description": "This repository is retired, use the Docker o…",
                "starCount": "66",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "nginx/nginx-quic-qns",
                "description": "NGINX QUIC interop",
                "starCount": "1",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "nginx/nginxaas-loadbalancer-kubernetes",
                "description": "",
                "starCount": "1",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "nginx/unit-preview",
                "description": "Unit preview features",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "bitnamicharts/nginx",
                "description": "Bitnami Helm chart for NGINX Open Source",
                "starCount": "3",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "ubuntu/nginx",
                "description": "Nginx, a high-performance reverse proxy & we…",
                "starCount": "141",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "kasmweb/nginx",
                "description": "An Nginx image based off nginx:alpine and in…",
                "starCount": "9",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "rancher/nginx",
                "description": "",
                "starCount": "4",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "linuxserver/nginx",
                "description": "An Nginx container, brought to you by LinuxS…",
                "starCount": "236",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "dtagdevsec/nginx",
                "description": "T-Pot Nginx",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "paketobuildpacks/nginx",
                "description": "",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "vmware/nginx",
                "description": "",
                "starCount": "3",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "gluufederation/nginx",
                "description": " A customized NGINX image containing a consu…",
                "starCount": "1",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "cleanstart/nginx",
                "description": "Secure by Design, Built for Speed, Hardened …",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "antrea/nginx",
                "description": "Nginx server used for Antrea e2e testing",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "activestate/nginx",
                "description": "ActiveState's customizable, low-to-no vulner…",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "intel/nginx",
                "description": "",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "docksal/nginx",
                "description": "Nginx service image for Docksal",
                "starCount": "1",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "geokrety/nginx",
                "description": "Our customized nginx image",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "circleci/nginx",
                "description": "This image is for internal use",
                "starCount": "2",
                "isOfficial": false,
                "isAutomated": false
            },
            {
                "name": "ilios/nginx",
                "description": "Nginx customized to run Ilios along with the…",
                "starCount": "0",
                "isOfficial": false,
                "isAutomated": false
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 获取 Docker 镜像加速站配置

GET /docker/mirror

读取当前 Docker daemon 的镜像加速站配置。成功时返回 daemon 配置内容，适合设置页展示当前 registry mirror。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "registryMirrors": null,
        "daemonJsonPath": "/etc/docker/daemon.json"
    }
}
```

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "registryMirrors": [
            "https://docker.m.daocloud.cn"
        ],
        "daemonJsonPath": "/etc/docker/daemon.json",
        "rawConfig": {
            "registry-mirrors": [
                "https://docker.m.daocloud.cn"
            ]
        }
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 设置 Docker 镜像加速站

POST /docker/mirror

设置 Docker daemon 的镜像加速站列表。当前接口通过查询参数 `mirrors` 接收 JSON 字符串数组，例如 `["https://docker.m.daocloud.cn"]`。服务端会构造 daemon 配置并通过特权代理写入，成功时返回配置结果。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|mirrors|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "daemonJsonPath": "/etc/docker/daemon.json",
        "isSet": true,
        "isRestarted": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# Database 接口

## GET 查询数据库安装信息

GET /database/install/{databaseType}

查询指定数据库类型的安装信息。路径参数 `databaseType` 由底层数据库工具解析，常见取值为 `mysql`。成功时返回安装检测结果；若系统中未安装对应数据库或检测失败，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|databaseType|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "isInstalled": true,
        "version": "8.4.9",
        "databaseType": "mysql"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询数据库运行状态

GET /database/status/{databaseType}

查询指定数据库类型的运行状态。路径参数 `databaseType` 通常使用 `mysql`。成功时返回数据库服务当前状态、可用性等结构化信息；若服务不存在或读取失败，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|databaseType|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "isRunning": true,
        "databaseType": "mysql",
        "currentConnections": null,
        "slowQueryCount": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 测试 MySQL 连接

POST /database/mysql/test-connection

测试到目标 MySQL 实例的连接能力。请求体包含 `host`、`port`、`username`、`password`。该接口只做连通性验证，不会创建数据库或写入数据；成功时返回底层测试结果，失败时会区分权限不足、服务不可达或执行错误。

> Body 请求参数

```json
{
  "host": "127.0.0.1",
  "port": 3306,
  "username": "test",
  "password": "test123456"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» host|body|string| 是 ||none|
|» port|body|integer| 是 ||none|
|» username|body|string| 是 ||none|
|» password|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "isConnectable": true,
        "host": "127.0.0.1",
        "port": 3306,
        "username": "test"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 创建 MySQL 数据库

POST /database/mysql/database

创建新的 MySQL 数据库。请求体只包含 `dbName`，名称必须匹配代码中的正则限制：以字母或下划线开头，后续仅允许字母、数字和下划线。服务端通过特权代理执行建库操作，成功时返回建库结果。

> Body 请求参数

```json
{
  "dbName": "myapp"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» dbName|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "dbName": "myapp",
        "charset": "utf8mb4",
        "isCreated": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 创建 MySQL 用户并授权

POST /database/mysql/user

创建新的 MySQL 用户并为指定数据库授权。请求体包含 `dbName`、`username`、`password`，其中库名和用户名都需要满足命名规则。服务端通过特权代理执行用户创建与授权，成功时返回执行结果。

> Body 请求参数

```json
{
  "dbName": "myapp",
  "username": "myapptest",
  "password": "test123456"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» dbName|body|string| 是 ||none|
|» username|body|string| 是 ||none|
|» password|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "dbName": "myapp",
        "username": "myapptest",
        "host": "localhost",
        "privileges": "ALL PRIVILEGES",
        "isGranted": true,
        "isCreated": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 获取 MySQL 数据库列表

GET /database/mysql/databases

获取当前 MySQL 实例中的数据库名列表。成功时响应 `data` 形如 `{ databaseType: "mysql", databases: [...] }`，适合数据库选择框或管理页展示。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "databaseType": "mysql",
        "databases": [
            "information_schema",
            "myapp",
            "mysql",
            "performance_schema",
            "sys"
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# nginx

## GET 查询 Nginx 安装信息

GET /nginx/install

查询 Nginx 是否已安装以及安装相关信息。成功时返回底层工具检测结果；若系统缺少 Nginx 或读取失败，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "isInstalled": true,
        "version": "1.28.3",
        "configPath": "/etc/nginx/nginx.conf"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询 Nginx 运行状态

GET /nginx/status

查询 Nginx 当前运行状态。成功时返回服务状态相关信息；若 Nginx 未安装、服务不可用或读取失败，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "isRunning": true,
        "workerProcessCount": 20,
        "activeConnections": null,
        "requestsPerSecond": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 测试 Nginx 配置

POST /nginx/test-config

执行 Nginx 配置语法检查，相当于后端通过特权代理执行 `nginx -t`。该接口不会重载服务，只返回配置是否合法及底层检查输出，适合在保存站点配置前先做校验。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "isValid": true,
        "stdout": "",
        "stderr": "nginx: the configuration file /etc/nginx/nginx.conf syntax is ok\nnginx: configuration file /etc/nginx/nginx.conf test is successful"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 重载 Nginx

POST /nginx/reload

重载 Nginx 配置，使新的配置生效。该接口会通过特权代理执行 reload，适合在配置已通过语法校验后调用。若当前配置错误或权限不足，会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "serviceName": "nginx",
        "action": "reload",
        "isReloaded": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 重启 Nginx

POST /nginx/restart

重启 Nginx 服务。与 reload 相比，重启会完整停止并重新启动服务，适用于需要彻底刷新状态的场景。调用失败时会返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "serviceName": "nginx",
        "action": "restart",
        "isRestarted": true,
        "currentStatus": "active"
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 获取站点列表

GET /nginx/sites

获取当前 Nginx 站点列表。响应 `data` 为 `{ total, list }`，其中每一项来自底层站点扫描结果，适合站点管理页展示启用中的静态站点或反向代理站点。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 1,
        "list": [
            {
                "configName": "example.com.conf",
                "configPath": "/etc/nginx/sites-enabled/example.com.conf",
                "domain": "example.com",
                "listen": "80",
                "mode": "static",
                "rootPath": "/var/www/example.com",
                "proxyPass": null,
                "isEnabled": true
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 创建站点

POST /nginx/site

创建新的 Nginx 站点。请求体包含 `domain`、`mode`、`listenPort`，以及根据模式选择的字段：`mode=static` 时必须提供 `rootPath`；`mode=reverse_proxy` 时必须提供 `proxyPass`，若同时提供 `proxyPort` 则后端会自动拼接成完整上游地址，协议由 `proxyProtocol` 控制。成功时会生成配置、写入站点文件并自动 reload Nginx。

> Body 请求参数

```json
{
  "domain": "example.com",
  "mode": "static",
  "listenPort": 80,
  "rootPath": "/var/www/example.com",
  "proxyPass": null,
  "proxyPort": null,
  "proxyProtocol": "http"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» domain|body|string| 是 ||none|
|» mode|body|string| 是 ||none|
|» listenPort|body|integer| 是 ||none|
|» rootPath|body|string| 是 ||none|
|» proxyPass|body|null| 是 ||none|
|» proxyPort|body|null| 是 ||none|
|» proxyProtocol|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "domain": "example.com",
        "mode": "static",
        "listenPort": 80,
        "configPath": "/etc/nginx/sites-available/example.com.conf",
        "enabledPath": "/etc/nginx/sites-available/example.com.conf",
        "rootPath": "/var/www/example.com",
        "proxyPass": null,
        "isEnabled": true,
        "isReloaded": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 删除站点

DELETE /nginx/site/{configName}

删除指定站点配置。路径参数 `configName` 用于定位站点配置文件，服务端会通过特权代理删除配置并完成 reload。成功时返回被删除的配置路径及删除结果。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|configName|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "configName": "example.com.conf",
        "configPath": "/etc/nginx/sites-available/example.com.conf",
        "isDeleted": true,
        "isReloaded": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 申请 SSL 证书

POST /nginx/ssl/apply

为指定域名申请 SSL 证书。请求体包含 `domain` 和 `email`。服务端会先读取现有站点配置并解析 `webroot`，再通过特权代理执行证书申请流程。成功时返回证书申请结果；若站点配置缺失、解析失败或证书申请失败，会返回业务错误。

> Body 请求参数

```json
{
  "domain": "example.com",
  "email": "admin@example.com"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» domain|body|string| 是 ||none|
|» email|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 0,
    "msg": "申请 SSL 证书失败",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 配置 SSL

POST /nginx/ssl/config

为指定域名写入 HTTPS/SSL 配置。请求体包含 `domain`、`certPath`、`keyPath`。服务端会基于现有站点配置生成包含证书路径的 HTTPS 配置，并通过特权代理保存与应用。适用于证书已存在、只需要挂载到站点的场景。

> Body 请求参数

```json
{
  "domain": "example.com",
  "certPath": "/etc/letsencrypt/live/example.com/fullchain.pem",
  "keyPath": "/etc/letsencrypt/live/example.com/privkey.pem"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» domain|body|string| 是 ||none|
|» certPath|body|string| 是 ||none|
|» keyPath|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 续期 SSL 证书

POST /nginx/ssl/renew

为指定域名续期 SSL 证书。请求体包含 `domain`。服务端会通过特权代理执行续期流程，成功时返回续期结果。

> Body 请求参数

```json
{
  "domain": "example.com"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» domain|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 读取站点配置

GET /nginx/site/{domain}

读取指定域名站点的配置。路径参数 `domain` 用于定位站点配置文件，成功时返回配置原文及解析后的结构化字段，供前端编辑器或详情页展示。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|domain|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "domain": "example.com",
        "configPath": "/etc/nginx/sites-enabled/example.com.conf",
        "content": "server {\n    listen 80;\n    server_name example.com;\n    root /var/www/example.com;\n    index index.html;\n    location / {\n        try_files $uri $uri/ =404;\n    }\n}",
        "parsed": {
            "serverName": "example.com",
            "listen": "80",
            "root": "/var/www/example.com",
            "proxyPass": null,
            "sslCertPath": null,
            "sslKeyPath": null
        }
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» domain|string|true|none||none|
|»» configPath|string|true|none||none|
|»» content|string|true|none||none|
|»» parsed|object|true|none||none|
|»»» serverName|string|true|none||none|
|»»» listen|string|true|none||none|
|»»» root|string|true|none||none|
|»»» proxyPass|null|true|none||none|
|»»» sslCertPath|null|true|none||none|
|»»» sslKeyPath|null|true|none||none|

## PUT 上传并应用站点配置

PUT /nginx/site/{domain}

原子化更新指定域名的 Nginx 站点配置。路径参数 `domain` 指定目标站点，请求体中的 `content` 必须是完整配置原文。服务端会执行“写入临时内容 -> `nginx -t` 校验 -> 失败回滚 / 成功保存并 reload”流程，因此比普通文本覆盖更安全。成功时返回站点配置保存结果。

> Body 请求参数

```json
{
  "content": "server {\n    listen 80;\n    server_name example.com;\n    root /var/www/example.com;\n    index index.html;\n    location / {\n        try_files $uri $uri/ =404;\n    }\n}"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|domain|path|string| 是 ||none|
|body|body|object| 是 ||none|
|» content|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "targetPath": "/etc/nginx/sites-enabled/example.com.conf",
        "isSaved": true,
        "isReloaded": true
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# agent

## POST 创建 Agent 会话

POST /agent/sessions

 请求体 AgentSessionCreate 

 参数         类型   必填 默认值          说明
 ──────────── ────── ──── ─────────────── ──────────────────────────────────────
 title        string 否   "新 Agent 会话" 会话标题，1-100 字符
 mode         string 否   "agent"         运行模式（见下方）
 profileId    int    否   null            LLM Profile ID，不传则使用默认 Profile
 toolSource   string 否   "current_mcp"   工具来源模式："current_mcp" 或 "stdio"
 safetyPolicy string 否   "default"       安全策略（见下方）
 mcpServers   array  否   null            仅 toolSource="stdio" 时有效

 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

 mode — 四种运行模式 

 值            名称       行为
 ───────────── ────────── ───────────────────────────────────────────────────────
 "agent"       标准 Agent 默认。低风险自动执行，中高风险需用户审批
 "read_only"   只读       只能使用风险等级 read_only 的工具，禁写
 "plan"        计划       可查询诊断，生成执行方案但不执行，等待用户批准
 "break_glass" 紧急       跳过审批降级，所有操作强制审计日志，回复标明 [紧急模式]

 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

 toolSource — 工具来源（两种） 

 "current_mcp"（默认） 

加载项目内置工具集，共 53 个工具，涵盖：

 · 系统观测：CPU、内存、磁盘、网络、进程、Docker、Nginx、systemd
 · 文件操作：读写、搜索、替换、补丁
 · Git/项目：状态、diff、变更文件、项目命令检测
 · 命令执行：argv 风格命令、shell 命令
 · 安全相关：防火墙端口管理（通过特权 Agent）

不接收  mcpServers  参数。如果传了会拒绝。

 "stdio" 

加载外部 stdio MCP 服务端的工具集。

mcpServers 自动发现规则：

 1. 如果请求中显式传了  mcpServers  → 使用前端传入的
 2. 如果没传 → 自动从  pyproject.toml  读取  [tool.ndlmpanel-agent.mcp-servers] 

项目内置了两个预配置的 MCP 服务端：

 server 名      入口                          工具集
 ────────────── ───────────────────────────── ───────────────────────────────────────────
 ndlmpanel-mcp  python -m ndlmpanel_agent.mcp 系统观测、Docker、Nginx、防火墙等 ops 工具
 agent-core-mcp python -m agent.agent_mcp     文件读写编辑、搜索、Git、命令执行等编码工具

如果前端显式传  mcpServers ，格式如下：

 McpServerSpec  每项：

 字段    类型     必填 说明
 ─────── ──────── ──── ────────────────────────────────────────────
 name    string   是   唯一标识名，冲突时报错
 command string[] 是   argv 格式命令，如 ["python", "-m", "my_mcp"]
 cwd     string   否   工作目录

校验规则：

 ·  stdio  + 空  mcpServers  → 拒绝
 · 两个 server 暴露同名工具 → 拒绝（报错含冲突名 + server 名）

 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

 safetyPolicy — 安全策略 

值      : "default"
名称    : 默认
行为差异: 平衡安全与可用性。拦截 rm -rf / / dd of=/dev / fork 炸弹等危险命令；写操作需审批

值      : "strict"
名称    : 严格
行为差异: 用于生产/高风险环境。阈值更严：safe ≤ 10（默认是 20），拦截 rm -rf（所有路径）、shutdown、chmod 777、chown root 等；require_approval 为 "all_write"（所有
          写操作需审批）

两种策略均有的保护：

 · 受保护路径（ /etc/shadow 、 /boot 、 /proc 、 /sys  等）不可写
 · 危险模式匹配（ curl \| bash 、 sudo su  等）直接拦截
 · 输出长度上限控制

 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

 profileId — LLM Profile 

不传则自动使用默认 Profile。可通过以下接口管理：

 ·  GET /agent/llm/profiles  — 查看所有 Profile
 ·  GET /agent/llm/profiles/default  — 查看当前默认
 ·  PUT /agent/llm/profiles/{profileId}/default  — 设置默认

每个 Profile 包含：提供商（DeepSeek/Qwen/OpenAI Compatible）、模型名、maxTokens、temperature、重试策略等。

 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

 完整示例 

最简 — current_mcp + 默认 Profile：

 json
 POST /agent/sessions 
 {} 

最简 — stdio + 自动发现（推荐）：

 json
 POST /agent/sessions 
 { 
   "toolSource": "stdio" 
 } 

完整参数：

 json
 POST /agent/sessions 
 { 
   "title": "生产环境巡检", 
   "mode": "read_only", 
   "profileId": 2, 
   "toolSource": "current_mcp", 
   "safetyPolicy": "strict" 
 } 

自定义 stdio server：

 json
 POST /agent/sessions 
 { 
   "title": "自定义 MCP", 
   "toolSource": "stdio", 
   "mcpServers": [ 
     { 
       "name": "my-tools", 
       "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/data"] 
     } 
   ] 
 } 

 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

 响应 AgentSessionResponse 

 字段         类型      说明
 ──────────── ───────── ─────────────────────────────────────────────────
 sessionId    string    会话 ID，WebSocket 连接用
 title        string    会话标题
 mode         string    运行模式
 status       string    "idle" / "running" / "waiting_approval" / "error"
 profileId    int?      使用的 LLM Profile ID
 toolSource   string    实际生效的工具来源
 safetyPolicy string    安全策略
 mcpServers   array?    如果是 stdio 模式，列出实际运行的 server 配置
 summary      string?   会话摘要
 lastError    string?   最后一次错误信息
 createdAt    datetime  创建时间
 updatedAt    datetime  最后更新时间
 finishedAt   datetime? 完成时间

> Body 请求参数

```json
{
    "title": "磁盘异常排查",
    "mode": "agent",
    "profileId": 2,
    "toolSource": "current_mcp",
    "safetyPolicy": "default"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» title|body|string| 是 ||none|
|» mode|body|string| 是 ||none|
|» profileId|body|integer| 是 ||none|
|» toolSource|body|string| 是 ||none|
|» safetyPolicy|body|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "sessionId": "sess_e6d9702d7b61",
        "title": "磁盘异常排查",
        "mode": "agent",
        "status": "idle",
        "profileId": 2,
        "toolSource": "current_mcp",
        "safetyPolicy": "default",
        "summary": null,
        "lastError": null,
        "createdAt": "2026-06-09T15:36:14.271472",
        "updatedAt": "2026-06-09T15:36:14.271474",
        "finishedAt": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询 Agent 会话列表

GET /agent/sessions

查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | integer | 否 | 页码，默认 `1` |
| pageSize | integer | 否 | 每页数量，默认 `20`，最大 `200` |
| status | string | 否 | 按状态过滤 |
| keyword | string | 否 | 按标题模糊搜索 |

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "total": 1,
    "items": [
      {
        "sessionId": "sess_xxx",
        "title": "磁盘异常排查",
        "mode": "agent",
        "status": "idle",
        "profileId": 1,
        "toolSource": "current_mcp",
        "safetyPolicy": "default",
        "summary": null,
        "lastError": null,
        "createdAt": "2026-06-09T13:00:00",
        "updatedAt": "2026-06-09T13:05:00",
        "finishedAt": null
      }
    ]
  }
}
```

注意事项：

- 只查询当前登录用户自己的会话。
- `status` 可选值包括：`idle`、`running`、`waiting_approval`、`completed`、`cancelled`、`error`。
- 当前 WebSocket turn 正常结束后会将状态恢复为 `idle`，方便继续下一轮。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|page|query|string| 否 ||none|
|pageSize|query|string| 否 ||none|
|status|query|string| 否 ||none|
|keyword|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "total": 1,
        "items": [
            {
                "sessionId": "sess_e6d9702d7b61",
                "title": "磁盘异常排查",
                "mode": "agent",
                "status": "idle",
                "profileId": 2,
                "toolSource": "current_mcp",
                "safetyPolicy": "default",
                "summary": null,
                "lastError": null,
                "createdAt": "2026-06-09T15:36:14.271472",
                "updatedAt": "2026-06-09T15:36:14.271474",
                "finishedAt": null
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询单个 Agent 会话

GET /agent/sessions/{sessionId}

响应体同创建会话返回的 `data`。

注意事项：

- 只能查询当前登录用户自己的会话。
- session 不存在或不属于当前用户时，会返回参数错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "sessionId": "sess_e6d9702d7b61",
        "title": "磁盘异常排查",
        "mode": "agent",
        "status": "idle",
        "profileId": 2,
        "toolSource": "current_mcp",
        "safetyPolicy": "default",
        "summary": null,
        "lastError": null,
        "createdAt": "2026-06-09T15:36:14.271472",
        "updatedAt": "2026-06-09T15:36:14.271474",
        "finishedAt": null
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## DELETE 删除会话

DELETE /agent/sessions/{sessionId}

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

注意事项：

- 会同时删除该会话下的 `agent_messages`。
- 当前实现不会级联删除 `agent_trace_logs`，Trace 仍可保留审计用途。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询会话消息历史

GET /agent/sessions/{sessionId}/messages

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "total": 2,
    "items": [
      {
        "messageId": 1,
        "sessionId": "sess_xxx",
        "role": "user",
        "content": "帮我分析磁盘使用情况",
        "traceId": "trace_xxx",
        "roundIndex": 1,
        "metadata": null,
        "createdAt": "2026-06-09T13:01:00"
      },
      {
        "messageId": 2,
        "sessionId": "sess_xxx",
        "role": "assistant",
        "content": "磁盘使用情况如下...",
        "traceId": "trace_xxx",
        "roundIndex": 1,
        "metadata": null,
        "createdAt": "2026-06-09T13:01:10"
      }
    ]
  }
}
```

注意事项：

- 当前历史恢复只保存 `user` 和最终 `assistant` 文本。
- 工具结果不会原样作为跨轮上下文保存，避免 LLM tool message 格式错乱。
- `roundIndex` 表示对话轮次，同一轮用户消息和助手最终回复使用同一个 index。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询 Trace 原始事件

GET /agent/traces

查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| sessionId | string | 否 | 按 session 过滤 |
| traceId | string | 否 | 按 trace 过滤 |
| eventType | string | 否 | 按事件类型过滤 |
| limit | integer | 否 | 限制条数，默认 `100`，最大 `1000` |

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "total": 1,
    "items": [
      {
        "id": 1,
        "traceId": "trace_xxx",
        "sessionId": "sess_xxx",
        "eventType": "tool.result",
        "timestamp": 1780000000.0,
        "data": {
          "tool": "listDirectory",
          "output_len": 100
        },
        "entryHash": "abc123",
        "prevHash": null,
        "createdAt": "2026-06-09T13:00:00"
      }
    ]
  }
}
```

注意事项：

- `data` 字段数据库内以 JSON 字符串保存，API 返回时会解析为对象。
- 默认按最新事件倒序返回。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|query|string| 否 ||none|
|traceId|query|string| 否 ||none|
|eventType|query|string| 否 ||none|
|limit|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询 Session Timeline

GET /agent/traces/{sessionId}/timeline

```http
GET /agent/traces/{sessionId}/timeline?limit=200
```

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "total": 3,
    "items": [
      {
        "id": 1,
        "traceId": "trace_xxx",
        "sessionId": "sess_xxx",
        "eventType": "input.received",
        "stage": "接收指令",
        "timestamp": 1780000000.0,
        "data": {
          "input": "帮我看看磁盘"
        }
      }
    ]
  }
}
```

阶段映射：

| eventType | stage |
| --- | --- |
| input.received | 接收指令 |
| llm.request | 推理决策 |
| llm.response | 推理决策 |
| safety.check | 安全校验 |
| approval.requested | 人工审批 |
| approval.resolved | 人工审批 |
| tool.result | 执行结果 |
| injection.detected | 注入风险 |
| session.done | 闭环完成 |

注意事项：

- Timeline 按时间正序返回。
- 未在映射表中的事件，`stage` 会直接使用原始 `eventType`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|
|limit|query|string| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 查询 Session Trace Summary

GET /agent/traces/{sessionId}/summary

响应示例：

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "sessionId": "sess_xxx",
    "totalEvents": 10,
    "toolCalls": 2,
    "approvalCount": 1,
    "hasInjection": false,
    "traces": [
      "trace_xxx"
    ]
  }
}
```

注意事项：

- `toolCalls` 统计 `tool.result` 事件数量。
- `approvalCount` 统计 `approval.requested` 与 `approval.resolved`。
- `hasInjection=true` 表示该会话出现过 prompt injection 检测事件。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## PUT 工具来源切换

PUT /agent/sessions/{sessionId}/tool-source

**Request Body：**
```json
{
    "toolSource": "current_mcp" | "stdio",
    "mcpServers": [
        {
            "name": "server-name",
            "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
            "cwd": "/path/to/cwd"
        }
    ]
}
```

**Response：**
```json
{
    "code": 200,
    "data": {
        "sessionId": "sess_xxx",
        "toolSource": "stdio",
        "mcpServers": [...],
        "updatedAt": "2026-06-09T12:00:00"
    }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## PUT 模型切换

PUT /agent/sessions/{sessionId}/switch-model

**Request Body：**
```json
{
    "profileId": 2
}
```

**Response：**
```json
{
    "code": 200,
    "data": {
        "sessionId": "sess_xxx",
        "profileId": 2,
        "updatedAt": "2026-06-09T12:00:00"
    }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET Token 用量明细

GET /agent/sessions/{sessionId}/usage

**Response：**
```json
{
    "code": 200,
    "data": {
        "total": 3,
        "items": [
            {
                "id": 1,
                "sessionId": "sess_xxx",
                "model": "deepseek-chat",
                "inputTokens": 1500,
                "outputTokens": 320,
                "totalTokens": 1820,
                "inputCost": 0.00075,
                "outputCost": 0.00064,
                "totalCost": 0.00139,
                "createdAt": "2026-06-09T12:00:00"
            }
        ]
    }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": [
        {
            "id": 1,
            "sessionId": "sess_dd16ab5afedc",
            "traceId": "trace_5141326d157e4603",
            "model": "gemini-2.5-flash",
            "inputTokens": 6243,
            "outputTokens": 11,
            "totalTokens": 6254,
            "inputCost": 0.006243,
            "outputCost": 3.3e-05,
            "totalCost": 0.006276,
            "createdAt": "2026-06-09T23:26:57.701264"
        },
        {
            "id": 2,
            "sessionId": "sess_dd16ab5afedc",
            "traceId": "trace_9200d435016d41b9",
            "model": "deepseek-v4-flash",
            "inputTokens": 10985,
            "outputTokens": 299,
            "totalTokens": 11284,
            "inputCost": 0.001099,
            "outputCost": 0.00012,
            "totalCost": 0.001218,
            "createdAt": "2026-06-09T23:27:15.881350"
        },
        {
            "id": 3,
            "sessionId": "sess_dd16ab5afedc",
            "traceId": "trace_00d2793517074373",
            "model": "gpt-5.4-mini",
            "inputTokens": 4796,
            "outputTokens": 949,
            "totalTokens": 5745,
            "inputCost": 0.004796,
            "outputCost": 0.002847,
            "totalCost": 0.007643,
            "createdAt": "2026-06-09T23:36:00.492757"
        }
    ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|[object]|true|none||none|
|»» id|integer|true|none||none|
|»» sessionId|string|true|none||none|
|»» traceId|string|true|none||none|
|»» model|string|true|none||none|
|»» inputTokens|integer|true|none||none|
|»» outputTokens|integer|true|none||none|
|»» totalTokens|integer|true|none||none|
|»» inputCost|number|true|none||none|
|»» outputCost|number|true|none||none|
|»» totalCost|number|true|none||none|
|»» createdAt|string|true|none||none|

## GET 会话计费汇总

GET /agent/sessions/{sessionId}/billing

**Response：**
```json
{
    "code": 200,
    "data": {
        "sessionId": "sess_xxx",
        "totalInputTokens": 4500,
        "totalOutputTokens": 960,
        "totalTokens": 5460,
        "totalInputCost": 0.00225,
        "totalOutputCost": 0.00192,
        "totalCost": 0.00417,
        "callCount": 3
    }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||none|

> 返回示例

> 200 Response

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "sessionId": "sess_dd16ab5afedc",
        "totalInputTokens": 22024,
        "totalOutputTokens": 1259,
        "totalTokens": 23283,
        "totalInputCost": 0.012138,
        "totalOutputCost": 0.003,
        "totalCost": 0.015137,
        "callCount": 3
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» sessionId|string|true|none||none|
|»» totalInputTokens|integer|true|none||none|
|»» totalOutputTokens|integer|true|none||none|
|»» totalTokens|integer|true|none||none|
|»» totalInputCost|number|true|none||none|
|»» totalOutputCost|number|true|none||none|
|»» totalCost|number|true|none||none|
|»» callCount|integer|true|none||none|

# 日志管理

<a id="opIdgetAll_log_all_get"></a>

## GET 查询操作日志列表

GET /log/all

查询系统记录的操作日志列表。返回每条日志的函数名、请求路径、HTTP 方法、输入参数、返回值、用户 ID、客户端 IP、执行耗时、错误信息和操作时间。该接口当前不分页，会一次返回全部日志记录，适合后台日志页初始化或调试排查。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

# Agent

<a id="opIdmarkSessionRead_agent_sessions__sessionId__mark_read_put"></a>

## PUT 标记会话已读

PUT /agent/sessions/{sessionId}/mark-read

将会话状态从 `completed_unread` 标记为已读，并恢复为 `idle`。通常在前端打开会话详情、消除未读提示时调用。

请求说明：
- 需要登录 Cookie `accessToken`。
- 仅允许操作当前登录用户自己的会话。
- 无请求体，只使用路径参数 `sessionId`。

返回说明：
- 返回更新后的 `AgentSessionResponse`。
- 如果会话不存在或不属于当前用户，会返回参数错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 | Sessionid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdswitchAgentMode_agent_sessions__sessionId__mode_put"></a>

## PUT 切换 Agent 模式

PUT /agent/sessions/{sessionId}/mode

切换指定 Agent 会话的运行模式，既会持久化到数据库，也会立即对当前运行时生效，无需重建会话。

请求体：
```json
{
  "mode": "read_only"
}
```

`mode` 可选值：
- `read_only`：只读模式，只允许低风险只读工具。
- `plan`：规划模式，只生成方案，不直接执行。
- `agent`：标准模式，按默认安全策略执行。
- `break_glass`：紧急模式，允许更激进执行，但会被强制审计。

注意事项：
- 需要登录 Cookie `accessToken`。
- 仅允许操作当前登录用户自己的会话。
- 传入非法模式会返回参数错误。
- 返回更新后的 `AgentSessionResponse`。

> Body 请求参数

```json
{
  "mode": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 | Sessionid|none|
|body|body|[AgentModeSwitch](#schemaagentmodeswitch)| 是 | AgentModeSwitch|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

# 管理员特权审批

<a id="opIdget_code_admin_elevation_codes__code__get"></a>

## GET 查询特权审批码

GET /admin/elevation/codes/{code}

查询单个特权审批码详情，供本机 CLI 或运维审批页展示。

访问限制：
- 仅允许从 `127.0.0.1` / `::1` / `localhost` 发起请求。
- 必须携带 `Authorization: Bearer <token>`。
- Bearer Token 需与服务器 `NDLM_ADMIN_TOKEN_PATH`（默认 `/etc/nereus/admin_token`）中的内容一致。

返回内容通常包含：
- code 当前状态（如 `pending` / `approved` / `rejected`）
- sessionId、requestType、reason、commands、taskId 等审批上下文

如果特权码不存在，业务层会返回 `code=0` 和错误消息，而不是 404。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|code|path|string| 是 | Code|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdlist_pending_admin_elevation_pending_get"></a>

## GET 查询待审批特权码列表

GET /admin/elevation/pending

列出所有待审批的特权请求，主要供 `sudo nereus` 或管理员本机界面查看。

访问限制：
- 仅允许本机访问。
- 必须携带 `/etc/nereus/admin_token` 对应的 Bearer Token。

返回说明：
- `data` 为待审批 code 数组。
- 每项通常包含 code、sessionId、requestType、reason、创建时间、关联任务或命令摘要。
- 仅返回状态仍为 `pending` 的审批项。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

<a id="opIdapprove_code_admin_elevation_approve_post"></a>

## POST 批准特权请求

POST /admin/elevation/approve

批准一个待审批的特权码，并在需要时联动更新定时任务预授权状态。

请求体：
```json
{
  "code": "NGA7-K3X9",
  "approved_by": "admin"
}
```

关键行为：
- 仅允许本机访问，并要求 Bearer Token 鉴权。
- 普通特权请求会签发内部 token，允许 Agent 继续执行后续高权限操作。
- 如果 `request_type=scheduled_task_policy` 且存在 `taskId`，会同时把对应定时任务从 `pending_approval` 更新为 `active`，并注册调度器任务。
- 审批完成后会向关联 Agent 会话推送 WebSocket 事件 `elevation.resolved`，其中 `status=approved`。

响应字段重点：
- `status`：固定为 `approved`
- `request_type`、`code`、`token_id`、`session_id`
- 定时任务场景下还会返回 `taskId`、`max_ops`、`allowed_commands`

> Body 请求参数

```json
{}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 | Body|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdreject_code_admin_elevation_reject_post"></a>

## POST 拒绝特权请求

POST /admin/elevation/reject

拒绝一个待审批的特权码，并向前端/Agent 推送拒绝结果。

请求体：
```json
{
  "code": "NGA7-K3X9",
  "reason": "操作风险过高"
}
```

关键行为：
- 仅允许本机访问，并要求 Bearer Token 鉴权。
- 如果对应请求属于定时任务预授权（`request_type=scheduled_task_policy`），会把任务审批状态标记为 `rejected`，并移除调度器 job。
- 会向关联 Agent 会话推送 `elevation.resolved` 事件，其中 `status=rejected`。

响应字段重点：
- `status`：固定为 `rejected`
- `code`
- `request_type`
- `taskId`（若为定时任务审批）

> Body 请求参数

```json
{}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 | Body|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdrevoke_token_admin_elevation_revoke_post"></a>

## POST 吊销特权 Token

POST /admin/elevation/revoke

吊销一个已经签发的内部特权 token，使其后续不能再用于高权限操作。

请求体：
```json
{
  "token_id": "..."
}
```

访问限制：
- 仅允许本机访问。
- 必须使用 `/etc/nereus/admin_token` 对应的 Bearer Token。

返回说明：
- 成功时 `data.status=revoked`。
- 如果 `token_id` 不存在或已经过期，业务层会返回失败消息。

> Body 请求参数

```json
{}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 | Body|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdaudit_code_admin_elevation_audit__code__get"></a>

## GET 审计特权请求

GET /admin/elevation/audit/{code}

对一个待审批的特权码执行 AI/规则结合的安全审计，返回结构化风险报告，供 CLI 富文本展示。

访问限制：
- 仅允许本机访问。
- 必须使用 Bearer Token 鉴权。

审计逻辑：
- code 不存在时返回业务失败。
- code 状态不是 `pending` 时也不会继续审计。
- 若 `request_type=scheduled_task_policy`，不会读取命令脚本，而是返回一份针对预授权策略的中风险提示。
- 若存在 `script_path` 且文件可读，优先审计脚本内容；否则审计 `commands` 列表。
- 审计异常时会降级为规则扫描，并返回 `risk_level=MEDIUM` 的兜底报告。

返回重点：
- `data.code`
- `data.audit.risk_level`
- `data.audit.summary`
- `data.audit.findings`
- `data.audit.dangerous_commands`
- `data.audit.ai_advice`

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|code|path|string| 是 | Code|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdlist_history_admin_elevation_history_get"></a>

## GET 查询特权审批历史

GET /admin/elevation/history

查询历史审批记录，默认最多返回 50 条。

访问限制：
- 仅允许本机访问。
- 必须使用 Bearer Token 鉴权。

查询参数：
- `limit`：返回条数上限，默认 `50`。

返回说明：
- `data` 为历史记录数组。
- 通常用于排查某个 code 的审批流转、签发 token、批准/拒绝人和时间。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|limit|query|integer| 否 | Limit|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

# ScheduledTask

<a id="opIdcreateTask_scheduled_tasks_post"></a>

## POST 创建定时任务

POST /scheduled-tasks

创建一个新的定时任务。到达 `cronExpression` 指定时间后，后端会通过后台 Agent 执行 `taskDescription`。

请求体关键字段：
- `name`：任务名称，1-100 字符。
- `cronExpression`：5 段 crontab 表达式，例如 `0 3 * * *`。
- `taskDescription`：真正交给后台 Agent 执行的任务描述。
- `approvalPolicy`：可选。传入后任务不会立刻启用，而是进入 `pending_approval`，等待管理员在服务器侧批准。

`approvalPolicy` 支持的关键字段：
- `allowedTools`：允许自动执行的工具名数组。
- `allowedPaths` / `deniedPaths`：允许/拒绝的路径前缀。
- `allowedPrivilegedCommands`：允许的特权命令白名单。
- `ttlSeconds`：审批码有效期，默认 3600 秒。
- `maxRuns`：批准后的最大授权次数，默认 100。

状态流转：
- 不传 `approvalPolicy`：创建后直接为 `active`，并注册到调度器。
- 传 `approvalPolicy`：创建后为 `pending_approval`，响应中会返回 `approvalCode`。管理员批准后才会切换为 `active`。

> Body 请求参数

```json
{
  "name": "string",
  "cronExpression": "string",
  "taskDescription": "string",
  "approvalPolicy": {
    "allowedTools": [
      "string"
    ],
    "allowedPaths": [
      "string"
    ],
    "deniedPaths": [
      "string"
    ],
    "allowedPrivilegedCommands": [
      "string"
    ],
    "ttlSeconds": 3600,
    "maxRuns": 100
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|[ScheduledTaskCreate](#schemascheduledtaskcreate)| 是 | ScheduledTaskCreate|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdlistTasks_scheduled_tasks_get"></a>

## GET 查询定时任务列表

GET /scheduled-tasks

查询定时任务列表。

鉴权：
- 需要登录 Cookie `accessToken`。

查询参数：
- `status`：可按状态筛选，如 `active`、`paused`、`pending_approval`。
- `includeDeleted`：是否包含已软删除任务，默认 `false`。

返回说明：
- `data.total` 为数量。
- `data.items` 为 `ScheduledTaskResponse` 数组。
- 当前实现按系统范围查询，不再按当前用户过滤。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|status|query|any| 否 | Status|none|
|includeDeleted|query|boolean| 否 | Includedeleted|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdlistAllTasks_scheduled_tasks_all_get"></a>

## GET 查询全部定时任务

GET /scheduled-tasks/all

查询全部定时任务，默认包含已删除任务，适合后台管理页使用。

鉴权：
- 需要登录 Cookie `accessToken`。

与 `GET /scheduled-tasks` 的区别：
- 本接口 `includeDeleted` 默认值为 `true`。
- 常用于查看 `active`、`paused`、`pending_approval`、`deleted` 等全部状态。

查询参数：
- `status`：按状态过滤。
- `includeDeleted`：默认 `true`，可显式改为 `false`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|status|query|any| 否 | Status|none|
|includeDeleted|query|boolean| 否 | Includedeleted|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdlistPendingApprovalTasks_scheduled_tasks_pending_approval_get"></a>

## GET 查询待审批定时任务

GET /scheduled-tasks/pending-approval

返回所有仍处于 `pending_approval` 状态的定时任务。

鉴权：
- 需要登录 Cookie `accessToken`。

用途：
- 管理页集中展示等待 CLI/管理员批准的任务。
- 结合 `approvalCode`、`approvalStatus`、`approvalPolicy` 字段展示审批进度。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

<a id="opIdgetRun_scheduled_tasks_runs__runId__get"></a>

## GET 查询定时任务执行记录

GET /scheduled-tasks/runs/{runId}

根据执行记录 ID 查询单次定时任务运行结果。

路径参数：
- `runId`：执行记录 ID。

返回说明：
- 返回 `ScheduledTaskRunResponse`。
- 重点字段包括 `sessionId`、`status`、`startedAt`、`finishedAt`、`resultSummary`、`errorMessage`、`tokenUsage`。
- 如果 `sessionId` 不为空，可继续通过 Agent 会话、消息、Trace 接口追踪完整执行过程。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|runId|path|integer| 是 | Runid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdgetApproval_scheduled_tasks__taskId__approval_get"></a>

## GET 查询任务审批详情

GET /scheduled-tasks/{taskId}/approval

查询某个定时任务的审批信息。

鉴权：
- 需要登录 Cookie `accessToken`。

返回字段重点：
- `taskId`
- `status`
- `approvalPolicy`
- `approvalCode`
- `approvalStatus`
- `approvalApprovedAt`
- `approvalApprovedBy`
- `approvalTokenId`
- `approvalRejectedReason`

适用于前端展示 `sudo nereus approve <approvalCode>` 提示、审批结果和拒绝原因。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdreissueApproval_scheduled_tasks__taskId__approval_reissue_post"></a>

## POST 重新签发任务审批码

POST /scheduled-tasks/{taskId}/approval/reissue

为 `pending_approval` 状态的定时任务重新生成审批码。

鉴权：
- 需要登录 Cookie `accessToken`。

调用限制：
- 只有状态为 `pending_approval` 的任务可以调用。
- 任务必须存在 `approvalPolicy`，否则会返回业务错误。

关键行为：
- 旧的待审批 code 会失效。
- 会生成新的 `approvalCode` 并写回任务记录。
- 返回更新后的 `ScheduledTaskResponse`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdgetTask_scheduled_tasks__taskId__get"></a>

## GET 查询单个定时任务

GET /scheduled-tasks/{taskId}

查询单个定时任务详情。

鉴权：
- 需要登录 Cookie `accessToken`。

返回说明：
- 返回 `ScheduledTaskResponse`。
- 如果任务已软删除，当前实现会按“不存在”处理。
- 可结合 `nextRunAt`、`lastRunAt`、`approvalStatus` 等字段判断调度与审批状态。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdupdateTask_scheduled_tasks__taskId__put"></a>

## PUT 更新定时任务

PUT /scheduled-tasks/{taskId}

部分更新定时任务，`name`、`cronExpression`、`taskDescription`、`approvalPolicy` 均可按需传入。

鉴权：
- 需要登录 Cookie `accessToken`。

关键规则：
- 如果更新了 `cronExpression`，后端会重新校验 5 段 crontab 格式。
- 如果本次请求传入了非空 `approvalPolicy`，任务会重新进入 `pending_approval`，并清空此前审批结果、移除调度器 job，然后重新签发 `approvalCode`。
- 如果只是普通字段更新，后端会刷新调度器中的任务定义。
- 如果请求体为空，接口会直接返回当前任务对象。

> Body 请求参数

```json
{
  "name": "string",
  "cronExpression": "string",
  "taskDescription": "string",
  "approvalPolicy": {
    "allowedTools": [
      "string"
    ],
    "allowedPaths": [
      "string"
    ],
    "deniedPaths": [
      "string"
    ],
    "allowedPrivilegedCommands": [
      "string"
    ],
    "ttlSeconds": 3600,
    "maxRuns": 100
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|
|body|body|[ScheduledTaskUpdate](#schemascheduledtaskupdate)| 是 | ScheduledTaskUpdate|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIddeleteTask_scheduled_tasks__taskId__delete"></a>

## DELETE 删除定时任务

DELETE /scheduled-tasks/{taskId}

软删除指定定时任务。

鉴权：
- 需要登录 Cookie `accessToken`。

删除行为：
- 后端不会物理删除记录，而是把 `status` 置为 `deleted`。
- `nextRunAt` 会被清空。
- 调度器中的 job 会被移除。

成功时外层响应 `data` 为 `null`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdpauseTask_scheduled_tasks__taskId__pause_post"></a>

## POST 暂停定时任务

POST /scheduled-tasks/{taskId}/pause

暂停指定定时任务。

鉴权：
- 需要登录 Cookie `accessToken`。

执行效果：
- 将任务状态改为 `paused`。
- 清空 `nextRunAt`。
- 从调度器移除对应 job。
- 返回更新后的 `ScheduledTaskResponse`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdresumeTask_scheduled_tasks__taskId__resume_post"></a>

## POST 恢复定时任务

POST /scheduled-tasks/{taskId}/resume

恢复一个已暂停或可重新启用的定时任务。

鉴权：
- 需要登录 Cookie `accessToken`。

执行效果：
- 将任务状态置为 `active`。
- 重新注册调度器 job。
- 返回更新后的 `ScheduledTaskResponse`，其中通常会重新计算 `nextRunAt`。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdtriggerTask_scheduled_tasks__taskId__trigger_post"></a>

## POST 手动触发定时任务

POST /scheduled-tasks/{taskId}/trigger

立即手动执行一次指定定时任务，并等待本次后台 Agent 执行完成后返回。

鉴权：
- 需要登录 Cookie `accessToken`。

执行规则：
- `deleted` 状态任务不可执行。
- `pending_approval` 状态任务会直接返回业务错误，提示仍在等待 CLI 审批。
- 后端会先创建一条运行记录，再通过 `AgentGatewayService.createEphemeralRun(...)` 发起一次临时 Agent 会话。

返回说明：
- 返回 `ScheduledTaskRunResponse`。
- `sessionId` 不为空时，可继续通过 Agent 会话/消息/Trace 接口查看完整执行过程。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdlistRuns_scheduled_tasks__taskId__runs_get"></a>

## GET 查询任务运行历史

GET /scheduled-tasks/{taskId}/runs

查询指定定时任务最近的执行记录列表。

鉴权：
- 需要登录 Cookie `accessToken`。

查询参数：
- `limit`：返回条数上限，默认 `50`，最大 `200`。

返回说明：
- `data.total` 为返回记录数。
- `data.items` 为 `ScheduledTaskRunResponse` 数组。
- 每条记录都包含运行状态、开始/结束时间、摘要、错误信息、token 用量等信息。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 | Taskid|none|
|limit|query|integer| 否 | Limit|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

# Inspection

<a id="opIdlistReports_inspection_reports_get"></a>

## GET 查询巡检报告列表

GET /inspection/reports

分页查询自动巡检报告列表。

查询参数：
- `page`：页码，默认 `1`。
- `pageSize`：每页条数，默认 `20`，最大 `200`。

返回说明：
- `data.total` 为总数。
- `data.items` 为 `InspectionReportResponse` 数组。
- 每条报告包含 `status`、`summary`、`findings`、`durationMs`、`errorMessage`、`sessionId` 等字段。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|page|query|integer| 否 | Page|none|
|pageSize|query|integer| 否 | Pagesize|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdlatestReport_inspection_reports_latest_get"></a>

## GET 查询最新巡检报告

GET /inspection/reports/latest

返回最近一条巡检报告。

返回说明：
- 有报告时返回单个 `InspectionReportResponse`。
- 尚无巡检记录时，`data` 可能为 `null`。
- 可用于首页或告警卡片快速展示最近一次巡检结果。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

<a id="opIdgetReport_inspection_reports__reportId__get"></a>

## GET 查询单个巡检报告

GET /inspection/reports/{reportId}

根据报告 ID 查询完整巡检报告。

路径参数：
- `reportId`：巡检报告 ID。

返回说明：
- 返回 `InspectionReportResponse`。
- `fullReport` 为 Agent 原始完整报告文本。
- `findings` 为后端从报告尾部 JSON 中提取出的结构化问题列表。
- 不存在的报告会返回参数错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|reportId|path|integer| 是 | Reportid|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdtriggerInspection_inspection_trigger_post"></a>

## POST 手动触发巡检

POST /inspection/trigger

立即发起一次系统巡检，并等待后台 Agent 执行完成后返回本次巡检报告。

鉴权：
- 需要登录 Cookie `accessToken`。

执行逻辑：
- 后端会读取 `workspace/inspection.md` 作为巡检配置文档；若文件不存在，会使用默认兜底提示。
- 调用 `AgentGatewayService.createEphemeralRun(...)`，标题固定为“自动巡检”，并自动开启核心工具集。
- 完成后会保存 `summary`、`findings`、`fullReport`、`durationMs`、`errorMessage` 等数据。

返回说明：
- 返回新创建的 `InspectionReportResponse`。
- `sessionId` 不为空时，可继续通过 Agent 会话、消息、Trace 接口查看巡检执行细节。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

<a id="opIdgetConfig_inspection_config_get"></a>

## GET 查询巡检调度配置

GET /inspection/config

查询自动巡检当前的调度配置。

返回内容由调度器 `AgentScheduler` 提供，通常用于前端展示：
- 是否启用自动巡检
- 当前巡检间隔（分钟）
- 下一次计划执行时间等调度信息

本接口不要求用户登录。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

<a id="opIdupdateConfig_inspection_config_put"></a>

## PUT 更新巡检调度配置

PUT /inspection/config

更新自动巡检的执行间隔。

请求体：
```json
{
  "intervalMinutes": 30
}
```

规则说明：
- `intervalMinutes` 取值范围为 `1` 到 `1440`。
- 后端会调用调度器 `setInspectionInterval(...)` 立即生效。
- 成功后返回更新后的最新巡检配置。

本接口当前不要求用户登录。

> Body 请求参数

```json
{
  "intervalMinutes": 1
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|[InspectionConfigUpdate](#schemainspectionconfigupdate)| 是 | InspectionConfigUpdate|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

# 数据模型

<h2 id="tocS_AgentLlmProfileBatchCreate">AgentLlmProfileBatchCreate</h2>

<a id="schemaagentllmprofilebatchcreate"></a>
<a id="schema_AgentLlmProfileBatchCreate"></a>
<a id="tocSagentllmprofilebatchcreate"></a>
<a id="tocsagentllmprofilebatchcreate"></a>

```json
{
  "credentialId": 1,
  "models": [
    "string"
  ],
  "namePrefix": "string",
  "maxTokens": 4096,
  "contextWindow": 1048576,
  "temperature": 0.1,
  "retryCount": 3,
  "retryDelay": 2,
  "isDefaultFirst": false,
  "isActive": true,
  "description": "string"
}

```

AgentLlmProfileBatchCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|credentialId|integer|true|none|Credentialid|none|
|models|[string]|true|none|Models|none|
|namePrefix|any|false|none|Nameprefix|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|maxTokens|integer|false|none|Maxtokens|none|
|contextWindow|integer|false|none|Contextwindow|none|
|temperature|number|false|none|Temperature|none|
|retryCount|integer|false|none|Retrycount|none|
|retryDelay|number|false|none|Retrydelay|none|
|isDefaultFirst|boolean|false|none|Isdefaultfirst|none|
|isActive|boolean|false|none|Isactive|none|
|description|any|false|none|Description|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_AgentLlmProfileCreate">AgentLlmProfileCreate</h2>

<a id="schemaagentllmprofilecreate"></a>
<a id="schema_AgentLlmProfileCreate"></a>
<a id="tocSagentllmprofilecreate"></a>
<a id="tocsagentllmprofilecreate"></a>

```json
{
  "name": "string",
  "credentialId": 1,
  "model": "string",
  "maxTokens": 4096,
  "contextWindow": 1048576,
  "temperature": 0.1,
  "retryCount": 3,
  "retryDelay": 2,
  "isDefault": false,
  "isActive": true,
  "description": "string"
}

```

AgentLlmProfileCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|name|string|true|none|Name|none|
|credentialId|integer|true|none|Credentialid|none|
|model|string|true|none|Model|none|
|maxTokens|integer|false|none|Maxtokens|none|
|contextWindow|integer|false|none|Contextwindow|none|
|temperature|number|false|none|Temperature|none|
|retryCount|integer|false|none|Retrycount|none|
|retryDelay|number|false|none|Retrydelay|none|
|isDefault|boolean|false|none|Isdefault|none|
|isActive|boolean|false|none|Isactive|none|
|description|any|false|none|Description|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_AgentLlmProfileUpdate">AgentLlmProfileUpdate</h2>

<a id="schemaagentllmprofileupdate"></a>
<a id="schema_AgentLlmProfileUpdate"></a>
<a id="tocSagentllmprofileupdate"></a>
<a id="tocsagentllmprofileupdate"></a>

```json
{
  "name": "string",
  "credentialId": 1,
  "model": "string",
  "maxTokens": 1,
  "contextWindow": 1,
  "temperature": 2,
  "retryCount": 0,
  "retryDelay": 0,
  "isDefault": true,
  "isActive": true,
  "description": "string"
}

```

AgentLlmProfileUpdate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|name|any|false|none|Name|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|credentialId|any|false|none|Credentialid|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|model|any|false|none|Model|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|maxTokens|any|false|none|Maxtokens|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|contextWindow|any|false|none|Contextwindow|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|temperature|any|false|none|Temperature|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|retryCount|any|false|none|Retrycount|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|retryDelay|any|false|none|Retrydelay|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|isDefault|any|false|none|Isdefault|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|boolean|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|isActive|any|false|none|Isactive|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|boolean|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|description|any|false|none|Description|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_AgentModeSwitch">AgentModeSwitch</h2>

<a id="schemaagentmodeswitch"></a>
<a id="schema_AgentModeSwitch"></a>
<a id="tocSagentmodeswitch"></a>
<a id="tocsagentmodeswitch"></a>

```json
{
  "mode": "string"
}

```

AgentModeSwitch

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|mode|string|true|none|Mode|目标模式: read_only / plan / agent / break_glass|

<h2 id="tocS_AgentModelSwitch">AgentModelSwitch</h2>

<a id="schemaagentmodelswitch"></a>
<a id="schema_AgentModelSwitch"></a>
<a id="tocSagentmodelswitch"></a>
<a id="tocsagentmodelswitch"></a>

```json
{
  "profileId": 0
}

```

AgentModelSwitch

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|profileId|integer|true|none|Profileid|none|

<h2 id="tocS_AgentSessionCreate">AgentSessionCreate</h2>

<a id="schemaagentsessioncreate"></a>
<a id="schema_AgentSessionCreate"></a>
<a id="tocSagentsessioncreate"></a>
<a id="tocsagentsessioncreate"></a>

```json
{
  "title": "新 Agent 会话",
  "mode": "agent",
  "profileId": 1,
  "toolSource": "current_mcp",
  "safetyPolicy": "default",
  "mcpServers": [
    {
      "name": "string",
      "command": [
        "string"
      ],
      "cwd": "string"
    }
  ]
}

```

AgentSessionCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|title|string|false|none|Title|none|
|mode|string|false|none|Mode|none|
|profileId|any|false|none|Profileid|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|toolSource|string|false|none|Toolsource|none|
|safetyPolicy|string|false|none|Safetypolicy|none|
|mcpServers|any|false|none|Mcpservers|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|[[McpServerSpec](#schemamcpserverspec)]|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|toolSource|current_mcp|
|toolSource|stdio|

<h2 id="tocS_AgentToolSourceSwitch">AgentToolSourceSwitch</h2>

<a id="schemaagenttoolsourceswitch"></a>
<a id="schema_AgentToolSourceSwitch"></a>
<a id="tocSagenttoolsourceswitch"></a>
<a id="tocsagenttoolsourceswitch"></a>

```json
{
  "toolSource": "current_mcp",
  "mcpServers": [
    {
      "name": "string",
      "command": [
        "string"
      ],
      "cwd": "string"
    }
  ]
}

```

AgentToolSourceSwitch

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|toolSource|string|true|none|Toolsource|none|
|mcpServers|any|false|none|Mcpservers|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|[[McpServerSpec](#schemamcpserverspec)]|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|toolSource|current_mcp|
|toolSource|stdio|

<h2 id="tocS_AlertQuery">AlertQuery</h2>

<a id="schemaalertquery"></a>
<a id="schema_AlertQuery"></a>
<a id="tocSalertquery"></a>
<a id="tocsalertquery"></a>

```json
{
  "page": 0,
  "pageSize": 0,
  "excludeProcessed": false
}

```

AlertQuery

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|page|integer|true|none|Page|当前页码|
|pageSize|integer|true|none|Pagesize|每页记录数|
|excludeProcessed|boolean|false|none|Excludeprocessed|是否排除已处理的告警|

<h2 id="tocS_ApiCredentialCreate">ApiCredentialCreate</h2>

<a id="schemaapicredentialcreate"></a>
<a id="schema_ApiCredentialCreate"></a>
<a id="tocSapicredentialcreate"></a>
<a id="tocsapicredentialcreate"></a>

```json
{
  "name": "string",
  "provider": "OpenAI",
  "baseUrl": "string",
  "isActive": true,
  "description": "string",
  "quotaLimit": 0,
  "apiKey": "stringstri"
}

```

ApiCredentialCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|name|string|true|none|Name|凭证别名|
|provider|[ProviderEnum](#schemaproviderenum)|true|none||服务商类型|
|baseUrl|any|false|none|Baseurl|自定义请求地址|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|isActive|boolean|false|none|Isactive|是否启用|
|description|any|false|none|Description|备注说明|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|quotaLimit|any|false|none|Quotalimit|预算额度限制|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|apiKey|string|true|none|Apikey|完整的API Key|

<h2 id="tocS_ApiCredentialUpdate">ApiCredentialUpdate</h2>

<a id="schemaapicredentialupdate"></a>
<a id="schema_ApiCredentialUpdate"></a>
<a id="tocSapicredentialupdate"></a>
<a id="tocsapicredentialupdate"></a>

```json
{
  "credentialId": 1,
  "name": "string",
  "baseUrl": "string",
  "isActive": true,
  "description": "string",
  "quotaLimit": 0
}

```

ApiCredentialUpdate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|credentialId|integer|true|none|Credentialid|none|
|name|any|false|none|Name|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|baseUrl|any|false|none|Baseurl|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|isActive|any|false|none|Isactive|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|boolean|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|description|any|false|none|Description|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|quotaLimit|any|false|none|Quotalimit|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_ApplySslRequest">ApplySslRequest</h2>

<a id="schemaapplysslrequest"></a>
<a id="schema_ApplySslRequest"></a>
<a id="tocSapplysslrequest"></a>
<a id="tocsapplysslrequest"></a>

```json
{
  "domain": "string",
  "email": "string"
}

```

ApplySslRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|domain|string|true|none|Domain|域名|
|email|string|true|none|Email|邮箱|

<h2 id="tocS_AutoCleanRequest">AutoCleanRequest</h2>

<a id="schemaautocleanrequest"></a>
<a id="schema_AutoCleanRequest"></a>
<a id="tocSautocleanrequest"></a>
<a id="tocsautocleanrequest"></a>

```json
{
  "cpuThreshold": 90,
  "memoryThreshold": 80
}

```

AutoCleanRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|cpuThreshold|number|false|none|Cputhreshold|CPU占用阈值 (%)|
|memoryThreshold|number|false|none|Memorythreshold|内存占用阈值 (%)|

<h2 id="tocS_BatchDeletePathRequest">BatchDeletePathRequest</h2>

<a id="schemabatchdeletepathrequest"></a>
<a id="schema_BatchDeletePathRequest"></a>
<a id="tocSbatchdeletepathrequest"></a>
<a id="tocsbatchdeletepathrequest"></a>

```json
{
  "paths": [
    "string"
  ]
}

```

BatchDeletePathRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|paths|[string]|true|none|Paths|要删除的路径列表|

<h2 id="tocS_BatchKillProcessRequest">BatchKillProcessRequest</h2>

<a id="schemabatchkillprocessrequest"></a>
<a id="schema_BatchKillProcessRequest"></a>
<a id="tocSbatchkillprocessrequest"></a>
<a id="tocsbatchkillprocessrequest"></a>

```json
{
  "pids": [
    0
  ],
  "reason": "string"
}

```

BatchKillProcessRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|pids|[integer]|true|none|Pids|待杀死的PID列表|
|reason|any|false|none|Reason|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_Body_uploadFile_file_upload_post">Body_uploadFile_file_upload_post</h2>

<a id="schemabody_uploadfile_file_upload_post"></a>
<a id="schema_Body_uploadFile_file_upload_post"></a>
<a id="tocSbody_uploadfile_file_upload_post"></a>
<a id="tocsbody_uploadfile_file_upload_post"></a>

```json
{
  "destinationPath": "string",
  "file": "string"
}

```

Body_uploadFile_file_upload_post

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|destinationPath|string|true|none|Destinationpath|none|
|file|string|true|none|File|none|

<h2 id="tocS_ConfigSslRequest">ConfigSslRequest</h2>

<a id="schemaconfigsslrequest"></a>
<a id="schema_ConfigSslRequest"></a>
<a id="tocSconfigsslrequest"></a>
<a id="tocsconfigsslrequest"></a>

```json
{
  "domain": "string",
  "certPath": "string",
  "keyPath": "string"
}

```

ConfigSslRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|domain|string|true|none|Domain|域名|
|certPath|string|true|none|Certpath|证书路径|
|keyPath|string|true|none|Keypath|私钥路径|

<h2 id="tocS_CopyFileRequest">CopyFileRequest</h2>

<a id="schemacopyfilerequest"></a>
<a id="schema_CopyFileRequest"></a>
<a id="tocScopyfilerequest"></a>
<a id="tocscopyfilerequest"></a>

```json
{
  "sourcePath": "string",
  "destinationPath": "string"
}

```

CopyFileRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|sourcePath|string|true|none|Sourcepath|原文件路径|
|destinationPath|string|true|none|Destinationpath|新文件路径|

<h2 id="tocS_CreateDatabaseRequest">CreateDatabaseRequest</h2>

<a id="schemacreatedatabaserequest"></a>
<a id="schema_CreateDatabaseRequest"></a>
<a id="tocScreatedatabaserequest"></a>
<a id="tocscreatedatabaserequest"></a>

```json
{
  "dbName": "string"
}

```

CreateDatabaseRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|dbName|string|true|none|Dbname|数据库名称|

<h2 id="tocS_CreateFileRequest">CreateFileRequest</h2>

<a id="schemacreatefilerequest"></a>
<a id="schema_CreateFileRequest"></a>
<a id="tocScreatefilerequest"></a>
<a id="tocscreatefilerequest"></a>

```json
{
  "path": "string"
}

```

CreateFileRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|path|string|true|none|Path|文件路径|

<h2 id="tocS_CreateSiteRequest">CreateSiteRequest</h2>

<a id="schemacreatesiterequest"></a>
<a id="schema_CreateSiteRequest"></a>
<a id="tocScreatesiterequest"></a>
<a id="tocscreatesiterequest"></a>

```json
{
  "domain": "string",
  "mode": "string",
  "listenPort": 80,
  "rootPath": "string",
  "proxyPass": "string",
  "proxyPort": 1,
  "proxyProtocol": "http"
}

```

CreateSiteRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|domain|string|true|none|Domain|域名|
|mode|string|true|none|Mode|站点类型|
|listenPort|integer|false|none|Listenport|监听端口|
|rootPath|any|false|none|Rootpath|静态站点根目录|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|proxyPass|any|false|none|Proxypass|反代目标地址|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|proxyPort|any|false|none|Proxyport|反代目标端口|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|proxyProtocol|string|false|none|Proxyprotocol|反代协议|

<h2 id="tocS_CreateUserRequest">CreateUserRequest</h2>

<a id="schemacreateuserrequest"></a>
<a id="schema_CreateUserRequest"></a>
<a id="tocScreateuserrequest"></a>
<a id="tocscreateuserrequest"></a>

```json
{
  "dbName": "string",
  "username": "string",
  "password": "string"
}

```

CreateUserRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|dbName|string|true|none|Dbname|数据库名称|
|username|string|true|none|Username|用户名|
|password|string|true|none|Password|密码|

<h2 id="tocS_DeletePathRequest">DeletePathRequest</h2>

<a id="schemadeletepathrequest"></a>
<a id="schema_DeletePathRequest"></a>
<a id="tocSdeletepathrequest"></a>
<a id="tocsdeletepathrequest"></a>

```json
{
  "path": "string"
}

```

DeletePathRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|path|string|true|none|Path|要删除的路径|

<h2 id="tocS_GetFolderTreeRequest">GetFolderTreeRequest</h2>

<a id="schemagetfoldertreerequest"></a>
<a id="schema_GetFolderTreeRequest"></a>
<a id="tocSgetfoldertreerequest"></a>
<a id="tocsgetfoldertreerequest"></a>

```json
{
  "rootPath": "string",
  "depth": 1
}

```

GetFolderTreeRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|rootPath|string|true|none|Rootpath|根路径|
|depth|integer|false|none|Depth|递归深度|

<h2 id="tocS_HTTPValidationError">HTTPValidationError</h2>

<a id="schemahttpvalidationerror"></a>
<a id="schema_HTTPValidationError"></a>
<a id="tocShttpvalidationerror"></a>
<a id="tocshttpvalidationerror"></a>

```json
{
  "detail": [
    {
      "loc": [
        "string"
      ],
      "msg": "string",
      "type": "string",
      "input": null,
      "ctx": {}
    }
  ]
}

```

HTTPValidationError

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|

<h2 id="tocS_InspectionConfigUpdate">InspectionConfigUpdate</h2>

<a id="schemainspectionconfigupdate"></a>
<a id="schema_InspectionConfigUpdate"></a>
<a id="tocSinspectionconfigupdate"></a>
<a id="tocsinspectionconfigupdate"></a>

```json
{
  "intervalMinutes": 1
}

```

InspectionConfigUpdate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|intervalMinutes|integer|true|none|Intervalminutes|none|

<h2 id="tocS_KillProcessRequest">KillProcessRequest</h2>

<a id="schemakillprocessrequest"></a>
<a id="schema_KillProcessRequest"></a>
<a id="tocSkillprocessrequest"></a>
<a id="tocskillprocessrequest"></a>

```json
{
  "pid": 0,
  "reason": "string"
}

```

KillProcessRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|pid|integer|true|none|Pid|none|
|reason|any|false|none|Reason|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_ListDirectoryRequest">ListDirectoryRequest</h2>

<a id="schemalistdirectoryrequest"></a>
<a id="schema_ListDirectoryRequest"></a>
<a id="tocSlistdirectoryrequest"></a>
<a id="tocslistdirectoryrequest"></a>

```json
{
  "page": 0,
  "pageSize": 0,
  "path": "string"
}

```

ListDirectoryRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|page|integer|true|none|Page|当前页码|
|pageSize|integer|true|none|Pagesize|每页记录数|
|path|string|true|none|Path|目标路径|

<h2 id="tocS_McpServerSpec">McpServerSpec</h2>

<a id="schemamcpserverspec"></a>
<a id="schema_McpServerSpec"></a>
<a id="tocSmcpserverspec"></a>
<a id="tocsmcpserverspec"></a>

```json
{
  "name": "string",
  "command": [
    "string"
  ],
  "cwd": "string"
}

```

McpServerSpec

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|name|string|true|none|Name|none|
|command|[string]|true|none|Command|argv style command|
|cwd|any|false|none|Cwd|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_ModelPricingCreate">ModelPricingCreate</h2>

<a id="schemamodelpricingcreate"></a>
<a id="schema_ModelPricingCreate"></a>
<a id="tocSmodelpricingcreate"></a>
<a id="tocsmodelpricingcreate"></a>

```json
{
  "model": "string",
  "inputPrice": 1,
  "cachedInputPrice": 0.1,
  "outputPrice": 3,
  "multiplier": 1,
  "credentialId": 1
}

```

ModelPricingCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|model|string|true|none|Model|none|
|inputPrice|number|false|none|Inputprice|none|
|cachedInputPrice|number|false|none|Cachedinputprice|none|
|outputPrice|number|false|none|Outputprice|none|
|multiplier|number|false|none|Multiplier|none|
|credentialId|any|false|none|Credentialid|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_ModelPricingUpdate">ModelPricingUpdate</h2>

<a id="schemamodelpricingupdate"></a>
<a id="schema_ModelPricingUpdate"></a>
<a id="tocSmodelpricingupdate"></a>
<a id="tocsmodelpricingupdate"></a>

```json
{
  "model": "string",
  "inputPrice": 0,
  "cachedInputPrice": 0,
  "outputPrice": 0,
  "multiplier": 0,
  "credentialId": 1,
  "isActive": 1
}

```

ModelPricingUpdate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|model|any|false|none|Model|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|inputPrice|any|false|none|Inputprice|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|cachedInputPrice|any|false|none|Cachedinputprice|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|outputPrice|any|false|none|Outputprice|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|multiplier|any|false|none|Multiplier|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|number|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|credentialId|any|false|none|Credentialid|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|isActive|any|false|none|Isactive|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_MysqlConnectionTestRequest">MysqlConnectionTestRequest</h2>

<a id="schemamysqlconnectiontestrequest"></a>
<a id="schema_MysqlConnectionTestRequest"></a>
<a id="tocSmysqlconnectiontestrequest"></a>
<a id="tocsmysqlconnectiontestrequest"></a>

```json
{
  "host": "string",
  "port": 3306,
  "username": "string",
  "password": "string"
}

```

MysqlConnectionTestRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|host|string|true|none|Host|MySQL 主机地址|
|port|integer|false|none|Port|MySQL 端口|
|username|string|true|none|Username|MySQL 用户名|
|password|string|true|none|Password|MySQL 密码|

<h2 id="tocS_PageSearchRequest">PageSearchRequest</h2>

<a id="schemapagesearchrequest"></a>
<a id="schema_PageSearchRequest"></a>
<a id="tocSpagesearchrequest"></a>
<a id="tocspagesearchrequest"></a>

```json
{
  "page": 0,
  "pageSize": 0
}

```

PageSearchRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|page|integer|true|none|Page|当前页码|
|pageSize|integer|true|none|Pagesize|每页记录数|

<h2 id="tocS_PortRuleCreate">PortRuleCreate</h2>

<a id="schemaportrulecreate"></a>
<a id="schema_PortRuleCreate"></a>
<a id="tocSportrulecreate"></a>
<a id="tocsportrulecreate"></a>

```json
{
  "port": 1,
  "protocol": 1,
  "ipVersion": 4,
  "sourceIp": "string",
  "destinationIp": "string",
  "priority": 100,
  "action": 1
}

```

PortRuleCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|port|integer|true|none|Port|端口号|
|protocol|integer|true|none|Protocol|协议类型：0=UDP, 1=TCP|
|ipVersion|integer|false|none|Ipversion|IP版本：4=IPv4, 6=IPv6|
|sourceIp|string|true|none|Sourceip|来源IP，支持CIDR|
|destinationIp|string|true|none|Destinationip|目标IP，支持CIDR|
|priority|integer|false|none|Priority|规则优先级，默认100|
|action|integer|true|none|Action|动作：0=拒绝, 1=允许|

<h2 id="tocS_PortRuleDeleteRequest">PortRuleDeleteRequest</h2>

<a id="schemaportruledeleterequest"></a>
<a id="schema_PortRuleDeleteRequest"></a>
<a id="tocSportruledeleterequest"></a>
<a id="tocsportruledeleterequest"></a>

```json
{
  "port": 1,
  "protocol": 1,
  "ipVersion": 4,
  "sourceIp": "string",
  "destinationIp": "string"
}

```

PortRuleDeleteRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|port|integer|true|none|Port|端口号|
|protocol|integer|true|none|Protocol|协议类型：0=UDP, 1=TCP|
|ipVersion|any|false|none|Ipversion|IP版本：4=IPv4, 6=IPv6|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|sourceIp|any|false|none|Sourceip|来源IP，支持CIDR|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|destinationIp|any|false|none|Destinationip|目标IP，支持CIDR|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_ProviderEnum">ProviderEnum</h2>

<a id="schemaproviderenum"></a>
<a id="schema_ProviderEnum"></a>
<a id="tocSproviderenum"></a>
<a id="tocsproviderenum"></a>

```json
"OpenAI"

```

ProviderEnum

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|ProviderEnum|string|false|none|ProviderEnum|none|

#### 枚举值

|属性|值|
|---|---|
|ProviderEnum|OpenAI|
|ProviderEnum|Azure|
|ProviderEnum|Anthropic|
|ProviderEnum|Custom|

<h2 id="tocS_RenameOrMoveFileRequest">RenameOrMoveFileRequest</h2>

<a id="schemarenameormovefilerequest"></a>
<a id="schema_RenameOrMoveFileRequest"></a>
<a id="tocSrenameormovefilerequest"></a>
<a id="tocsrenameormovefilerequest"></a>

```json
{
  "sourcePath": "string",
  "destinationPath": "string"
}

```

RenameOrMoveFileRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|sourcePath|string|true|none|Sourcepath|原文件路径|
|destinationPath|string|true|none|Destinationpath|新文件路径|

<h2 id="tocS_RenewSslRequest">RenewSslRequest</h2>

<a id="schemarenewsslrequest"></a>
<a id="schema_RenewSslRequest"></a>
<a id="tocSrenewsslrequest"></a>
<a id="tocsrenewsslrequest"></a>

```json
{
  "domain": "string"
}

```

RenewSslRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|domain|string|true|none|Domain|域名|

<h2 id="tocS_ScheduledTaskApprovalPolicy">ScheduledTaskApprovalPolicy</h2>

<a id="schemascheduledtaskapprovalpolicy"></a>
<a id="schema_ScheduledTaskApprovalPolicy"></a>
<a id="tocSscheduledtaskapprovalpolicy"></a>
<a id="tocsscheduledtaskapprovalpolicy"></a>

```json
{
  "allowedTools": [
    "string"
  ],
  "allowedPaths": [
    "string"
  ],
  "deniedPaths": [
    "string"
  ],
  "allowedPrivilegedCommands": [
    "string"
  ],
  "ttlSeconds": 3600,
  "maxRuns": 100
}

```

ScheduledTaskApprovalPolicy

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|allowedTools|[string]|false|none|Allowedtools|none|
|allowedPaths|[string]|false|none|Allowedpaths|none|
|deniedPaths|[string]|false|none|Deniedpaths|none|
|allowedPrivilegedCommands|[string]|false|none|Allowedprivilegedcommands|none|
|ttlSeconds|integer|false|none|Ttlseconds|none|
|maxRuns|integer|false|none|Maxruns|none|

<h2 id="tocS_ScheduledTaskCreate">ScheduledTaskCreate</h2>

<a id="schemascheduledtaskcreate"></a>
<a id="schema_ScheduledTaskCreate"></a>
<a id="tocSscheduledtaskcreate"></a>
<a id="tocsscheduledtaskcreate"></a>

```json
{
  "name": "string",
  "cronExpression": "string",
  "taskDescription": "string",
  "approvalPolicy": {
    "allowedTools": [
      "string"
    ],
    "allowedPaths": [
      "string"
    ],
    "deniedPaths": [
      "string"
    ],
    "allowedPrivilegedCommands": [
      "string"
    ],
    "ttlSeconds": 3600,
    "maxRuns": 100
  }
}

```

ScheduledTaskCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|name|string|true|none|Name|none|
|cronExpression|string|true|none|Cronexpression|none|
|taskDescription|string|true|none|Taskdescription|none|
|approvalPolicy|[ScheduledTaskApprovalPolicy](#schemascheduledtaskapprovalpolicy)|false|none||none|

<h2 id="tocS_ScheduledTaskUpdate">ScheduledTaskUpdate</h2>

<a id="schemascheduledtaskupdate"></a>
<a id="schema_ScheduledTaskUpdate"></a>
<a id="tocSscheduledtaskupdate"></a>
<a id="tocsscheduledtaskupdate"></a>

```json
{
  "name": "string",
  "cronExpression": "string",
  "taskDescription": "string",
  "approvalPolicy": {
    "allowedTools": [
      "string"
    ],
    "allowedPaths": [
      "string"
    ],
    "deniedPaths": [
      "string"
    ],
    "allowedPrivilegedCommands": [
      "string"
    ],
    "ttlSeconds": 3600,
    "maxRuns": 100
  }
}

```

ScheduledTaskUpdate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|name|any|false|none|Name|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|cronExpression|any|false|none|Cronexpression|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|taskDescription|any|false|none|Taskdescription|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|approvalPolicy|[ScheduledTaskApprovalPolicy](#schemascheduledtaskapprovalpolicy)|false|none||none|

<h2 id="tocS_SearchFilesRequest">SearchFilesRequest</h2>

<a id="schemasearchfilesrequest"></a>
<a id="schema_SearchFilesRequest"></a>
<a id="tocSsearchfilesrequest"></a>
<a id="tocssearchfilesrequest"></a>

```json
{
  "path": "string",
  "expression": "string",
  "recursive": false,
  "ignoreCase": false,
  "invertMatch": false
}

```

SearchFilesRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|path|string|true|none|Path|搜索起始路径|
|expression|string|true|none|Expression|搜索表达式/关键字|
|recursive|boolean|false|none|Recursive|是否递归搜索子目录|
|ignoreCase|boolean|false|none|Ignorecase|是否忽略大小写|
|invertMatch|boolean|false|none|Invertmatch|是否取反匹配|

<h2 id="tocS_SecuritySwitchUpdate">SecuritySwitchUpdate</h2>

<a id="schemasecurityswitchupdate"></a>
<a id="schema_SecuritySwitchUpdate"></a>
<a id="tocSsecurityswitchupdate"></a>
<a id="tocssecurityswitchupdate"></a>

```json
{
  "firewallEnabled": true,
  "sshServiceEnabled": true
}

```

SecuritySwitchUpdate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|firewallEnabled|any|false|none|Firewallenabled|防火墙是否开启|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|boolean|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|sshServiceEnabled|any|false|none|Sshserviceenabled|SSH服务是否开启|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|boolean|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_SshConfigUpdate">SshConfigUpdate</h2>

<a id="schemasshconfigupdate"></a>
<a id="schema_SshConfigUpdate"></a>
<a id="tocSsshconfigupdate"></a>
<a id="tocssshconfigupdate"></a>

```json
{
  "port": 0,
  "permitRootLogin": "string",
  "passwordAuthentication": "string",
  "allowUsers": [
    "string"
  ],
  "allowGroups": [
    "string"
  ],
  "listenAddress": [
    "string"
  ],
  "protocol": 0,
  "loginGraceTime": 0,
  "maxAuthTries": 0
}

```

SshConfigUpdate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|port|any|false|none|Port|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|permitRootLogin|any|false|none|Permitrootlogin|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|passwordAuthentication|any|false|none|Passwordauthentication|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|allowUsers|any|false|none|Allowusers|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|[string]|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|allowGroups|any|false|none|Allowgroups|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|[string]|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|listenAddress|any|false|none|Listenaddress|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|[string]|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|protocol|any|false|none|Protocol|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|loginGraceTime|any|false|none|Logingracetime|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|maxAuthTries|any|false|none|Maxauthtries|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_TerminalLogSearchRequest">TerminalLogSearchRequest</h2>

<a id="schematerminallogsearchrequest"></a>
<a id="schema_TerminalLogSearchRequest"></a>
<a id="tocSterminallogsearchrequest"></a>
<a id="tocsterminallogsearchrequest"></a>

```json
{
  "page": 0,
  "pageSize": 0
}

```

TerminalLogSearchRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|page|integer|true|none|Page|当前页码|
|pageSize|integer|true|none|Pagesize|每页记录数|

<h2 id="tocS_UnzipFileRequest">UnzipFileRequest</h2>

<a id="schemaunzipfilerequest"></a>
<a id="schema_UnzipFileRequest"></a>
<a id="tocSunzipfilerequest"></a>
<a id="tocsunzipfilerequest"></a>

```json
{
  "dstPath": "string",
  "zipFilePath": "string"
}

```

UnzipFileRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|dstPath|string|true|none|Dstpath|解压目标路径|
|zipFilePath|any|false|none|Zipfilepath|压缩文件路径|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|null|false|none||none|

<h2 id="tocS_UpdateOwnerRequest">UpdateOwnerRequest</h2>

<a id="schemaupdateownerrequest"></a>
<a id="schema_UpdateOwnerRequest"></a>
<a id="tocSupdateownerrequest"></a>
<a id="tocsupdateownerrequest"></a>

```json
{
  "targetPath": "string",
  "owner": "string",
  "group": "string",
  "recursive": false
}

```

UpdateOwnerRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|targetPath|string|true|none|Targetpath|路径|
|owner|string|true|none|Owner|新所有者|
|group|string|true|none|Group|新组|
|recursive|boolean|false|none|Recursive|是否递归更新子目录|

<h2 id="tocS_UpdatePermissionsRequest">UpdatePermissionsRequest</h2>

<a id="schemaupdatepermissionsrequest"></a>
<a id="schema_UpdatePermissionsRequest"></a>
<a id="tocSupdatepermissionsrequest"></a>
<a id="tocsupdatepermissionsrequest"></a>

```json
{
  "path": "string",
  "permissions": "string"
}

```

UpdatePermissionsRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|path|string|true|none|Path|文件路径|
|permissions|string|true|none|Permissions|新权限值|

<h2 id="tocS_UpdateSiteConfigRequest">UpdateSiteConfigRequest</h2>

<a id="schemaupdatesiteconfigrequest"></a>
<a id="schema_UpdateSiteConfigRequest"></a>
<a id="tocSupdatesiteconfigrequest"></a>
<a id="tocsupdatesiteconfigrequest"></a>

```json
{
  "content": "string"
}

```

UpdateSiteConfigRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|content|string|true|none|Content|Nginx 配置原文（完整 server block）|

<h2 id="tocS_UserLoginRequest">UserLoginRequest</h2>

<a id="schemauserloginrequest"></a>
<a id="schema_UserLoginRequest"></a>
<a id="tocSuserloginrequest"></a>
<a id="tocsuserloginrequest"></a>

```json
{
  "account": "string",
  "hashedPassword": "string"
}

```

UserLoginRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|account|string|true|none|Account|用户名或邮箱|
|hashedPassword|string|true|none|Hashedpassword|密码|

<h2 id="tocS_ValidationError">ValidationError</h2>

<a id="schemavalidationerror"></a>
<a id="schema_ValidationError"></a>
<a id="tocSvalidationerror"></a>
<a id="tocsvalidationerror"></a>

```json
{
  "loc": [
    "string"
  ],
  "msg": "string",
  "type": "string",
  "input": null,
  "ctx": {}
}

```

ValidationError

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|loc|[anyOf]|true|none|Location|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|msg|string|true|none|Message|none|
|type|string|true|none|Error Type|none|
|input|any|false|none|Input|none|
|ctx|object|false|none|Context|none|

<h2 id="tocS_WriteTextRequest">WriteTextRequest</h2>

<a id="schemawritetextrequest"></a>
<a id="schema_WriteTextRequest"></a>
<a id="tocSwritetextrequest"></a>
<a id="tocswritetextrequest"></a>

```json
{
  "path": "string",
  "content": "string"
}

```

WriteTextRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|path|string|true|none|Path|文件路径|
|content|string|true|none|Content|要写入的内容|

<h2 id="tocS_ZipFileRequest">ZipFileRequest</h2>

<a id="schemazipfilerequest"></a>
<a id="schema_ZipFileRequest"></a>
<a id="tocSzipfilerequest"></a>
<a id="tocszipfilerequest"></a>

```json
{
  "path": "string"
}

```

ZipFileRequest

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|path|string|true|none|Path|文件路径|

