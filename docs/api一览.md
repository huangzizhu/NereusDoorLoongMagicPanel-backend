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

- HTTP Authentication, scheme: bearer

# 用户

## POST 登录

POST /user/login

使用用户名或邮箱及密码登录。成功时响应 data 返回 accessToken 和 refreshToken，并分别设置 HttpOnly Cookie：accessToken 有效期 5 分钟，refreshToken 有效期 7 天。

> Body 请求参数

```json
{
  "account": "string",
  "hashedPassword": "string"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» account|body|string| 是 |用户名或邮箱|
|» hashedPassword|body|string| 是 |密码字段|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "accessToken": "eyJ...",
    "refreshToken": "eyJ..."
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» accessToken|string|true|none||JWT access token，同时通过 HttpOnly Cookie 写入|
|»» refreshToken|string|true|none||刷新 token，同时通过 HttpOnly Cookie 写入|

## DELETE 登出

DELETE /user/logout

使用 refreshToken Cookie 注销服务端刷新令牌，并清除 accessToken 与 refreshToken Cookie。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|refreshToken|cookie|string| 是 |登录后由服务端写入的 HttpOnly Cookie，有效期 7 天。|
|accessToken|cookie|string| 否 |none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## POST 刷新访问令牌

POST /user/refresh

使用 refreshToken Cookie 签发新的 accessToken；成功后重新设置两个 Cookie。refreshToken 无效或过期时返回 401。

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
    "accessToken": "eyJ...",
    "refreshToken": "eyJ..."
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» accessToken|string|true|none||JWT access token，同时通过 HttpOnly Cookie 写入|
|»» refreshToken|string|true|none||刷新 token，同时通过 HttpOnly Cookie 写入|

# 系统信息

<a id="opIdgetSystemInfoHealthSSE_system_health_get"></a>

## GET 系统健康 SSE

GET /system/health

建立系统健康 SSE 长连接。需要 accessToken Cookie；成功响应为 text/event-stream，每约 2 秒发送一条 data: <json>\n\n，直到客户端断开。事件 JSON 包含 hostname、CPU/内存/磁盘使用率、healthScore/status，以及 CPU、内存、GPU、磁盘分区和网卡明细。

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
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|持续推送事件；每条记录形如 data: <json>\n\n|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» hostname|string|false|none||none|
|» cpuUsage|number|false|none||none|
|» memoryUsage|number|false|none||none|
|» diskUsage|number|false|none||none|
|» healthScore|integer|false|none||none|
|» status|integer|false|none||0 正常，1 警告，2 异常|
|» cpuInfo|object|false|none||none|
|»» modelName|string|false|none||none|
|»» coreCount|integer|false|none||none|
|»» usagePercent|number|false|none||none|
|»» load1Min|number|false|none||none|
|»» load5Min|number|false|none||none|
|»» load15Min|number|false|none||none|
|» memoryInfo|object|false|none||none|
|»» totalBytes|integer|false|none||none|
|»» usedBytes|integer|false|none||none|
|»» availableBytes|integer|false|none||none|
|»» usagePercent|number|false|none||none|
|»» swapTotalBytes|integer|false|none||none|
|»» swapUsedBytes|integer|false|none||none|
|»» swapUsagePercent|number|false|none||none|
|» gpuInfos|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|[string]|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» diskInfos|[object]|false|none||none|
|»» mountPoint|string|false|none||none|
|»» fileSystem|string|false|none||none|
|»» totalBytes|integer|false|none||none|
|»» usedBytes|integer|false|none||none|
|»» usagePercent|number|false|none||none|
|»» readBytesPerSec|number|false|none||none|
|»» writeBytesPerSec|number|false|none||none|
|» networkInfos|[object]|false|none||none|
|»» interfaceName|string|false|none||none|
|»» ipAddress|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» macAddress|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» recvBytesPerSec|number|false|none||none|
|»» sentBytesPerSec|number|false|none||none|
|»» totalRecvBytes|integer|false|none||none|
|»» totalSentBytes|integer|false|none||none|
|»» isUp|boolean|false|none||none|

<a id="opIdgetAllSystemAlerts_system_alerts_all_post"></a>

## POST 查询告警列表

POST /system/alerts/all

分页查询系统告警。需要 accessToken Cookie。请求体 page/pageSize（代码允许从 0 开始但建议 page>=1，pageSize 1..200）和 excludeProcessed；data 为 {total,items[]}，每项含 level(0/1/2)、message、status(0 未读/1 未处理/2 已处理)、id、createTime。

> Body 请求参数

```json
{
  "page": 1,
  "pageSize": 10,
  "excludeProcessed": false
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» page|body|integer| 是 |none|
|» pageSize|body|integer| 是 |none|
|» excludeProcessed|body|boolean| 是 |none|

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
        "level": 1,
        "message": "CPU 使用率超过 80%",
        "status": 0,
        "id": 1,
        "createTime": "2026-08-17T10:00:00Z"
      }
    ]
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» items|[object]|false|none||none|
|»»» level|integer|false|none||0 Info，1 Warning，2 Error|
|»»» message|string|false|none||none|
|»»» status|integer|false|none||0 未读，1 未处理，2 已处理|
|»»» id|integer|false|none||none|
|»»» createTime|string(date-time)|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdsetAlertsRead_system_alerts_id_read_put"></a>

## PUT 标记告警已读

PUT /system/alerts/{id}/read

将告警 status 更新为 1（未处理/已读）。需要 accessToken Cookie。id 为告警主键；不存在时返回 code=0 和明确提示；成功返回更新后的 AlertEvent。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|id|path|integer| 是 |告警主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "level": 1,
    "message": "CPU 使用率超过 80%",
    "status": 1,
    "id": 1,
    "createTime": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» level|integer|false|none||0 Info，1 Warning，2 Error|
|»» message|string|false|none||none|
|»» status|integer|false|none||0 未读，1 未处理，2 已处理|
|»» id|integer|false|none||none|
|»» createTime|string(date-time)|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdsetAlertsProcess_system_alerts_id_process_put"></a>

## PUT 标记告警已处理

PUT /system/alerts/{id}/process

将告警 status 更新为 2（已处理）。需要 accessToken Cookie。id 为告警主键；不存在时返回 code=0；成功返回更新后的 AlertEvent。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|id|path|integer| 是 |告警主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "level": 2,
    "message": "数据库连接失败",
    "status": 2,
    "id": 2,
    "createTime": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» level|integer|false|none||0 Info，1 Warning，2 Error|
|»» message|string|false|none||none|
|»» status|integer|false|none||0 未读，1 未处理，2 已处理|
|»» id|integer|false|none||none|
|»» createTime|string(date-time)|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

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

覆盖写入指定的文本文件。请求体必须提供 `path` 与 `content`；目标必须已存在、是普通文件且具有写入权限。服务端不会创建缺失文件，也不会对内容进行追加。成功时返回写入结果；路径不存在、目标不是文件或底层写入失败时返回业务错误。

> Body 请求参数

```json
{"path":"/tmp/example.txt","content":"hello world"}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|accessToken|cookie|string| 否 |none|
|refreshToken|cookie|string| 否 |none|
|body|body|object| 是 |none|
|» path|body|string| 是 |待写入的文本文件绝对路径|
|» content|body|string| 是 |要覆盖写入的完整文本内容|

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

## POST 创建 API 凭证

POST /config/apikey

创建 API 凭证。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

> Body 请求参数

```json
{
  "name": "string",
  "provider": "OpenAI",
  "baseUrl": "string",
  "apiKey": "stringstri",
  "isActive": true,
  "description": "string",
  "quotaLimit": 0
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» name|body|string| 是 ||凭证别名|
|» provider|body|string| 是 ||服务商|
|» baseUrl|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||自定义请求地址|
|»» *anonymous*|body|null| 否 ||none|
|» apiKey|body|string| 是 ||完整 API Key；仅创建时提交，响应永不返回原文|
|» isActive|body|boolean| 否 ||是否启用|
|» description|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||备注|
|»» *anonymous*|body|null| 否 ||none|
|» quotaLimit|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||预算额度限制|
|»» *anonymous*|body|null| 否 ||none|

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
    "credentialId": 3,
    "name": "OpenAI 生产",
    "provider": "OpenAI",
    "baseUrl": "https://api.openai.com/v1",
    "isActive": true,
    "description": "生产模型",
    "quotaLimit": 100,
    "maskedKey": "sk-***xyz",
    "usedQuota": 0,
    "expireAt": null,
    "lastUsedAt": null,
    "createTime": "2026-08-16T15:00:00",
    "updateTime": "2026-08-16T15:00:00"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» credentialId|integer|true|none||凭证 ID|
|»» name|string|true|none||凭证别名|
|»» provider|string|true|none||服务商|
|»» baseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||自定义请求地址|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isActive|boolean|true|none||是否启用|
|»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» quotaLimit|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|number|false|none||预算额度限制|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» maskedKey|string|true|none||仅返回脱敏 API Key；不会返回原始 apiKey|
|»» usedQuota|number|true|none||已使用额度|
|»» expireAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||过期时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastUsedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||最后使用时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createTime|string(date-time)|true|none||创建时间|
|»» updateTime|string(date-time)|true|none||更新时间|

#### 枚举值

|属性|值|
|---|---|
|provider|OpenAI|
|provider|Azure|
|provider|Anthropic|
|provider|Custom|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询 API 凭证列表

GET /config/apikey

查询 API 凭证列表。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» credentialId|integer|true|none||凭证 ID|
|»»» name|string|true|none||凭证别名|
|»»» provider|string|true|none||服务商|
|»»» baseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||自定义请求地址|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» isActive|boolean|true|none||是否启用|
|»»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» quotaLimit|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|number|false|none||预算额度限制|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» maskedKey|string|true|none||仅返回脱敏 API Key；不会返回原始 apiKey|
|»»» usedQuota|number|true|none||已使用额度|
|»»» expireAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||过期时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» lastUsedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||最后使用时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createTime|string(date-time)|true|none||创建时间|
|»»» updateTime|string(date-time)|true|none||更新时间|

#### 枚举值

|属性|值|
|---|---|
|provider|OpenAI|
|provider|Azure|
|provider|Anthropic|
|provider|Custom|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## PUT 更新 API 凭证

PUT /config/apikey

更新 API 凭证。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

> Body 请求参数

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

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» credentialId|body|integer| 是 ||待更新的凭证 ID|
|» name|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||新别名|
|»» *anonymous*|body|null| 否 ||none|
|» baseUrl|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||新 Base URL|
|»» *anonymous*|body|null| 否 ||none|
|» isActive|body|any| 否 ||none|
|»» *anonymous*|body|boolean| 否 ||启用状态|
|»» *anonymous*|body|null| 否 ||none|
|» description|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||备注|
|»» *anonymous*|body|null| 否 ||none|
|» quotaLimit|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||预算额度限制|
|»» *anonymous*|body|null| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» credentialId|integer|true|none||凭证 ID|
|»» name|string|true|none||凭证别名|
|»» provider|string|true|none||服务商|
|»» baseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||自定义请求地址|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isActive|boolean|true|none||是否启用|
|»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» quotaLimit|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|number|false|none||预算额度限制|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» maskedKey|string|true|none||仅返回脱敏 API Key；不会返回原始 apiKey|
|»» usedQuota|number|true|none||已使用额度|
|»» expireAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||过期时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastUsedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||最后使用时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createTime|string(date-time)|true|none||创建时间|
|»» updateTime|string(date-time)|true|none||更新时间|

#### 枚举值

|属性|值|
|---|---|
|provider|OpenAI|
|provider|Azure|
|provider|Anthropic|
|provider|Custom|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## DELETE 删除 API 凭证

DELETE /config/apikey/{credentialId}

删除 API 凭证。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|credentialId|path|integer| 是 ||凭证 ID。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» credentialId|integer|true|none||凭证 ID|
|»» name|string|true|none||凭证别名|
|»» provider|string|true|none||服务商|
|»» baseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||自定义请求地址|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isActive|boolean|true|none||是否启用|
|»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» quotaLimit|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|number|false|none||预算额度限制|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» maskedKey|string|true|none||仅返回脱敏 API Key；不会返回原始 apiKey|
|»» usedQuota|number|true|none||已使用额度|
|»» expireAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||过期时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastUsedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||最后使用时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createTime|string(date-time)|true|none||创建时间|
|»» updateTime|string(date-time)|true|none||更新时间|

#### 枚举值

|属性|值|
|---|---|
|provider|OpenAI|
|provider|Azure|
|provider|Anthropic|
|provider|Custom|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

# 设置/model

## GET 根据凭证拉取官方模型列表

GET /agent/llm/credentials/{credentialId}/models

对已启用且配置 Base URL 的凭证请求其 /models 端点，返回供应商模型列表。该请求会访问外部供应商，失败以业务错误返回。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|credentialId|path|integer| 是 ||凭证 ID。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» credentialId|integer|true|none||凭证 ID|
|»» credentialName|string|true|none||凭证名|
|»» credentialProvider|string|true|none||供应商|
|»» credentialBaseUrl|string|true|none||Base URL|
|»» sourceUrl|string|true|none||实际请求的 /models 地址|
|»» models|[object]|true|none||none|
|»»» id|string|true|none||模型 ID|
|»»» name|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||显示名|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» ownedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||拥有者|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» raw|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## POST 创建 LLM Profile

POST /agent/llm/profiles

创建 LLM Profile。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

> Body 请求参数

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
  "isDefault": false,
  "isActive": true,
  "description": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» name|body|string| 是 ||显示名称|
|» credentialId|body|integer| 是 ||关联凭证 ID|
|» model|body|string| 是 ||模型标识|
|» maxTokens|body|integer| 否 ||最大输出 token，默认 4096|
|» contextWindow|body|integer| 否 ||上下文窗口，默认 1048576|
|» temperature|body|number| 否 ||采样温度，默认 0.1|
|» retryCount|body|integer| 否 ||重试次数，默认 3|
|» retryDelay|body|number| 否 ||重试间隔秒数，默认 2|
|» isDefault|body|boolean| 否 ||是否设为默认|
|» isActive|body|boolean| 否 ||是否启用|
|» description|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||备注|
|»» *anonymous*|body|null| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» profileId|integer|true|none||Profile ID|
|»» name|string|true|none||显示名称|
|»» credentialId|integer|true|none||关联凭证 ID|
|»» model|string|true|none||模型标识|
|»» maxTokens|integer|true|none||单次最大输出 token，1 至 393216|
|»» contextWindow|integer|true|none||上下文窗口，1 至 10485760|
|»» temperature|number|true|none||采样温度，0 至 2|
|»» retryCount|integer|true|none||重试次数|
|»» retryDelay|number|true|none||重试间隔秒数|
|»» isDefault|boolean|true|none||是否默认 Profile|
|»» isActive|boolean|true|none||是否启用|
|»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createTime|string(date-time)|true|none||ISO 8601 创建时间|
|»» updateTime|string(date-time)|true|none||ISO 8601 更新时间|
|»» credentialName|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证名称|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» credentialProvider|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证供应商|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» credentialBaseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证 Base URL|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询 LLM Profile 列表

GET /agent/llm/profiles

查询 LLM Profile 列表。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» profileId|integer|true|none||Profile ID|
|»»» name|string|true|none||显示名称|
|»»» credentialId|integer|true|none||关联凭证 ID|
|»»» model|string|true|none||模型标识|
|»»» maxTokens|integer|true|none||单次最大输出 token，1 至 393216|
|»»» contextWindow|integer|true|none||上下文窗口，1 至 10485760|
|»»» temperature|number|true|none||采样温度，0 至 2|
|»»» retryCount|integer|true|none||重试次数|
|»»» retryDelay|number|true|none||重试间隔秒数|
|»»» isDefault|boolean|true|none||是否默认 Profile|
|»»» isActive|boolean|true|none||是否启用|
|»»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createTime|string(date-time)|true|none||ISO 8601 创建时间|
|»»» updateTime|string(date-time)|true|none||ISO 8601 更新时间|
|»»» credentialName|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证名称|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» credentialProvider|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证供应商|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» credentialBaseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证 Base URL|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询默认 LLM Profile

GET /agent/llm/profiles/default

查询默认 LLM Profile。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|object|false|none||none|
|»»» profileId|integer|true|none||Profile ID|
|»»» name|string|true|none||显示名称|
|»»» credentialId|integer|true|none||关联凭证 ID|
|»»» model|string|true|none||模型标识|
|»»» maxTokens|integer|true|none||单次最大输出 token，1 至 393216|
|»»» contextWindow|integer|true|none||上下文窗口，1 至 10485760|
|»»» temperature|number|true|none||采样温度，0 至 2|
|»»» retryCount|integer|true|none||重试次数|
|»»» retryDelay|number|true|none||重试间隔秒数|
|»»» isDefault|boolean|true|none||是否默认 Profile|
|»»» isActive|boolean|true|none||是否启用|
|»»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createTime|string(date-time)|true|none||ISO 8601 创建时间|
|»»» updateTime|string(date-time)|true|none||ISO 8601 更新时间|
|»»» credentialName|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证名称|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» credentialProvider|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证供应商|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» credentialBaseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证 Base URL|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## PUT 更新 LLM Profile

PUT /agent/llm/profiles/{profileId}

更新 LLM Profile。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

> Body 请求参数

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
  "isDefault": false,
  "isActive": true,
  "description": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|integer| 是 ||LLM Profile ID。|
|body|body|object| 是 ||none|
|» name|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||显示名称|
|»» *anonymous*|body|null| 否 ||none|
|» credentialId|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||关联凭证 ID|
|»» *anonymous*|body|null| 否 ||none|
|» model|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||模型标识|
|»» *anonymous*|body|null| 否 ||none|
|» maxTokens|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||最大输出 token，默认 4096|
|»» *anonymous*|body|null| 否 ||none|
|» contextWindow|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||上下文窗口，默认 1048576|
|»» *anonymous*|body|null| 否 ||none|
|» temperature|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||采样温度，默认 0.1|
|»» *anonymous*|body|null| 否 ||none|
|» retryCount|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||重试次数，默认 3|
|»» *anonymous*|body|null| 否 ||none|
|» retryDelay|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||重试间隔秒数，默认 2|
|»» *anonymous*|body|null| 否 ||none|
|» isDefault|body|any| 否 ||none|
|»» *anonymous*|body|boolean| 否 ||是否设为默认|
|»» *anonymous*|body|null| 否 ||none|
|» isActive|body|any| 否 ||none|
|»» *anonymous*|body|boolean| 否 ||是否启用|
|»» *anonymous*|body|null| 否 ||none|
|» description|body|any| 否 ||none|
|»» *anonymous*|body|any| 否 ||none|
|»»» *anonymous*|body|string| 否 ||备注|
|»»» *anonymous*|body|null| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» profileId|integer|true|none||Profile ID|
|»» name|string|true|none||显示名称|
|»» credentialId|integer|true|none||关联凭证 ID|
|»» model|string|true|none||模型标识|
|»» maxTokens|integer|true|none||单次最大输出 token，1 至 393216|
|»» contextWindow|integer|true|none||上下文窗口，1 至 10485760|
|»» temperature|number|true|none||采样温度，0 至 2|
|»» retryCount|integer|true|none||重试次数|
|»» retryDelay|number|true|none||重试间隔秒数|
|»» isDefault|boolean|true|none||是否默认 Profile|
|»» isActive|boolean|true|none||是否启用|
|»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createTime|string(date-time)|true|none||ISO 8601 创建时间|
|»» updateTime|string(date-time)|true|none||ISO 8601 更新时间|
|»» credentialName|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证名称|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» credentialProvider|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证供应商|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» credentialBaseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证 Base URL|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## DELETE 删除 LLM Profile

DELETE /agent/llm/profiles/{profileId}

删除 LLM Profile。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|integer| 是 ||LLM Profile ID。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## POST 批量创建 LLM Profile

POST /agent/llm/profiles/batch

使用一个凭证批量创建去重后的模型 Profile。models 会去除空白与重复项；isDefaultFirst 只影响第一条新 Profile。

> Body 请求参数

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

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» credentialId|body|integer| 是 ||关联凭证 ID|
|» models|body|[string]| 是 ||none|
|» namePrefix|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||批量名称前缀|
|»» *anonymous*|body|null| 否 ||none|
|» maxTokens|body|integer| 否 ||默认 4096|
|» contextWindow|body|integer| 否 ||默认 1048576|
|» temperature|body|number| 否 ||默认 0.1|
|» retryCount|body|integer| 否 ||默认 3|
|» retryDelay|body|number| 否 ||默认 2 秒|
|» isDefaultFirst|body|boolean| 否 ||第一个创建的 Profile 是否设为默认|
|» isActive|body|boolean| 否 ||是否启用|
|» description|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||备注|
|»» *anonymous*|body|null| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» profileId|integer|true|none||Profile ID|
|»»» name|string|true|none||显示名称|
|»»» credentialId|integer|true|none||关联凭证 ID|
|»»» model|string|true|none||模型标识|
|»»» maxTokens|integer|true|none||单次最大输出 token，1 至 393216|
|»»» contextWindow|integer|true|none||上下文窗口，1 至 10485760|
|»»» temperature|number|true|none||采样温度，0 至 2|
|»»» retryCount|integer|true|none||重试次数|
|»»» retryDelay|number|true|none||重试间隔秒数|
|»»» isDefault|boolean|true|none||是否默认 Profile|
|»»» isActive|boolean|true|none||是否启用|
|»»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createTime|string(date-time)|true|none||ISO 8601 创建时间|
|»»» updateTime|string(date-time)|true|none||ISO 8601 更新时间|
|»»» credentialName|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证名称|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» credentialProvider|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证供应商|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» credentialBaseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||凭证 Base URL|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## PUT 设置默认 LLM Profile

PUT /agent/llm/profiles/{profileId}/default

设置默认 LLM Profile。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|integer| 是 ||LLM Profile ID。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» profileId|integer|true|none||Profile ID|
|»» name|string|true|none||显示名称|
|»» credentialId|integer|true|none||关联凭证 ID|
|»» model|string|true|none||模型标识|
|»» maxTokens|integer|true|none||单次最大输出 token，1 至 393216|
|»» contextWindow|integer|true|none||上下文窗口，1 至 10485760|
|»» temperature|number|true|none||采样温度，0 至 2|
|»» retryCount|integer|true|none||重试次数|
|»» retryDelay|number|true|none||重试间隔秒数|
|»» isDefault|boolean|true|none||是否默认 Profile|
|»» isActive|boolean|true|none||是否启用|
|»» description|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||备注|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createTime|string(date-time)|true|none||ISO 8601 创建时间|
|»» updateTime|string(date-time)|true|none||ISO 8601 更新时间|
|»» credentialName|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证名称|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» credentialProvider|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证供应商|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» credentialBaseUrl|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||凭证 Base URL|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## POST 测试 LLM Profile 连通性

POST /agent/llm/profiles/{profileId}/test

对 Profile 对应的供应商发起小型连通性请求。网络或模型错误不会使 HTTP 请求本身失败，而会在 data.available=false 和 data.error 中返回。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|profileId|path|integer| 是 ||LLM Profile ID。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» profileId|integer|true|none||Profile ID|
|»» credentialId|integer|true|none||凭证 ID|
|»» model|string|true|none||模型|
|»» available|boolean|true|none||连通性是否成功|
|»» latencyMs|number|true|none||耗时毫秒|
|»» content|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||成功时的结构化验证文本|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» finishReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||模型结束原因|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» usage|any|false|none||none|
|»» error|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||失败原因；连通性请求本身成功时也会放在 data 内|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

# 设置/模型价格

## POST 新增模型定价

POST /agent/model-pricing

新增官方通用价或绑定 credentialId 的用户自定义模型定价。费用单位由调用方与供应商计费口径保持一致。

> Body 请求参数

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

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» model|body|string| 是 ||模型标识|
|» inputPrice|body|number| 否 ||普通输入单价，默认 1.0|
|» cachedInputPrice|body|number| 否 ||缓存输入单价，默认 0.1|
|» outputPrice|body|number| 否 ||输出单价，默认 3.0|
|» multiplier|body|number| 否 ||价格乘数，默认 1.0|
|» credentialId|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||专属凭证 ID；不传则官方/通用定价|
|»» *anonymous*|body|null| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "pricingId": 7,
    "model": "gpt-5",
    "inputPrice": 1.0,
    "cachedInputPrice": 0.1,
    "outputPrice": 3.0,
    "multiplier": 1.0,
    "credentialId": null,
    "isActive": 1,
    "createdAt": "2026-08-16T15:00:00",
    "updatedAt": "2026-08-16T15:00:00"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» pricingId|integer|true|none||定价记录 ID|
|»» model|string|true|none||模型标识|
|»» inputPrice|number|true|none||普通输入单价，非负|
|»» cachedInputPrice|number|true|none||缓存输入单价，非负|
|»» outputPrice|number|true|none||输出单价，非负|
|»» multiplier|number|true|none||价格乘数，非负|
|»» credentialId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||专属凭证 ID；null 为官方/通用定价|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isActive|integer|true|none||启用状态：1 启用、0 停用|
|»» createdAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 创建时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» updatedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 更新时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|isActive|0|
|isActive|1|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询模型定价列表

GET /agent/model-pricing

查询模型定价，可按 model、credentialId 与 isActive 筛选；返回 ListResponse。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|model|query|string| 否 ||按模型标识过滤。|
|credentialId|query|integer| 否 ||按专属凭证 ID 过滤。|
|isActive|query|integer| 否 ||按启用状态过滤：0 或 1。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» pricingId|integer|true|none||定价记录 ID|
|»»» model|string|true|none||模型标识|
|»»» inputPrice|number|true|none||普通输入单价，非负|
|»»» cachedInputPrice|number|true|none||缓存输入单价，非负|
|»»» outputPrice|number|true|none||输出单价，非负|
|»»» multiplier|number|true|none||价格乘数，非负|
|»»» credentialId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||专属凭证 ID；null 为官方/通用定价|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» isActive|integer|true|none||启用状态：1 启用、0 停用|
|»»» createdAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||ISO 8601 创建时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» updatedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||ISO 8601 更新时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|isActive|0|
|isActive|1|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询单条模型定价

GET /agent/model-pricing/{pricingId}

查询单条模型定价。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|pricingId|path|integer| 是 ||模型定价记录 ID。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» pricingId|integer|true|none||定价记录 ID|
|»» model|string|true|none||模型标识|
|»» inputPrice|number|true|none||普通输入单价，非负|
|»» cachedInputPrice|number|true|none||缓存输入单价，非负|
|»» outputPrice|number|true|none||输出单价，非负|
|»» multiplier|number|true|none||价格乘数，非负|
|»» credentialId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||专属凭证 ID；null 为官方/通用定价|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isActive|integer|true|none||启用状态：1 启用、0 停用|
|»» createdAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 创建时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» updatedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 更新时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|isActive|0|
|isActive|1|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## PUT 更新模型定价

PUT /agent/model-pricing/{pricingId}

仅提交需要修改的字段。记录不存在时返回业务失败。

> Body 请求参数

```json
{
  "model": "string",
  "inputPrice": 0,
  "cachedInputPrice": 0,
  "outputPrice": 0,
  "multiplier": 0,
  "credentialId": 1,
  "isActive": 0
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|pricingId|path|integer| 是 ||模型定价记录 ID。|
|body|body|object| 是 ||none|
|» model|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||模型标识|
|»» *anonymous*|body|null| 否 ||none|
|» inputPrice|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||普通输入单价|
|»» *anonymous*|body|null| 否 ||none|
|» cachedInputPrice|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||缓存输入单价|
|»» *anonymous*|body|null| 否 ||none|
|» outputPrice|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||输出单价|
|»» *anonymous*|body|null| 否 ||none|
|» multiplier|body|any| 否 ||none|
|»» *anonymous*|body|number| 否 ||价格乘数|
|»» *anonymous*|body|null| 否 ||none|
|» credentialId|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||专属凭证 ID|
|»» *anonymous*|body|null| 否 ||none|
|» isActive|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||启用状态：0 或 1|
|»» *anonymous*|body|null| 否 ||none|

#### 枚举值

|属性|值|
|---|---|
|»» *anonymous*|0|
|»» *anonymous*|1|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» pricingId|integer|true|none||定价记录 ID|
|»» model|string|true|none||模型标识|
|»» inputPrice|number|true|none||普通输入单价，非负|
|»» cachedInputPrice|number|true|none||缓存输入单价，非负|
|»» outputPrice|number|true|none||输出单价，非负|
|»» multiplier|number|true|none||价格乘数，非负|
|»» credentialId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||专属凭证 ID；null 为官方/通用定价|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isActive|integer|true|none||启用状态：1 启用、0 停用|
|»» createdAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 创建时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» updatedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 更新时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|isActive|0|
|isActive|1|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## DELETE 删除模型定价

DELETE /agent/model-pricing/{pricingId}

删除模型定价记录。记录不存在时返回业务失败。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|pricingId|path|integer| 是 ||模型定价记录 ID。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» pricingId|integer|true|none||定价记录 ID|
|»» model|string|true|none||模型标识|
|»» inputPrice|number|true|none||普通输入单价，非负|
|»» cachedInputPrice|number|true|none||缓存输入单价，非负|
|»» outputPrice|number|true|none||输出单价，非负|
|»» multiplier|number|true|none||价格乘数，非负|
|»» credentialId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||专属凭证 ID；null 为官方/通用定价|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isActive|integer|true|none||启用状态：1 启用、0 停用|
|»» createdAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 创建时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» updatedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 更新时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|isActive|0|
|isActive|1|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

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
|pid|path|integer| 是 ||目标进程的 PID，必须为大于 0 的整数。|

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

检查普通模式 WebSocket 终端依赖的运行环境。服务端会确认 Docker 已安装且普通终端容器正在运行；只有检查成功时才返回可用状态。该接口不创建终端会话。失败时返回业务错误，例如 Docker 不可用或指定容器未运行。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "normalTerminalAvailable": true,
    "normalContainerName": "string"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|普通终端环境可用时的统一响应。|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码|
|» msg|string|true|none||提示信息|
|» data|object|true|none||终端环境信息|
|»» normalTerminalAvailable|boolean|true|none||普通终端是否可用|
|»» normalContainerName|string|true|none||承载普通终端的 Docker 容器名称|

## POST 查询终端会话日志

POST /terminal/session/log

分页查询已结束或已记录的终端会话审计日志。请求体继承 PageSearchRequest，`page` 与 `pageSize` 均为非负整数。响应 data 为 `{ total, items }`；每条日志记录会话 ID、面板用户、客户端 IP、普通/管理员模式、管理员认证结果、开始与结束时间、关闭原因及子进程退出码。该接口只读取持久化日志，不会影响正在运行的终端会话。

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
|containerId|path|string| 是 ||目标 Docker 容器的 ID 或名称。|

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
|containerId|path|string| 是 ||需要删除的 Docker 容器 ID 或名称。|

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
|containerId|path|string| 是 ||目标 Docker 容器的 ID 或名称。|
|tailLines|query|integer| 否 ||返回日志末尾的行数，默认 200，范围 1-5000。|

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
|containerId|path|string| 是 ||需要停止的 Docker 容器 ID 或名称。|

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
|containerId|path|string| 是 ||需要启动的 Docker 容器 ID 或名称。|

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
|containerId|path|string| 是 ||需要重启的 Docker 容器 ID 或名称。|

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
|imageName|query|string| 是 ||待拉取的镜像名称，例如 nginx。|
|tag|query|string| 否 ||镜像标签，默认 latest。|
|platform|query|string| 否 ||目标镜像平台，可选，例如 linux/amd64。|
|registry|query|string| 否 ||可选的自定义镜像仓库地址。|

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
|imageName|query|string| 是 ||用于创建容器的镜像名称。|
|containerName|query|string| 是 ||新容器名称。|
|ports|query|string| 否 ||端口映射 JSON 字符串，例如 {"8080":"80"}。|
|envVars|query|string| 否 ||环境变量 JSON 字符串，例如 {"APP_ENV":"prod"}。|
|volumes|query|string| 否 ||卷挂载 JSON 字符串，例如 {"/host/data":"/app/data"}。|
|platform|query|string| 否 ||可选的目标平台，例如 linux/amd64。|
|restartPolicy|query|string| 否 ||可选的 Docker 重启策略，例如 always 或 unless-stopped。|

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
|q|query|string| 是 ||Docker 镜像搜索关键词。|
|limit|query|integer| 否 ||最多返回的镜像数量，默认 25，范围 1-100。|

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
|mirrors|query|string| 是 ||镜像加速站 URL 数组的 JSON 字符串，例如 ["https://docker.m.daocloud.cn"]。|

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
|databaseType|path|string| 是 ||待检查的数据库类型。当前数据库管理接口主要使用 `mysql`。|

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
|databaseType|path|string| 是 ||待查询运行状态的数据库类型。当前数据库管理接口主要使用 `mysql`。|

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

<a id="opIdgetInstallInfo_nginx_install_get"></a>

## GET 查询 Nginx 安装信息

GET /nginx/install

读取 Nginx 是否安装、版本和主配置路径。需要 accessToken Cookie；未安装时仍返回成功包装但 data.isInstalled=false。底层命令失败会返回 code=0。

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

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» isInstalled|boolean|false|none||none|
|»» version|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» configPath|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetStatus_nginx_status_get"></a>

## GET 查询 Nginx 运行状态

GET /nginx/status

读取 Nginx active 状态、worker 进程数和可选 stub_status 指标。需要 accessToken Cookie；Nginx 未安装/服务不可用时返回业务错误。

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
    "workerProcessCount": 4,
    "activeConnections": 12,
    "requestsPerSecond": null
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» isRunning|boolean|false|none||none|
|»» workerProcessCount|integer|false|none||none|
|»» activeConnections|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» requestsPerSecond|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|number|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdtestConfig_nginx_test_config_post"></a>

## POST 测试 Nginx 配置

POST /nginx/test-config

通过特权代理执行 nginx -t，验证配置语法，不会 reload。需要 accessToken Cookie；返回 isValid、stdout、stderr，命令失败时返回业务错误。

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
    "stderr": "nginx: configuration file /etc/nginx/nginx.conf test is successful"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» isValid|boolean|false|none||none|
|»» stdout|string|false|none||none|
|»» stderr|string|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdreloadNginx_nginx_reload_post"></a>

## POST 重载 Nginx

POST /nginx/reload

通过特权代理执行 systemctl reload nginx。需要 accessToken Cookie；建议先调用 /nginx/test-config；成功返回服务名、动作和 isReloaded，权限/配置错误返回业务错误。

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

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» serviceName|string|false|none||none|
|»» action|string|false|none||none|
|»» isReloaded|boolean|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|action|reload|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdrestartNginx_nginx_restart_post"></a>

## POST 重启 Nginx

POST /nginx/restart

通过特权代理执行 systemctl restart nginx，并查询 is-active。需要 accessToken Cookie；成功返回 isRestarted 和 currentStatus，权限/服务错误返回业务错误。

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

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» serviceName|string|false|none||none|
|»» action|string|false|none||none|
|»» isRestarted|boolean|false|none||none|
|»» currentStatus|string|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|action|restart|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetSiteList_nginx_sites_get"></a>

## GET 获取 Nginx 站点列表

GET /nginx/sites

扫描 sites-enabled 或 conf.d，返回站点总数和配置摘要。需要 accessToken Cookie。每个站点包含配置文件名/路径、域名、listen、static/reverse_proxy/unknown 模式、rootPath、proxyPass、启用状态。

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

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» list|[object]|false|none||none|
|»»» configName|string|false|none||none|
|»»» configPath|string|false|none||none|
|»»» domain|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» listen|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» mode|string|false|none||none|
|»»» rootPath|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» proxyPass|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» isEnabled|boolean|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdcreateSite_nginx_site_post"></a>

## POST 创建 Nginx 站点

POST /nginx/site

创建 static 或 reverse_proxy 站点并 reload。需要 accessToken Cookie。domain 必填；mode=static 时 rootPath 必填；mode=reverse_proxy 时 proxyPass 必填，可用 proxyProtocol+proxyPort 拼出上游地址；listenPort 1..65535 默认 80。

> Body 请求参数

```json
{
  "domain": "string",
  "mode": "static",
  "listenPort": 80,
  "rootPath": "string",
  "proxyPass": "string",
  "proxyPort": 1,
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
|» listenPort|body|integer| 否 ||none|
|» rootPath|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|
|» proxyPass|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|
|» proxyPort|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|
|» proxyProtocol|body|string| 否 ||none|

#### 枚举值

|属性|值|
|---|---|
|» mode|static|
|» mode|reverse_proxy|
|» proxyProtocol|http|
|» proxyProtocol|https|

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
    "enabledPath": "/etc/nginx/sites-enabled/example.com.conf",
    "rootPath": "/var/www/example.com",
    "proxyPass": null,
    "isEnabled": true,
    "isReloaded": true
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» domain|string|false|none||none|
|»» mode|string|false|none||none|
|»» listenPort|integer|false|none||none|
|»» configPath|string|false|none||none|
|»» enabledPath|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» rootPath|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» proxyPass|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isEnabled|boolean|false|none||none|
|»» isReloaded|boolean|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|static|
|mode|reverse_proxy|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIddeleteSite_nginx_site_configName_delete"></a>

## DELETE 删除 Nginx 站点

DELETE /nginx/site/{configName}

删除指定站点配置并 reload。需要 accessToken Cookie。configName 为配置文件名（如 example.com.conf），不存在或特权代理失败时返回业务错误；删除不可恢复，请确认目标。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|configName|path|string| 是 ||配置文件名，不应包含路径|

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

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» configName|string|false|none||none|
|»» configPath|string|false|none||none|
|»» isDeleted|boolean|false|none||none|
|»» isReloaded|boolean|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdapplySsl_nginx_ssl_apply_post"></a>

## POST 申请 Nginx SSL 证书

POST /nginx/ssl/apply

为已有站点申请 Let’s Encrypt 证书。需要 accessToken Cookie。服务端从站点配置推断 webroot，再经特权代理运行 certbot；domain/email 必填。certbot 未安装、LoongArch 不支持或 ACME 校验失败时返回业务错误。

> Body 请求参数

```json
{
  "domain": "string",
  "email": "user@example.com"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» domain|body|string| 否 ||none|
|» email|body|string(email)| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "domain": "example.com",
    "webroot": "/var/www/example.com",
    "certPath": "/etc/letsencrypt/live/example.com/fullchain.pem",
    "keyPath": "/etc/letsencrypt/live/example.com/privkey.pem",
    "isApplied": true
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» domain|string|false|none||none|
|»» webroot|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» certPath|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» keyPath|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» isApplied|boolean|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdconfigSsl_nginx_ssl_config_post"></a>

## POST 配置 Nginx SSL

POST /nginx/ssl/config

将已有证书挂载到指定站点，生成 HTTPS 配置并测试/reload。需要 accessToken Cookie。domain、certPath、keyPath 必填且文件必须存在；配置测试或权限失败返回业务错误。

> Body 请求参数

```json
{
  "domain": "string",
  "certPath": "string",
  "keyPath": "string"
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
{
  "code": 1,
  "msg": "success",
  "data": {
    "domain": "example.com",
    "configPath": "/etc/nginx/sites-enabled/example.com.conf",
    "certPath": "/etc/letsencrypt/live/example.com/fullchain.pem",
    "keyPath": "/etc/letsencrypt/live/example.com/privkey.pem",
    "isSslConfigured": true,
    "isReloaded": true
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» domain|string|false|none||none|
|»» configPath|string|false|none||none|
|»» certPath|string|false|none||none|
|»» keyPath|string|false|none||none|
|»» isSslConfigured|boolean|false|none||none|
|»» isReloaded|boolean|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdrenewSsl_nginx_ssl_renew_post"></a>

## POST 续期 Nginx SSL 证书

POST /nginx/ssl/renew

续期指定域名的 certbot 证书，并执行 nginx -t 和 reload。需要 accessToken Cookie。domain 必填；certbot 不可用、续期失败或配置校验失败返回业务错误。

> Body 请求参数

```json
{
  "domain": "string"
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
{
  "code": 1,
  "msg": "success",
  "data": {
    "domain": "example.com",
    "isRenewed": true,
    "isReloaded": true
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» domain|string|false|none||none|
|»» isRenewed|boolean|false|none||none|
|»» isReloaded|boolean|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetSiteConfig_nginx_site_domain_get"></a>

## GET 读取站点配置

GET /nginx/site/{domain}

读取指定域名的 Nginx 配置原文和解析字段。需要 accessToken Cookie。domain 必须是域名或站点名；找不到配置时返回业务错误。解析字段包括 serverName、listen、root、proxyPass、sslCertPath、sslKeyPath。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|domain|path|string| 是 ||域名/站点名|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "domain": "example.com",
    "configPath": "/etc/nginx/sites-enabled/example.com.conf",
    "content": "server {\n    listen 80;\n    server_name example.com;\n}",
    "parsed": {
      "serverName": "example.com",
      "listen": "80",
      "root": null,
      "proxyPass": null,
      "sslCertPath": null,
      "sslKeyPath": null
    }
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» domain|string|true|none||none|
|»» configPath|string|true|none||none|
|»» content|string|true|none||none|
|»» parsed|object|true|none||none|
|»»» serverName|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» listen|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» root|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» proxyPass|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» sslCertPath|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» sslKeyPath|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdupdateSiteConfig_nginx_site_domain_put"></a>

## PUT 上传并应用站点配置

PUT /nginx/site/{domain}

原子化替换指定站点的完整 server block：备份旧文件→写入→nginx -t→失败回滚，成功后 reload。需要 accessToken Cookie。content 非空且应包含完整合法配置；语法错误、站点不存在或权限不足返回业务错误。

> Body 请求参数

```json
{
  "content": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|domain|path|string| 是 ||域名/站点名|
|body|body|object| 是 ||none|
|» content|body|string| 否 ||完整 Nginx server block 原文|

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

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» targetPath|string|false|none||none|
|»» isSaved|boolean|false|none||none|
|»» isReloaded|boolean|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

# agent

## POST 创建 Agent 会话

POST /agent/sessions

创建 Agent 会话。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

> Body 请求参数

```json
{
  "title": "新 Agent 会话",
  "mode": "read_only",
  "profileId": 1,
  "toolSource": "current_mcp",
  "safetyPolicy": "default",
  "source": "manual",
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

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» title|body|string| 否 ||会话标题，默认 新 Agent 会话|
|» mode|body|string| 否 ||运行模式，默认 agent|
|» profileId|body|any| 否 ||none|
|»» *anonymous*|body|integer| 否 ||LLM Profile ID；不传使用默认|
|»» *anonymous*|body|null| 否 ||none|
|» toolSource|body|string| 否 ||工具来源|
|» safetyPolicy|body|string| 否 ||安全策略，默认 default|
|» source|body|string| 否 ||会话来源 manual / scheduled / inspection|
|» mcpServers|body|any| 否 ||none|
|»» *anonymous*|body|[object]| 否 ||none|
|»»» name|body|string| 是 ||服务端唯一名称|
|»»» command|body|[string]| 是 ||none|
|»»» cwd|body|any| 否 ||none|
|»»»» *anonymous*|body|string| 否 ||可选工作目录|
|»»»» *anonymous*|body|null| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|

#### 枚举值

|属性|值|
|---|---|
|» mode|read_only|
|» mode|plan|
|» mode|agent|
|» mode|break_glass|
|» toolSource|current_mcp|
|» toolSource|stdio|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "sessionId": "sess_01JEXAMPLE",
    "title": "磁盘异常排查",
    "mode": "agent",
    "status": "idle",
    "source": "manual",
    "profileId": 2,
    "toolSource": "current_mcp",
    "safetyPolicy": "default",
    "mcpServers": null,
    "summary": null,
    "lastError": null,
    "createdAt": "2026-08-16T15:00:00",
    "updatedAt": "2026-08-16T15:00:00",
    "finishedAt": null
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话唯一 ID|
|»» title|string|true|none||会话标题|
|»» mode|string|true|none||运行模式：read_only、plan、agent 或 break_glass|
|»» status|string|true|none||会话状态，例如 idle、running、waiting_approval、completed_unread 或 error|
|»» source|string|true|none||会话来源：manual、scheduled 或 inspection|
|»» profileId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||LLM Profile ID；null 表示使用默认 Profile|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» toolSource|string|true|none||工具来源|
|»» safetyPolicy|string|true|none||安全策略|
|»» mcpServers|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|[object]|false|none||none|
|»»»» name|string|true|none||服务端唯一名称|
|»»»» command|[string]|true|none||none|
|»»»» cwd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|string|false|none||可选工作目录|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||最后错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|read_only|
|mode|plan|
|mode|agent|
|mode|break_glass|
|toolSource|current_mcp|
|toolSource|stdio|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询 Agent 会话列表

GET /agent/sessions

查询 Agent 会话列表。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|page|query|integer| 否 ||页码，从 1 开始，默认 1。|
|pageSize|query|integer| 否 ||每页数量，1 至 200，默认 20。|
|status|query|string| 否 ||按会话状态筛选。|
|keyword|query|string| 否 ||按关键词筛选。|

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
        "sessionId": "sess_01JEXAMPLE",
        "title": "磁盘异常排查",
        "mode": "agent",
        "status": "idle",
        "source": "manual",
        "profileId": 2,
        "toolSource": "current_mcp",
        "safetyPolicy": "default",
        "createdAt": "2026-08-16T15:00:00",
        "updatedAt": "2026-08-16T15:00:00"
      }
    ]
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» sessionId|string|true|none||会话唯一 ID|
|»»» title|string|true|none||会话标题|
|»»» mode|string|true|none||运行模式：read_only、plan、agent 或 break_glass|
|»»» status|string|true|none||会话状态，例如 idle、running、waiting_approval、completed_unread 或 error|
|»»» source|string|true|none||会话来源：manual、scheduled 或 inspection|
|»»» profileId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||LLM Profile ID；null 表示使用默认 Profile|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» toolSource|string|true|none||工具来源|
|»»» safetyPolicy|string|true|none||安全策略|
|»»» mcpServers|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|[object]|false|none||none|
|»»»»» name|string|true|none||服务端唯一名称|
|»»»»» command|[string]|true|none||none|
|»»»»» cwd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»»» *anonymous*|string|false|none||可选工作目录|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||最后错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|read_only|
|mode|plan|
|mode|agent|
|mode|break_glass|
|toolSource|current_mcp|
|toolSource|stdio|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询单个 Agent 会话

GET /agent/sessions/{sessionId}

查询单个 Agent 会话。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话唯一 ID|
|»» title|string|true|none||会话标题|
|»» mode|string|true|none||运行模式：read_only、plan、agent 或 break_glass|
|»» status|string|true|none||会话状态，例如 idle、running、waiting_approval、completed_unread 或 error|
|»» source|string|true|none||会话来源：manual、scheduled 或 inspection|
|»» profileId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||LLM Profile ID；null 表示使用默认 Profile|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» toolSource|string|true|none||工具来源|
|»» safetyPolicy|string|true|none||安全策略|
|»» mcpServers|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|[object]|false|none||none|
|»»»» name|string|true|none||服务端唯一名称|
|»»»» command|[string]|true|none||none|
|»»»» cwd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|string|false|none||可选工作目录|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||最后错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|read_only|
|mode|plan|
|mode|agent|
|mode|break_glass|
|toolSource|current_mcp|
|toolSource|stdio|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## DELETE 删除 Agent 会话

DELETE /agent/sessions/{sessionId}

删除 Agent 会话。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询会话消息历史

GET /agent/sessions/{sessionId}/messages

查询会话消息历史。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» messageId|integer|true|none||消息 ID|
|»»» sessionId|string|true|none||所属会话 ID|
|»»» role|string|true|none||消息角色，例如 user、assistant、tool 或 system|
|»»» content|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||文本内容；仅含 tool_calls 的 assistant 消息可为 null|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» toolCallId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||工具调用 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» traceId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||关联 trace ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» roundIndex|integer|true|none||对话轮次|
|»»» metadata|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||ISO 8601 时间|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询 Agent Trace 原始事件

GET /agent/traces

按可选 sessionId、traceId、eventType 查询原始 Trace 事件。当前实现只依赖登录拦截器，不额外按会话归属过滤，调用方应遵守权限边界。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|query|string| 否 ||按会话 ID 过滤。|
|traceId|query|string| 否 ||按 Trace ID 过滤。|
|eventType|query|string| 否 ||按事件类型过滤。|
|limit|query|integer| 否 ||返回数量，1 至 1000，默认 100。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» id|integer|true|none||Trace 事件 ID|
|»»» traceId|string|true|none||Trace ID|
|»»» sessionId|string|true|none||会话 ID|
|»»» eventType|string|true|none||事件类型|
|»»» timestamp|number|true|none||Unix 时间戳|
|»»» data|any|true|none||none|
|»»» entryHash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||当前事件哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» prevHash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||前一事件哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||ISO 8601 入库时间|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询 Session Trace 时间线

GET /agent/traces/{sessionId}/timeline

按会话 ID 返回排序后的精简 Trace 时间线。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|
|limit|query|integer| 否 ||时间线最大事件数，1 至 1000，默认 200。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» id|integer|true|none||Trace 事件 ID|
|»»» traceId|string|true|none||Trace ID|
|»»» sessionId|string|true|none||会话 ID|
|»»» eventType|string|true|none||事件类型|
|»»» stage|string|true|none||时间线阶段|
|»»» timestamp|number|true|none||Unix 时间戳|
|»»» data|any|true|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询 Session Trace 汇总

GET /agent/traces/{sessionId}/summary

返回会话 Trace 的事件数、工具调用数、审批数、注入标记和关联 Trace ID。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "sessionId": "sess_01JEXAMPLE",
    "totalEvents": 12,
    "toolCalls": 2,
    "approvalCount": 0,
    "hasInjection": false,
    "traces": [
      "trace_01"
    ]
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话 ID|
|»» totalEvents|integer|true|none||事件总数|
|»» toolCalls|integer|true|none||工具调用数|
|»» approvalCount|integer|true|none||审批请求数|
|»» hasInjection|boolean|true|none||是否检测到注入相关事件|
|»» traces|[string]|true|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## PUT 切换 Agent 工具来源

PUT /agent/sessions/{sessionId}/tool-source

切换会话运行时工具来源并使运行时缓存失效。使用 current_mcp 时不应提交 mcpServers；使用 stdio 时可提交外部 MCP 服务端配置。

> Body 请求参数

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

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|
|body|body|object| 是 ||none|
|» toolSource|body|string| 是 ||目标工具来源|
|» mcpServers|body|any| 否 ||none|
|»» *anonymous*|body|[object]| 否 ||仅 stdio 可用；未提供时保留已有配置|
|»»» name|body|string| 是 ||服务端唯一名称|
|»»» command|body|[string]| 是 ||none|
|»»» cwd|body|any| 否 ||none|
|»»»» *anonymous*|body|string| 否 ||可选工作目录|
|»»»» *anonymous*|body|null| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|

#### 枚举值

|属性|值|
|---|---|
|» toolSource|current_mcp|
|» toolSource|stdio|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话唯一 ID|
|»» title|string|true|none||会话标题|
|»» mode|string|true|none||运行模式：read_only、plan、agent 或 break_glass|
|»» status|string|true|none||会话状态，例如 idle、running、waiting_approval、completed_unread 或 error|
|»» source|string|true|none||会话来源：manual、scheduled 或 inspection|
|»» profileId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||LLM Profile ID；null 表示使用默认 Profile|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» toolSource|string|true|none||工具来源|
|»» safetyPolicy|string|true|none||安全策略|
|»» mcpServers|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|[object]|false|none||none|
|»»»» name|string|true|none||服务端唯一名称|
|»»»» command|[string]|true|none||none|
|»»»» cwd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|string|false|none||可选工作目录|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||最后错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|read_only|
|mode|plan|
|mode|agent|
|mode|break_glass|
|toolSource|current_mcp|
|toolSource|stdio|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## PUT 切换 Agent 模型

PUT /agent/sessions/{sessionId}/switch-model

将会话绑定到目标的已启用 LLM Profile，并使运行时缓存失效。Profile 不存在或未启用时为业务失败。

> Body 请求参数

```json
{
  "profileId": 1
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|
|body|body|object| 是 ||none|
|» profileId|body|integer| 是 ||目标可用 LLM Profile ID|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话唯一 ID|
|»» title|string|true|none||会话标题|
|»» mode|string|true|none||运行模式：read_only、plan、agent 或 break_glass|
|»» status|string|true|none||会话状态，例如 idle、running、waiting_approval、completed_unread 或 error|
|»» source|string|true|none||会话来源：manual、scheduled 或 inspection|
|»» profileId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||LLM Profile ID；null 表示使用默认 Profile|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» toolSource|string|true|none||工具来源|
|»» safetyPolicy|string|true|none||安全策略|
|»» mcpServers|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|[object]|false|none||none|
|»»»» name|string|true|none||服务端唯一名称|
|»»»» command|[string]|true|none||none|
|»»»» cwd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|string|false|none||可选工作目录|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||最后错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|read_only|
|mode|plan|
|mode|agent|
|mode|break_glass|
|toolSource|current_mcp|
|toolSource|stdio|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询 Token 用量明细

GET /agent/sessions/{sessionId}/usage

查询 Token 用量明细。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": []
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|[object]|true|none||none|
|»» id|integer|true|none||记录 ID|
|»» sessionId|string|true|none||会话 ID|
|»» traceId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||Trace ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» model|string|true|none||模型|
|»» inputTokens|integer|true|none||输入 token|
|»» cachedInputTokens|integer|false|none||缓存输入 token|
|»» nonCachedInputTokens|integer|false|none||非缓存输入 token|
|»» outputTokens|integer|true|none||输出 token|
|»» totalTokens|integer|true|none||总 token|
|»» cachedInputCost|number|false|none||缓存输入费用|
|»» nonCachedInputCost|number|false|none||非缓存输入费用|
|»» inputCost|number|true|none||输入费用|
|»» outputCost|number|true|none||输出费用|
|»» totalCost|number|true|none||总费用|
|»» createdAt|string(date-time)|true|none||ISO 8601 时间|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询会话计费汇总

GET /agent/sessions/{sessionId}/billing

查询会话计费汇总。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "sessionId": "sess_01JEXAMPLE",
    "totalInputTokens": 1200,
    "totalCachedInputTokens": 0,
    "totalNonCachedInputTokens": 1200,
    "totalOutputTokens": 300,
    "totalTokens": 1500,
    "totalCachedInputCost": 0,
    "totalNonCachedInputCost": 0.0012,
    "totalInputCost": 0.0012,
    "totalOutputCost": 0.0009,
    "totalCost": 0.0021,
    "callCount": 1
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话 ID|
|»» totalInputTokens|integer|true|none||输入 token 合计|
|»» totalCachedInputTokens|integer|false|none||缓存输入 token 合计|
|»» totalNonCachedInputTokens|integer|false|none||非缓存输入 token 合计|
|»» totalOutputTokens|integer|true|none||输出 token 合计|
|»» totalTokens|integer|true|none||token 总计|
|»» totalCachedInputCost|number|false|none||缓存输入费用合计|
|»» totalNonCachedInputCost|number|false|none||非缓存输入费用合计|
|»» totalInputCost|number|false|none||输入费用合计|
|»» totalOutputCost|number|false|none||输出费用合计|
|»» totalCost|number|true|none||总费用|
|»» callCount|integer|true|none||模型调用次数|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

## GET 查询最近 Agent 会话状态

GET /agent/status

首页轻量状态接口。仅返回当前登录用户最近会话的状态摘要，不加载消息及 Trace 明细。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|limit|query|integer| 否 ||返回最近会话数量，1 至 20，默认 5。|

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
        "sessionId": "sess_01JEXAMPLE",
        "title": "磁盘异常排查",
        "status": "running",
        "source": "manual",
        "summary": null,
        "lastError": null,
        "createdAt": "2026-08-16T15:00:00",
        "updatedAt": "2026-08-16T15:01:00",
        "finishedAt": null
      }
    ]
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» total|integer|true|none||总记录数|
|»» items|[object]|true|none||数据列表|
|»»» sessionId|string|true|none||会话唯一 ID|
|»»» title|string|true|none||会话标题|
|»»» status|string|true|none||当前状态|
|»»» source|string|true|none||会话来源|
|»»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||最近错误|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

# 日志管理

<a id="opIdgetAll_log_all_get"></a>

## GET 查询操作日志列表

GET /log/all

返回系统记录的全部操作日志，不分页。日志字段可能包含请求和返回快照，调用方应避免在页面或外部系统泄露敏感信息。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|[object]|true|none||none|
|»» logId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||日志 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» functionName|string|true|none||函数名|
|»» inputParams|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» returnValue|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» userId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||用户 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» ipAddress|string|true|none||来源 IP|
|»» operationTime|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||操作时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» executionTime|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|number|false|none||执行耗时毫秒|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» errorMessage|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» requestPath|string|true|none||请求路径|
|»» httpMethod|string|true|none||HTTP 方法|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

# Agent

<a id="opIdmarkSessionRead_agent_sessions__sessionId__mark_read_put"></a>

## PUT 标记 Agent 会话已读

PUT /agent/sessions/{sessionId}/mark-read

标记 Agent 会话已读。需要登录后的 accessToken HttpOnly Cookie。 成功响应统一为 {code: 1, msg: 'success', data: ...}；业务校验失败通常为 HTTP 200 且 code=0。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话唯一 ID|
|»» title|string|true|none||会话标题|
|»» mode|string|true|none||运行模式：read_only、plan、agent 或 break_glass|
|»» status|string|true|none||会话状态，例如 idle、running、waiting_approval、completed_unread 或 error|
|»» source|string|true|none||会话来源：manual、scheduled 或 inspection|
|»» profileId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||LLM Profile ID；null 表示使用默认 Profile|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» toolSource|string|true|none||工具来源|
|»» safetyPolicy|string|true|none||安全策略|
|»» mcpServers|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|[object]|false|none||none|
|»»»» name|string|true|none||服务端唯一名称|
|»»»» command|[string]|true|none||none|
|»»»» cwd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|string|false|none||可选工作目录|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||最后错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|read_only|
|mode|plan|
|mode|agent|
|mode|break_glass|
|toolSource|current_mcp|
|toolSource|stdio|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

<a id="opIdswitchAgentMode_agent_sessions__sessionId__mode_put"></a>

## PUT 切换 Agent 运行模式

PUT /agent/sessions/{sessionId}/mode

即时切换并持久化会话模式。合法值为 read_only、plan、agent、break_glass；不合法模式为业务失败。

> Body 请求参数

```json
{
  "mode": "read_only"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 是 ||登录后由服务端写入的 HttpOnly Cookie。除登录、刷新及管理员本地接口外均必填。|
|refreshToken|cookie|string| 否 ||none|
|sessionId|path|string| 是 ||Agent 会话 ID。仅允许当前登录用户拥有的会话。|
|body|body|object| 是 ||none|
|» mode|body|string| 是 ||目标模式|

#### 枚举值

|属性|值|
|---|---|
|» mode|read_only|
|» mode|plan|
|» mode|agent|
|» mode|break_glass|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

> 401 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|未携带、过期或非法 accessToken 时由全局拦截器返回；data 为 null。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» sessionId|string|true|none||会话唯一 ID|
|»» title|string|true|none||会话标题|
|»» mode|string|true|none||运行模式：read_only、plan、agent 或 break_glass|
|»» status|string|true|none||会话状态，例如 idle、running、waiting_approval、completed_unread 或 error|
|»» source|string|true|none||会话来源：manual、scheduled 或 inspection|
|»» profileId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||LLM Profile ID；null 表示使用默认 Profile|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» toolSource|string|true|none||工具来源|
|»» safetyPolicy|string|true|none||安全策略|
|»» mcpServers|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|[object]|false|none||none|
|»»»» name|string|true|none||服务端唯一名称|
|»»»» command|[string]|true|none||none|
|»»»» cwd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|string|false|none||可选工作目录|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»»» *anonymous*|null|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||会话摘要|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastError|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||最后错误信息|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||ISO 8601 创建时间|
|»» updatedAt|string(date-time)|true|none||ISO 8601 更新时间|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 完成时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|mode|read_only|
|mode|plan|
|mode|agent|
|mode|break_glass|
|toolSource|current_mcp|
|toolSource|stdio|

状态码 **401**

*业务校验失败通常仍返回 HTTP 200，但 code 为 0；认证失败返回 HTTP 401。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

# 管理员特权审批

## GET 查询工具授权请求详情

GET /admin/elevation/authorization/{code}

仅限 localhost 调用。查询数据库中工具授权请求的详细信息，用于管理员审批展示。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|code|path|string| 是 ||特权审批码，格式如 NGA7-K3X9。|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» code|string|true|none||授权审批码|
|»» sessionId|string|true|none||会话 ID|
|»» sourceType|string|false|none||来源：manual、scheduled 或 inspection|
|»» taskId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||关联定时任务 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» toolName|string|true|none||请求授权的工具名|
|»» args|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|any|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» paths|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|[string]|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» commandLine|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||请求命令|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» reason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||请求原因|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» policyReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||策略命中原因|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» riskLevel|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||风险等级|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» ttlSeconds|integer|true|none||有效期秒数|
|»» maxRuns|integer|true|none||最大运行次数|
|»» status|string|true|none||审批状态|
|»» createdAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||创建时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||审批人|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» rejectReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||拒绝原因|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

<a id="opIdget_code_admin_elevation_codes__code__get"></a>

## GET 查询特权审批码

GET /admin/elevation/codes/{code}

仅限 localhost 调用，必须携带 /etc/nereus/admin_token 的 Bearer Token。查询内存中的特权审批码生命周期详情。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|code|path|string| 是 ||特权审批码，格式如 NGA7-K3X9。|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» code|string|true|none||特权审批码，格式如 NGA7-K3X9|
|»» session_id|string|true|none||关联 Agent 会话 ID|
|»» request_type|string|true|none||请求类型：privileged、scheduled_task_policy 或 tool_authorization|
|»» task_id|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||关联定时任务 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approval_policy|any|false|none||none|
|»» commands|[object]|true|none||none|
|»»» command|string|true|none||命令|
|»»» args|[any]|false|none||none|
|»» reason|string|true|none||申请原因|
|»» status|string|true|none||状态：pending、approved、rejected、expired 或 consumed|
|»» ttl_seconds|integer|true|none||有效期秒数|
|»» max_ops|integer|true|none||允许最大操作次数|
|»» ops_used|integer|true|none||已使用操作次数|
|»» requested_at|string(date-time)|true|none||ISO 8601 申请时间|
|»» approved_by|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||审批人|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approved_at|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 审批时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» token_id|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||JIT Token ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» expired|boolean|true|none||是否已过期|
|»» exhausted|boolean|true|none||是否已耗尽操作次数|
|»» inline_cmd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||待执行的自由命令|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» inline_cmd_hash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||命令哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» script_path|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||待审计脚本路径|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» script_hash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||脚本哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

<a id="opIdlist_pending_admin_elevation_pending_get"></a>

## GET 查询待审批特权码列表

GET /admin/elevation/pending

仅限 localhost 调用。列出未过期且状态为 pending 的内存特权审批码。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": []
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|[object]|true|none||none|
|»» code|string|true|none||特权审批码，格式如 NGA7-K3X9|
|»» session_id|string|true|none||关联 Agent 会话 ID|
|»» request_type|string|true|none||请求类型：privileged、scheduled_task_policy 或 tool_authorization|
|»» task_id|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||关联定时任务 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approval_policy|any|false|none||none|
|»» commands|[object]|true|none||none|
|»»» command|string|true|none||命令|
|»»» args|[any]|false|none||none|
|»» reason|string|true|none||申请原因|
|»» status|string|true|none||状态：pending、approved、rejected、expired 或 consumed|
|»» ttl_seconds|integer|true|none||有效期秒数|
|»» max_ops|integer|true|none||允许最大操作次数|
|»» ops_used|integer|true|none||已使用操作次数|
|»» requested_at|string(date-time)|true|none||ISO 8601 申请时间|
|»» approved_by|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||审批人|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approved_at|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 审批时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» token_id|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||JIT Token ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» expired|boolean|true|none||是否已过期|
|»» exhausted|boolean|true|none||是否已耗尽操作次数|
|»» inline_cmd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||待执行的自由命令|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» inline_cmd_hash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||命令哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» script_path|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||待审计脚本路径|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» script_hash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||脚本哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

<a id="opIdapprove_code_admin_elevation_approve_post"></a>

## POST 批准特权请求

POST /admin/elevation/approve

仅限 localhost 调用。批准 pending 审批码并签发 JIT Token；工具授权请求可选 path_prefix 覆盖持久化授权路径范围。

> Body 请求参数

```json
{
  "code": "string",
  "approved_by": "admin",
  "path_prefix": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|
|body|body|object| 是 ||none|
|» code|body|string| 是 ||待批准的 pending 审批码|
|» approved_by|body|string| 否 ||审批人标识，默认 admin|
|» path_prefix|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||仅 tool_authorization：用该路径前缀覆盖请求路径授权范围|
|»» *anonymous*|body|null| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "status": "approved",
    "request_type": "privileged",
    "code": "NGA7-K3X9",
    "token_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "sess_01JEXAMPLE",
    "taskId": null,
    "max_ops": 10,
    "allowed_commands": []
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» status|string|true|none||approved|
|»» request_type|string|false|none||请求类型|
|»» code|string|true|none||审批码|
|»» token_id|string|true|none||JIT Token ID|
|»» session_id|string|true|none||会话 ID|
|»» taskId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||任务 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» max_ops|integer|true|none||最大操作次数|
|»» allowed_commands|[any]|true|none||none|

<a id="opIdreject_code_admin_elevation_reject_post"></a>

## POST 拒绝特权请求

POST /admin/elevation/reject

仅限 localhost 调用。拒绝 pending 审批码；对应任务或工具授权请求会同步写入拒绝状态。接口对不存在 code 保持幂等成功响应。

> Body 请求参数

```json
{
  "code": "string",
  "reason": "管理员拒绝"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|
|body|body|object| 是 ||none|
|» code|body|string| 是 ||待拒绝的 pending 审批码|
|» reason|body|string| 否 ||拒绝原因，默认 管理员拒绝|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "status": "rejected",
    "code": "NGA7-K3X9",
    "request_type": "privileged",
    "taskId": null
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» status|string|true|none||rejected|
|»» code|string|true|none||审批码|
|»» request_type|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||请求类型|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» taskId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||任务 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

<a id="opIdrevoke_token_admin_elevation_revoke_post"></a>

## POST 吊销特权 Token

POST /admin/elevation/revoke

仅限 localhost 调用。强制吊销一个已经签发的 JIT Token；Token 不存在或已过期时返回业务失败。

> Body 请求参数

```json
{
  "token_id": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|
|body|body|object| 是 ||none|
|» token_id|body|string| 是 ||待吊销的 JIT Token ID|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "status": "revoked",
    "token_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» status|string|true|none||revoked|
|»» token_id|string|true|none||Token ID|

<a id="opIdaudit_code_admin_elevation_audit__code__get"></a>

## GET 审计特权请求

GET /admin/elevation/audit/{code}

仅限 localhost 调用。仅允许审计 pending 审批码；对命令或脚本进行安全审计，返回风险等级、发现项和人工审批建议。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|code|path|string| 是 ||特权审批码，格式如 NGA7-K3X9。|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|object|true|none||none|
|»» code|string|true|none||审批码|
|»» audit|object|true|none||none|
|»»» risk_level|string|true|none||风险等级|
|»»» summary|string|true|none||审计摘要|
|»»» findings|[any]|true|none||none|
|»»» dangerous_commands|[any]|true|none||none|
|»»» network_requests|boolean|true|none||是否涉及网络请求|
|»»» nested_execution|boolean|true|none||是否包含嵌套执行|
|»»» ai_advice|string|true|none||人工审批建议|

<a id="opIdlist_history_admin_elevation_history_get"></a>

## GET 查询特权审批历史

GET /admin/elevation/history

仅限 localhost 调用。返回最近已处理或已过期的审批记录，排除仍处于 pending 状态的记录。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|limit|query|integer| 否 ||最近审批历史数量，默认 50。|
|Authorization|header|string| 是 ||仅 localhost 可调用。格式：Bearer <由 /etc/nereus/admin_token 读取的令牌>。|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "note": "请结合响应 JSON Schema 查看字段定义。"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|统一成功包络。业务失败可仍使用 HTTP 200 且 code=0。|Inline|

### 返回数据结构

状态码 **200**

*业务成功时 code 为 1。*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务状态码：1 表示成功；0 表示业务失败；40101 至 40104 表示认证失败或令牌状态错误。|
|» msg|string|true|none||结果说明；成功默认值为 success。|
|» data|[object]|true|none||none|
|»» code|string|true|none||特权审批码，格式如 NGA7-K3X9|
|»» session_id|string|true|none||关联 Agent 会话 ID|
|»» request_type|string|true|none||请求类型：privileged、scheduled_task_policy 或 tool_authorization|
|»» task_id|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|integer|false|none||关联定时任务 ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approval_policy|any|false|none||none|
|»» commands|[object]|true|none||none|
|»»» command|string|true|none||命令|
|»»» args|[any]|false|none||none|
|»» reason|string|true|none||申请原因|
|»» status|string|true|none||状态：pending、approved、rejected、expired 或 consumed|
|»» ttl_seconds|integer|true|none||有效期秒数|
|»» max_ops|integer|true|none||允许最大操作次数|
|»» ops_used|integer|true|none||已使用操作次数|
|»» requested_at|string(date-time)|true|none||ISO 8601 申请时间|
|»» approved_by|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||审批人|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approved_at|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||ISO 8601 审批时间|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» token_id|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||JIT Token ID|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» expired|boolean|true|none||是否已过期|
|»» exhausted|boolean|true|none||是否已耗尽操作次数|
|»» inline_cmd|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||待执行的自由命令|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» inline_cmd_hash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||命令哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» script_path|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||待审计脚本路径|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» script_hash|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||脚本哈希|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

# ScheduledTask

<a id="opIdcreateTask_scheduled_tasks_post"></a>

## POST 创建定时任务

POST /scheduled-tasks

创建后台 Agent 定时任务。需要 accessToken Cookie。name 1..100 字符，cronExpression 为 5 段 crontab，taskDescription 为执行指令。未传 approvalPolicy 时创建 active 并注册调度；传入策略时创建 pending_approval 并签发 approvalCode，管理员批准后才执行。

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
    "allowedCommands": [
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
    "ttlSeconds": 25200,
    "maxRuns": 100
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» name|body|string| 否 ||none|
|» cronExpression|body|string| 否 ||none|
|» taskDescription|body|string| 否 ||none|
|» approvalPolicy|body|object| 否 ||none|
|»» allowedTools|body|[string]| 否 ||允许无人值守调用的工具名|
|»» allowedCommands|body|[string]| 否 ||runCommand/runShellCommand 命令前缀白名单；空数组拒绝命令|
|»» allowedPaths|body|[string]| 否 ||允许访问的路径前缀|
|»» deniedPaths|body|[string]| 否 ||拒绝访问的路径前缀|
|»» allowedPrivilegedCommands|body|[string]| 否 ||允许的特权命令白名单|
|»» ttlSeconds|body|integer| 否 ||审批授权有效期，秒|
|»» maxRuns|body|integer| 否 ||最多执行次数|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "name": "每日巡检",
    "cronExpression": "0 3 * * *",
    "taskDescription": "检查磁盘与 Nginx 状态并汇总",
    "status": "active",
    "createdBy": 1001,
    "approvalPolicy": null,
    "approvalCode": null,
    "approvalStatus": null,
    "approvalApprovedAt": null,
    "approvalApprovedBy": null,
    "approvalTokenId": null,
    "approvalRejectedReason": null,
    "nextRunAt": "2026-08-18T03:00:00+08:00",
    "lastRunAt": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» name|string|true|none||none|
|»» cronExpression|string|true|none||5 段 crontab 表达式|
|»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»» status|string|true|none||none|
|»» createdBy|integer|true|none||none|
|»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdlistTasks_scheduled_tasks_get"></a>

## GET 查询定时任务列表

GET /scheduled-tasks

查询系统范围内的定时任务。需要 accessToken Cookie。status 可按 active/paused/pending_approval/deleted 筛选；includeDeleted 默认 false。返回 {total,items[]}，items 为完整 ScheduledTaskResponse。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|status|query|string| 否 ||状态筛选：active、paused、pending_approval、deleted|
|includeDeleted|query|boolean| 否 ||是否包含软删除任务|

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
        "id": 1,
        "name": "每日巡检",
        "cronExpression": "0 3 * * *",
        "taskDescription": "检查磁盘与 Nginx 状态并汇总",
        "status": "active",
        "createdBy": 1001,
        "approvalPolicy": null,
        "approvalCode": null,
        "approvalStatus": null,
        "approvalApprovedAt": null,
        "approvalApprovedBy": null,
        "approvalTokenId": null,
        "approvalRejectedReason": null,
        "nextRunAt": "2026-08-18T03:00:00+08:00",
        "lastRunAt": null,
        "createdAt": "2026-08-17T10:00:00Z",
        "updatedAt": "2026-08-17T10:00:00Z"
      }
    ]
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» items|[object]|false|none||none|
|»»» id|integer|true|none||none|
|»»» name|string|true|none||none|
|»»» cronExpression|string|true|none||5 段 crontab 表达式|
|»»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»»» status|string|true|none||none|
|»»» createdBy|integer|true|none||none|
|»»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||none|
|»»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdlistAllTasks_scheduled_tasks_all_get"></a>

## GET 查询全部定时任务

GET /scheduled-tasks/all

后台管理视图查询全部定时任务。需要 accessToken Cookie。includeDeleted 默认 true，与 GET /scheduled-tasks 的区别是默认包含 deleted；status 仍可筛选。返回 {total,items[]}。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|status|query|string| 否 ||状态筛选|
|includeDeleted|query|boolean| 否 ||是否包含软删除任务，默认 true|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "total": 1,
    "items": []
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» items|[object]|false|none||none|
|»»» id|integer|true|none||none|
|»»» name|string|true|none||none|
|»»» cronExpression|string|true|none||5 段 crontab 表达式|
|»»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»»» status|string|true|none||none|
|»»» createdBy|integer|true|none||none|
|»»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||none|
|»»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdlistPendingApprovalTasks_scheduled_tasks_pending_approval_get"></a>

## GET 查询待审批定时任务

GET /scheduled-tasks/pending-approval

列出所有 pending_approval 任务，供管理员审批页使用。需要 accessToken Cookie。每条记录包含 approvalCode、approvalPolicy、approvalStatus 和拒绝原因等字段。

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
    "items": []
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» items|[object]|false|none||none|
|»»» id|integer|true|none||none|
|»»» name|string|true|none||none|
|»»» cronExpression|string|true|none||5 段 crontab 表达式|
|»»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»»» status|string|true|none||none|
|»»» createdBy|integer|true|none||none|
|»»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||none|
|»»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetRun_scheduled_tasks_runs_runId_get"></a>

## GET 查询定时任务执行记录

GET /scheduled-tasks/runs/{runId}

按 runId 查询单次定时任务执行记录。需要 accessToken Cookie。不存在时返回业务错误；成功 data 为 ScheduledTaskRunResponse，可用 sessionId 关联 Agent 会话。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|runId|path|integer| 是 ||执行记录主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "taskId": 1,
    "sessionId": "sess_demo",
    "status": "success",
    "startedAt": "2026-08-17T03:00:00Z",
    "finishedAt": "2026-08-17T03:00:02Z",
    "resultSummary": "检查完成",
    "errorMessage": null,
    "tokenUsage": {
      "total": 120
    }
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» taskId|integer|true|none||none|
|»» sessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» status|string|true|none||none|
|»» startedAt|string(date-time)|true|none||none|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» resultSummary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» errorMessage|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» tokenUsage|any|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetApproval_scheduled_tasks_taskId_approval_get"></a>

## GET 查询任务审批详情

GET /scheduled-tasks/{taskId}/approval

查询任务审批状态。需要 accessToken Cookie。返回 taskId、status、approvalPolicy、approvalCode、approvalStatus、approvedAt/by、tokenId 和 rejectedReason；任务不存在时返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "taskId": 1,
    "status": "pending_approval",
    "approvalPolicy": {
      "allowedTools": [
        "runCommand"
      ],
      "allowedCommands": [
        "df -h"
      ],
      "allowedPaths": [],
      "deniedPaths": [],
      "allowedPrivilegedCommands": [],
      "ttlSeconds": 25200,
      "maxRuns": 100
    },
    "approvalCode": "ABC123",
    "approvalStatus": "pending",
    "approvalApprovedAt": null,
    "approvalApprovedBy": null,
    "approvalTokenId": null,
    "approvalRejectedReason": null
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» taskId|integer|false|none||none|
|»» status|string|false|none||none|
|»» approvalPolicy|any|false|none||none|
|»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdreissueApproval_scheduled_tasks_taskId_approval_reissue_post"></a>

## POST 重新签发任务审批码

POST /scheduled-tasks/{taskId}/approval/reissue

为 pending_approval 且存在 approvalPolicy 的任务重新签发审批码。需要 accessToken Cookie。旧 code 立即失效，返回更新后的 ScheduledTaskResponse；active/paused 或无策略任务返回业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "name": "每日巡检",
    "cronExpression": "0 3 * * *",
    "taskDescription": "检查磁盘与 Nginx 状态并汇总",
    "status": "pending_approval",
    "createdBy": 1001,
    "approvalPolicy": {
      "allowedTools": [
        "runCommand"
      ],
      "allowedCommands": [
        "df -h"
      ],
      "allowedPaths": [],
      "deniedPaths": [],
      "allowedPrivilegedCommands": [],
      "ttlSeconds": 25200,
      "maxRuns": 100
    },
    "approvalCode": "ABC123",
    "approvalStatus": "pending",
    "approvalApprovedAt": null,
    "approvalApprovedBy": null,
    "approvalTokenId": null,
    "approvalRejectedReason": null,
    "nextRunAt": null,
    "lastRunAt": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» name|string|true|none||none|
|»» cronExpression|string|true|none||5 段 crontab 表达式|
|»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»» status|string|true|none||none|
|»» createdBy|integer|true|none||none|
|»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetTask_scheduled_tasks_taskId_get"></a>

## GET 查询单个定时任务

GET /scheduled-tasks/{taskId}

按 taskId 查询定时任务详情。需要 accessToken Cookie。deleted 任务按不存在处理；成功返回 ScheduledTaskResponse。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "name": "每日巡检",
    "cronExpression": "0 3 * * *",
    "taskDescription": "检查磁盘与 Nginx 状态并汇总",
    "status": "active",
    "createdBy": 1001,
    "approvalPolicy": null,
    "approvalCode": null,
    "approvalStatus": null,
    "approvalApprovedAt": null,
    "approvalApprovedBy": null,
    "approvalTokenId": null,
    "approvalRejectedReason": null,
    "nextRunAt": "2026-08-18T03:00:00+08:00",
    "lastRunAt": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» name|string|true|none||none|
|»» cronExpression|string|true|none||5 段 crontab 表达式|
|»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»» status|string|true|none||none|
|»» createdBy|integer|true|none||none|
|»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdupdateTask_scheduled_tasks_taskId_put"></a>

## PUT 更新定时任务

PUT /scheduled-tasks/{taskId}

部分更新定时任务。需要 accessToken Cookie。name/cronExpression/taskDescription/approvalPolicy 均可选；cronExpression 仍须为合法 5 段表达式。传入 approvalPolicy 会清除旧审批并重新进入 pending_approval、签发新 code；空对象返回当前任务。

> Body 请求参数

```json
{
  "name": "string",
  "cronExpression": "string",
  "taskDescription": "string",
  "approvalPolicy": {}
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|
|body|body|object| 是 ||none|
|» name|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|
|» cronExpression|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|
|» taskDescription|body|any| 否 ||none|
|»» *anonymous*|body|string| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|
|» approvalPolicy|body|any| 否 ||none|
|»» *anonymous*|body|object| 否 ||none|
|»» *anonymous*|body|null| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "name": "每日巡检（更新）",
    "cronExpression": "0 4 * * *",
    "taskDescription": "检查磁盘、Nginx 与容器状态",
    "status": "active",
    "createdBy": 1001,
    "approvalPolicy": null,
    "approvalCode": null,
    "approvalStatus": null,
    "approvalApprovedAt": null,
    "approvalApprovedBy": null,
    "approvalTokenId": null,
    "approvalRejectedReason": null,
    "nextRunAt": "2026-08-18T04:00:00+08:00",
    "lastRunAt": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» name|string|true|none||none|
|»» cronExpression|string|true|none||5 段 crontab 表达式|
|»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»» status|string|true|none||none|
|»» createdBy|integer|true|none||none|
|»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIddeleteTask_scheduled_tasks_taskId_delete"></a>

## DELETE 删除定时任务

DELETE /scheduled-tasks/{taskId}

软删除定时任务。需要 accessToken Cookie。后端将 status 设为 deleted、清空 nextRunAt 并从调度器移除 job，不物理删除数据库记录；成功 data=null。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdpauseTask_scheduled_tasks_taskId_pause_post"></a>

## POST 暂停定时任务

POST /scheduled-tasks/{taskId}/pause

暂停定时任务。需要 accessToken Cookie。状态变为 paused，清空 nextRunAt 并移除调度器 job；返回更新后的 ScheduledTaskResponse。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "name": "每日巡检",
    "cronExpression": "0 3 * * *",
    "taskDescription": "检查磁盘与 Nginx 状态并汇总",
    "status": "paused",
    "createdBy": 1001,
    "approvalPolicy": null,
    "approvalCode": null,
    "approvalStatus": null,
    "approvalApprovedAt": null,
    "approvalApprovedBy": null,
    "approvalTokenId": null,
    "approvalRejectedReason": null,
    "nextRunAt": null,
    "lastRunAt": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» name|string|true|none||none|
|»» cronExpression|string|true|none||5 段 crontab 表达式|
|»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»» status|string|true|none||none|
|»» createdBy|integer|true|none||none|
|»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdresumeTask_scheduled_tasks_taskId_resume_post"></a>

## POST 恢复定时任务

POST /scheduled-tasks/{taskId}/resume

恢复定时任务。需要 accessToken Cookie。状态置为 active、重新注册调度器并计算 nextRunAt；返回更新后的 ScheduledTaskResponse。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "name": "每日巡检",
    "cronExpression": "0 3 * * *",
    "taskDescription": "检查磁盘与 Nginx 状态并汇总",
    "status": "active",
    "createdBy": 1001,
    "approvalPolicy": null,
    "approvalCode": null,
    "approvalStatus": null,
    "approvalApprovedAt": null,
    "approvalApprovedBy": null,
    "approvalRejectedReason": null,
    "approvalTokenId": null,
    "nextRunAt": "2026-08-18T03:00:00+08:00",
    "lastRunAt": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» name|string|true|none||none|
|»» cronExpression|string|true|none||5 段 crontab 表达式|
|»» taskDescription|string|true|none||传给后台 Agent 的自然语言任务|
|»» status|string|true|none||none|
|»» createdBy|integer|true|none||none|
|»» approvalPolicy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalCode|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalStatus|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalApprovedBy|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalTokenId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» approvalRejectedReason|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» nextRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» lastRunAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|status|active|
|status|paused|
|status|pending_approval|
|status|deleted|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdtriggerTask_scheduled_tasks_taskId_trigger_post"></a>

## POST 手动触发定时任务

POST /scheduled-tasks/{taskId}/trigger

立即执行一次定时任务并等待 Agent 临时会话结束。需要 accessToken Cookie。deleted 任务拒绝执行，pending_approval 任务提示等待审批；成功返回 ScheduledTaskRunResponse，失败记录 error 状态。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "taskId": 1,
    "sessionId": "sess_demo",
    "status": "success",
    "startedAt": "2026-08-17T03:00:00Z",
    "finishedAt": "2026-08-17T03:00:02Z",
    "resultSummary": "检查完成",
    "errorMessage": null,
    "tokenUsage": {
      "total": 120
    }
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» taskId|integer|true|none||none|
|»» sessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» status|string|true|none||none|
|»» startedAt|string(date-time)|true|none||none|
|»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» resultSummary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» errorMessage|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» tokenUsage|any|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdlistRuns_scheduled_tasks_taskId_runs_get"></a>

## GET 查询任务运行历史

GET /scheduled-tasks/{taskId}/runs

查询指定任务最近运行记录。需要 accessToken Cookie。taskId 必须存在；limit 默认 50、范围 1..200；返回 {total,items[]}，items 为 ScheduledTaskRunResponse。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|taskId|path|integer| 是 ||定时任务主键|
|limit|query|integer| 否 ||返回条数，1..200，默认 50|

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
        "id": 1,
        "taskId": 1,
        "sessionId": "sess_demo",
        "status": "success",
        "startedAt": "2026-08-17T03:00:00Z",
        "finishedAt": "2026-08-17T03:00:02Z",
        "resultSummary": "检查完成",
        "errorMessage": null,
        "tokenUsage": {
          "total": 120
        }
      }
    ]
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» items|[object]|false|none||none|
|»»» id|integer|true|none||none|
|»»» taskId|integer|true|none||none|
|»»» sessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» status|string|true|none||none|
|»»» startedAt|string(date-time)|true|none||none|
|»»» finishedAt|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string(date-time)|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» resultSummary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» errorMessage|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» tokenUsage|any|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

# Inspection

<a id="opIdlistReports_inspection_reports_get"></a>

## GET 查询巡检报告列表

GET /inspection/reports

分页查询自动巡检报告。需要 accessToken Cookie。page>=1，默认 1；pageSize 1..200，默认 20。data 为 {total,items[]}，items 使用 InspectionReportResponse；findings 是 Agent 从 fullReport 提取的结构化问题列表。报告不存在时列表为空。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|page|query|integer| 否 ||页码，最小 1|
|pageSize|query|integer| 否 ||每页条数，1..200|

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
        "id": 1,
        "sessionId": "sess_demo",
        "status": "completed",
        "summary": "系统状态正常",
        "findings": [],
        "fullReport": "# report",
        "durationMs": 1250,
        "errorMessage": null,
        "createdAt": "2026-08-17T10:00:00Z",
        "updatedAt": "2026-08-17T10:00:01Z"
      }
    ]
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» items|[object]|false|none||none|
|»»» id|integer|true|none||none|
|»»» sessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» status|string|true|none||none|
|»»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» findings|any|false|none||none|
|»»» fullReport|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» durationMs|integer|true|none||none|
|»»» errorMessage|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» createdAt|string(date-time)|true|none||none|
|»»» updatedAt|string(date-time)|true|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdlatestReport_inspection_reports_latest_get"></a>

## GET 查询最新巡检报告

GET /inspection/reports/latest

获取最近一次巡检报告。需要 accessToken Cookie；没有任何报告时 data 为 null。返回对象包含状态、摘要、发现项、原文和耗时。

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
  "data": null
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|any|true|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|object|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» *anonymous*|null|false|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetReport_inspection_reports_reportId_get"></a>

## GET 查询单个巡检报告

GET /inspection/reports/{reportId}

按 reportId 查询单个巡检报告。需要 accessToken Cookie。reportId 必须为整数；不存在时返回 code=0 的业务错误。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|reportId|path|integer| 是 ||巡检报告主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "sessionId": "sess_demo",
    "status": "completed",
    "summary": "系统状态正常",
    "findings": [],
    "fullReport": "# report",
    "durationMs": 1250,
    "errorMessage": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:01Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» sessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» status|string|true|none||none|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» findings|any|false|none||none|
|»» fullReport|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» durationMs|integer|true|none||none|
|»» errorMessage|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdtriggerInspection_inspection_trigger_post"></a>

## POST 手动触发巡检

POST /inspection/trigger

立即启动一次自动巡检并等待 Agent 临时会话完成。需要 accessToken Cookie；服务端使用当前巡检预授权策略，创建报告后返回 InspectionReportResponse。执行期间可能耗时较长；Agent 失败时报告 status/errorMessage 记录失败原因。

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
    "id": 1,
    "sessionId": "sess_demo",
    "status": "completed",
    "summary": "系统状态正常",
    "findings": [],
    "fullReport": "# report",
    "durationMs": 1250,
    "errorMessage": null,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:01Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» sessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» status|string|true|none||none|
|»» summary|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» findings|any|false|none||none|
|»» fullReport|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» durationMs|integer|true|none||none|
|»» errorMessage|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetConfig_inspection_config_get"></a>

## GET 查询巡检调度配置

GET /inspection/config

读取自动巡检调度器配置和 approvalPolicy。需要 accessToken Cookie。返回 intervalMinutes（分钟）、inspectionDocPath、timezone、schedulerStarted 及当前预授权策略；策略文件缺失/损坏时返回默认只读基线。

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
    "inspectionIntervalMinutes": 30,
    "inspectionDocPath": "/workspace/inspection.md",
    "timezone": "Asia/Shanghai",
    "schedulerStarted": true,
    "approvalPolicy": {
      "allowedTools": [
        "runCommand"
      ],
      "allowedCommands": [
        "uname -a"
      ],
      "allowedPaths": [],
      "deniedPaths": [],
      "allowedPrivilegedCommands": [],
      "ttlSeconds": 25200,
      "maxRuns": 100
    }
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» inspectionIntervalMinutes|integer|false|none||none|
|»» inspectionDocPath|string|false|none||none|
|»» timezone|string|false|none||none|
|»» schedulerStarted|boolean|false|none||none|
|»» approvalPolicy|object|false|none||none|
|»»» allowedTools|[string]|false|none||允许无人值守调用的工具名|
|»»» allowedCommands|[string]|false|none||runCommand/runShellCommand 命令前缀白名单；空数组拒绝命令|
|»»» allowedPaths|[string]|false|none||允许访问的路径前缀|
|»»» deniedPaths|[string]|false|none||拒绝访问的路径前缀|
|»»» allowedPrivilegedCommands|[string]|false|none||允许的特权命令白名单|
|»»» ttlSeconds|integer|false|none||审批授权有效期，秒|
|»»» maxRuns|integer|false|none||最多执行次数|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdupdateConfig_inspection_config_put"></a>

## PUT 更新巡检调度配置

PUT /inspection/config

更新自动巡检间隔或无人值守 approvalPolicy。需要 accessToken Cookie。请求体字段均可选：intervalMinutes 1..1440；approvalPolicy 与 ScheduledTaskApprovalPolicy 相同。成功后立即更新调度器并返回合并后的完整配置；提交空对象也会返回当前配置。

> Body 请求参数

```json
{
  "intervalMinutes": 1,
  "approvalPolicy": {
    "allowedTools": [
      "string"
    ],
    "allowedCommands": [
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
    "ttlSeconds": 25200,
    "maxRuns": 100
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» intervalMinutes|body|integer| 否 ||none|
|» approvalPolicy|body|object| 否 ||none|
|»» allowedTools|body|[string]| 否 ||允许无人值守调用的工具名|
|»» allowedCommands|body|[string]| 否 ||runCommand/runShellCommand 命令前缀白名单；空数组拒绝命令|
|»» allowedPaths|body|[string]| 否 ||允许访问的路径前缀|
|»» deniedPaths|body|[string]| 否 ||拒绝访问的路径前缀|
|»» allowedPrivilegedCommands|body|[string]| 否 ||允许的特权命令白名单|
|»» ttlSeconds|body|integer| 否 ||审批授权有效期，秒|
|»» maxRuns|body|integer| 否 ||最多执行次数|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "inspectionIntervalMinutes": 30,
    "inspectionDocPath": "/workspace/inspection.md",
    "timezone": "Asia/Shanghai",
    "schedulerStarted": true,
    "approvalPolicy": {
      "allowedTools": [
        "runCommand"
      ],
      "allowedCommands": [
        "uname -a"
      ],
      "allowedPaths": [],
      "deniedPaths": [],
      "allowedPrivilegedCommands": [],
      "ttlSeconds": 25200,
      "maxRuns": 100
    }
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» inspectionIntervalMinutes|integer|false|none||none|
|»» inspectionDocPath|string|false|none||none|
|»» timezone|string|false|none||none|
|»» schedulerStarted|boolean|false|none||none|
|»» approvalPolicy|object|false|none||none|
|»»» allowedTools|[string]|false|none||允许无人值守调用的工具名|
|»»» allowedCommands|[string]|false|none||runCommand/runShellCommand 命令前缀白名单；空数组拒绝命令|
|»»» allowedPaths|[string]|false|none||允许访问的路径前缀|
|»»» deniedPaths|[string]|false|none||拒绝访问的路径前缀|
|»»» allowedPrivilegedCommands|[string]|false|none||允许的特权命令白名单|
|»»» ttlSeconds|integer|false|none||审批授权有效期，秒|
|»»» maxRuns|integer|false|none||最多执行次数|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

# OpsExperience

<a id="opIdcreatePack_ops_experience_packs_post"></a>

## POST 创建运维经验包

POST /ops-experience/packs

人工创建经验包。需要 accessToken Cookie。title 与 deploymentDoc 必填；category=deployment|fault|optimization|security|negative，riskLevel=low|medium|high，status=enabled|disabled。stages/pitfalls/earlyWarnings 为结构化 JSON 数组。source 固定 human，初始 version=1、qualityScore=100。

> Body 请求参数

```json
{
  "title": "string",
  "category": "deployment",
  "osType": "通用",
  "tags": [
    "string"
  ],
  "deploymentDoc": "string",
  "stages": [
    null
  ],
  "pitfalls": [
    null
  ],
  "earlyWarnings": [
    null
  ],
  "riskLevel": "low",
  "status": "enabled"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» title|body|string| 是 ||none|
|» category|body|string| 否 ||none|
|» osType|body|string| 否 ||none|
|» tags|body|[string]| 否 ||none|
|» deploymentDoc|body|string| 是 ||主体 Markdown 文档|
|» stages|body|[any]| 否 ||none|
|» pitfalls|body|[any]| 否 ||none|
|» earlyWarnings|body|[any]| 否 ||none|
|» riskLevel|body|string| 否 ||none|
|» status|body|string| 否 ||none|

#### 枚举值

|属性|值|
|---|---|
|» category|deployment|
|» category|fault|
|» category|optimization|
|» category|security|
|» category|negative|
|» riskLevel|low|
|» riskLevel|medium|
|» riskLevel|high|
|» status|enabled|
|» status|disabled|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "title": "Nginx 证书续期",
    "category": "deployment",
    "osType": "通用",
    "tags": [
      "nginx",
      "ssl"
    ],
    "deploymentDoc": "# 操作步骤\n1. 检查 nginx -t",
    "stages": [
      {
        "name": "检查",
        "goal": "确认配置有效",
        "steps": [
          "nginx -t"
        ],
        "verify": "返回 successful",
        "pitfallsRef": []
      }
    ],
    "pitfalls": [],
    "earlyWarnings": [],
    "riskLevel": "medium",
    "status": "enabled",
    "source": "human",
    "version": 1,
    "sourceSessionId": null,
    "hitCount": 0,
    "usefulCount": 0,
    "uselessCount": 0,
    "qualityScore": 100,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z",
    "attachments": []
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» title|string|true|none||none|
|»» category|string|true|none||none|
|»» osType|string|true|none||none|
|»» tags|[string]|false|none||none|
|»» deploymentDoc|string|true|none||none|
|»» stages|[any]|false|none||none|
|»» pitfalls|[any]|false|none||none|
|»» earlyWarnings|[any]|false|none||none|
|»» riskLevel|string|true|none||none|
|»» status|string|true|none||none|
|»» source|string|true|none||none|
|»» version|integer|true|none||none|
|»» sourceSessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» hitCount|integer|true|none||none|
|»» usefulCount|integer|true|none||none|
|»» uselessCount|integer|true|none||none|
|»» qualityScore|integer|true|none||none|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|
|»» attachments|[object]|false|none||none|
|»»» id|integer|false|none||none|
|»»» packId|integer|false|none||none|
|»»» filename|string|false|none||none|
|»»» fileType|string|false|none||none|
|»»» storagePath|string|false|none||none|
|»»» sha256|string|false|none||none|
|»»» size|integer|false|none||none|
|»»» arch|string|false|none||none|
|»»» osType|string|false|none||none|
|»»» createdAt|string(date-time)|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|category|deployment|
|category|fault|
|category|optimization|
|category|security|
|category|negative|
|riskLevel|low|
|riskLevel|medium|
|riskLevel|high|
|status|enabled|
|status|disabled|
|source|ai|
|source|human|
|fileType|script|
|fileType|binary|
|fileType|doc|
|fileType|archive|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdlistPacks_ops_experience_packs_get"></a>

## GET 查询运维经验包列表

GET /ops-experience/packs

分页查询经验包。需要 accessToken Cookie。page>=1 默认 1，pageSize 1..200 默认 20；q 对标题、标签和 Markdown 正文按空格分词 AND 匹配；category/status 可过滤。data 为 {total,items[]}，按 qualityScore、id 倒序。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|page|query|integer| 否 ||页码，默认 1|
|pageSize|query|integer| 否 ||每页数量，1..200，默认 20|
|q|query|string| 否 ||关键词，可空格分隔多个词|
|category|query|string| 否 ||分类过滤|
|status|query|string| 否 ||enabled 或 disabled|

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
        "id": 1,
        "title": "Nginx 证书续期",
        "category": "deployment",
        "osType": "通用",
        "tags": [
          "nginx",
          "ssl"
        ],
        "deploymentDoc": "# 操作步骤\n1. 检查 nginx -t",
        "stages": [
          {
            "name": "检查",
            "goal": "确认配置有效",
            "steps": [
              "nginx -t"
            ],
            "verify": "返回 successful",
            "pitfallsRef": []
          }
        ],
        "pitfalls": [],
        "earlyWarnings": [],
        "riskLevel": "medium",
        "status": "enabled",
        "source": "human",
        "version": 1,
        "sourceSessionId": null,
        "hitCount": 0,
        "usefulCount": 0,
        "uselessCount": 0,
        "qualityScore": 100,
        "createdAt": "2026-08-17T10:00:00Z",
        "updatedAt": "2026-08-17T10:00:00Z",
        "attachments": []
      }
    ]
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» total|integer|false|none||none|
|»» items|[object]|false|none||none|
|»»» id|integer|true|none||none|
|»»» title|string|true|none||none|
|»»» category|string|true|none||none|
|»»» osType|string|true|none||none|
|»»» tags|[string]|false|none||none|
|»»» deploymentDoc|string|true|none||none|
|»»» stages|[any]|false|none||none|
|»»» pitfalls|[any]|false|none||none|
|»»» earlyWarnings|[any]|false|none||none|
|»»» riskLevel|string|true|none||none|
|»»» status|string|true|none||none|
|»»» source|string|true|none||none|
|»»» version|integer|true|none||none|
|»»» sourceSessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» hitCount|integer|true|none||none|
|»»» usefulCount|integer|true|none||none|
|»»» uselessCount|integer|true|none||none|
|»»» qualityScore|integer|true|none||none|
|»»» createdAt|string(date-time)|true|none||none|
|»»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|category|deployment|
|category|fault|
|category|optimization|
|category|security|
|category|negative|
|riskLevel|low|
|riskLevel|medium|
|riskLevel|high|
|status|enabled|
|status|disabled|
|source|ai|
|source|human|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdgetPack_ops_experience_packs_packId_get"></a>

## GET 查询运维经验包详情

GET /ops-experience/packs/{packId}

查询单个经验包及附件指针。需要 accessToken Cookie。packId 为主键；不存在时返回 code=0。data 包含正文、阶段/坑/预警、统计计数和 attachments（附件不返回文件内容）。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|packId|path|integer| 是 ||经验包主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "title": "Nginx 证书续期",
    "category": "deployment",
    "osType": "通用",
    "tags": [
      "nginx",
      "ssl"
    ],
    "deploymentDoc": "# 操作步骤\n1. 检查 nginx -t",
    "stages": [
      {
        "name": "检查",
        "goal": "确认配置有效",
        "steps": [
          "nginx -t"
        ],
        "verify": "返回 successful",
        "pitfallsRef": []
      }
    ],
    "pitfalls": [],
    "earlyWarnings": [],
    "riskLevel": "medium",
    "status": "enabled",
    "source": "human",
    "version": 1,
    "sourceSessionId": null,
    "hitCount": 0,
    "usefulCount": 0,
    "uselessCount": 0,
    "qualityScore": 100,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z",
    "attachments": []
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» title|string|true|none||none|
|»» category|string|true|none||none|
|»» osType|string|true|none||none|
|»» tags|[string]|false|none||none|
|»» deploymentDoc|string|true|none||none|
|»» stages|[any]|false|none||none|
|»» pitfalls|[any]|false|none||none|
|»» earlyWarnings|[any]|false|none||none|
|»» riskLevel|string|true|none||none|
|»» status|string|true|none||none|
|»» source|string|true|none||none|
|»» version|integer|true|none||none|
|»» sourceSessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» hitCount|integer|true|none||none|
|»» usefulCount|integer|true|none||none|
|»» uselessCount|integer|true|none||none|
|»» qualityScore|integer|true|none||none|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|
|»» attachments|[object]|false|none||none|
|»»» id|integer|false|none||none|
|»»» packId|integer|false|none||none|
|»»» filename|string|false|none||none|
|»»» fileType|string|false|none||none|
|»»» storagePath|string|false|none||none|
|»»» sha256|string|false|none||none|
|»»» size|integer|false|none||none|
|»»» arch|string|false|none||none|
|»»» osType|string|false|none||none|
|»»» createdAt|string(date-time)|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|category|deployment|
|category|fault|
|category|optimization|
|category|security|
|category|negative|
|riskLevel|low|
|riskLevel|medium|
|riskLevel|high|
|status|enabled|
|status|disabled|
|source|ai|
|source|human|
|fileType|script|
|fileType|binary|
|fileType|doc|
|fileType|archive|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdupdatePack_ops_experience_packs_packId_put"></a>

## PUT 更新运维经验包

PUT /ops-experience/packs/{packId}

部分更新人工经验包。需要 accessToken Cookie。所有字段可选；仅提交非空字段，version 自动加 1；category/riskLevel 使用枚举校验；不存在时返回业务错误。

> Body 请求参数

```json
{
  "title": "string",
  "category": "deployment",
  "osType": "通用",
  "tags": [
    "string"
  ],
  "deploymentDoc": "string",
  "stages": [
    null
  ],
  "pitfalls": [
    null
  ],
  "earlyWarnings": [
    null
  ],
  "riskLevel": "low",
  "status": "enabled"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|packId|path|integer| 是 ||经验包主键|
|body|body|object| 是 ||none|
|» title|body|string| 否 ||none|
|» category|body|string| 否 ||none|
|» osType|body|string| 否 ||none|
|» tags|body|[string]| 否 ||none|
|» deploymentDoc|body|string| 否 ||主体 Markdown 文档|
|» stages|body|[any]| 否 ||none|
|» pitfalls|body|[any]| 否 ||none|
|» earlyWarnings|body|[any]| 否 ||none|
|» riskLevel|body|string| 否 ||none|
|» status|body|string| 否 ||none|

#### 枚举值

|属性|值|
|---|---|
|» category|deployment|
|» category|fault|
|» category|optimization|
|» category|security|
|» category|negative|
|» riskLevel|low|
|» riskLevel|medium|
|» riskLevel|high|
|» status|enabled|
|» status|disabled|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "title": "Nginx 证书续期",
    "category": "deployment",
    "osType": "通用",
    "tags": [
      "nginx",
      "ssl"
    ],
    "deploymentDoc": "# 操作步骤\n1. 检查 nginx -t",
    "stages": [
      {
        "name": "检查",
        "goal": "确认配置有效",
        "steps": [
          "nginx -t"
        ],
        "verify": "返回 successful",
        "pitfallsRef": []
      }
    ],
    "pitfalls": [],
    "earlyWarnings": [],
    "riskLevel": "medium",
    "status": "enabled",
    "source": "human",
    "version": 1,
    "sourceSessionId": null,
    "hitCount": 0,
    "usefulCount": 0,
    "uselessCount": 0,
    "qualityScore": 100,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z",
    "attachments": []
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» title|string|true|none||none|
|»» category|string|true|none||none|
|»» osType|string|true|none||none|
|»» tags|[string]|false|none||none|
|»» deploymentDoc|string|true|none||none|
|»» stages|[any]|false|none||none|
|»» pitfalls|[any]|false|none||none|
|»» earlyWarnings|[any]|false|none||none|
|»» riskLevel|string|true|none||none|
|»» status|string|true|none||none|
|»» source|string|true|none||none|
|»» version|integer|true|none||none|
|»» sourceSessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» hitCount|integer|true|none||none|
|»» usefulCount|integer|true|none||none|
|»» uselessCount|integer|true|none||none|
|»» qualityScore|integer|true|none||none|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|
|»» attachments|[object]|false|none||none|
|»»» id|integer|false|none||none|
|»»» packId|integer|false|none||none|
|»»» filename|string|false|none||none|
|»»» fileType|string|false|none||none|
|»»» storagePath|string|false|none||none|
|»»» sha256|string|false|none||none|
|»»» size|integer|false|none||none|
|»»» arch|string|false|none||none|
|»»» osType|string|false|none||none|
|»»» createdAt|string(date-time)|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|category|deployment|
|category|fault|
|category|optimization|
|category|security|
|category|negative|
|riskLevel|low|
|riskLevel|medium|
|riskLevel|high|
|status|enabled|
|status|disabled|
|source|ai|
|source|human|
|fileType|script|
|fileType|binary|
|fileType|doc|
|fileType|archive|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIddeletePack_ops_experience_packs_packId_delete"></a>

## DELETE 删除运维经验包

DELETE /ops-experience/packs/{packId}

删除经验包及其附件指针。需要 accessToken Cookie。独占附件文件会尝试物理删除，共享哈希文件保留；不可恢复，成功 data=null。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|packId|path|integer| 是 ||经验包主键|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdfeedback_ops_experience_packs_packId_feedback_post"></a>

## POST 反馈运维经验包

POST /ops-experience/packs/{packId}/feedback

记录经验包命中/有用/无用反馈并重算 qualityScore。需要 accessToken Cookie。action 只能是 hit、useful、useless；不存在时返回业务错误。

> Body 请求参数

```json
{
  "action": "hit"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|packId|path|integer| 是 ||经验包主键|
|body|body|object| 是 ||none|
|» action|body|string| 是 ||none|

#### 枚举值

|属性|值|
|---|---|
|» action|hit|
|» action|useful|
|» action|useless|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "title": "Nginx 证书续期",
    "category": "deployment",
    "osType": "通用",
    "tags": [
      "nginx",
      "ssl"
    ],
    "deploymentDoc": "# 操作步骤\n1. 检查 nginx -t",
    "stages": [
      {
        "name": "检查",
        "goal": "确认配置有效",
        "steps": [
          "nginx -t"
        ],
        "verify": "返回 successful",
        "pitfallsRef": []
      }
    ],
    "pitfalls": [],
    "earlyWarnings": [],
    "riskLevel": "medium",
    "status": "enabled",
    "source": "human",
    "version": 1,
    "sourceSessionId": null,
    "hitCount": 0,
    "usefulCount": 0,
    "uselessCount": 0,
    "qualityScore": 100,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z",
    "attachments": []
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» title|string|true|none||none|
|»» category|string|true|none||none|
|»» osType|string|true|none||none|
|»» tags|[string]|false|none||none|
|»» deploymentDoc|string|true|none||none|
|»» stages|[any]|false|none||none|
|»» pitfalls|[any]|false|none||none|
|»» earlyWarnings|[any]|false|none||none|
|»» riskLevel|string|true|none||none|
|»» status|string|true|none||none|
|»» source|string|true|none||none|
|»» version|integer|true|none||none|
|»» sourceSessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» hitCount|integer|true|none||none|
|»» usefulCount|integer|true|none||none|
|»» uselessCount|integer|true|none||none|
|»» qualityScore|integer|true|none||none|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|category|deployment|
|category|fault|
|category|optimization|
|category|security|
|category|negative|
|riskLevel|low|
|riskLevel|medium|
|riskLevel|high|
|status|enabled|
|status|disabled|
|source|ai|
|source|human|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdimportPack_ops_experience_import_post"></a>

## POST 导入运维经验包

POST /ops-experience/import

导入 multipart/form-data ZIP 经验包。需要 accessToken Cookie；字段 file 必填。服务端校验 manifest schemaVersion、逐附件 sha256 并按哈希去重后落库/落盘，重复导入会创建新包记录但复用附件文件。ZIP 非法或校验失败返回业务错误。

> Body 请求参数

```yaml
file: null

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|body|body|object| 是 ||none|
|» file|body|file| 是 ||经验包 ZIP 文件|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 1,
    "title": "Nginx 证书续期",
    "category": "deployment",
    "osType": "通用",
    "tags": [
      "nginx",
      "ssl"
    ],
    "deploymentDoc": "# 操作步骤\n1. 检查 nginx -t",
    "stages": [
      {
        "name": "检查",
        "goal": "确认配置有效",
        "steps": [
          "nginx -t"
        ],
        "verify": "返回 successful",
        "pitfallsRef": []
      }
    ],
    "pitfalls": [],
    "earlyWarnings": [],
    "riskLevel": "medium",
    "status": "enabled",
    "source": "human",
    "version": 1,
    "sourceSessionId": null,
    "hitCount": 0,
    "usefulCount": 0,
    "uselessCount": 0,
    "qualityScore": 100,
    "createdAt": "2026-08-17T10:00:00Z",
    "updatedAt": "2026-08-17T10:00:00Z",
    "attachments": []
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» title|string|true|none||none|
|»» category|string|true|none||none|
|»» osType|string|true|none||none|
|»» tags|[string]|false|none||none|
|»» deploymentDoc|string|true|none||none|
|»» stages|[any]|false|none||none|
|»» pitfalls|[any]|false|none||none|
|»» earlyWarnings|[any]|false|none||none|
|»» riskLevel|string|true|none||none|
|»» status|string|true|none||none|
|»» source|string|true|none||none|
|»» version|integer|true|none||none|
|»» sourceSessionId|any|false|none||none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» *anonymous*|null|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»» hitCount|integer|true|none||none|
|»» usefulCount|integer|true|none||none|
|»» uselessCount|integer|true|none||none|
|»» qualityScore|integer|true|none||none|
|»» createdAt|string(date-time)|true|none||none|
|»» updatedAt|string(date-time)|true|none||none|
|»» attachments|[object]|false|none||none|
|»»» id|integer|false|none||none|
|»»» packId|integer|false|none||none|
|»»» filename|string|false|none||none|
|»»» fileType|string|false|none||none|
|»»» storagePath|string|false|none||none|
|»»» sha256|string|false|none||none|
|»»» size|integer|false|none||none|
|»»» arch|string|false|none||none|
|»»» osType|string|false|none||none|
|»»» createdAt|string(date-time)|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|category|deployment|
|category|fault|
|category|optimization|
|category|security|
|category|negative|
|riskLevel|low|
|riskLevel|medium|
|riskLevel|high|
|status|enabled|
|status|disabled|
|source|ai|
|source|human|
|fileType|script|
|fileType|binary|
|fileType|doc|
|fileType|archive|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIdexportPack_ops_experience_packs_packId_export_get"></a>

## GET 导出运维经验包

GET /ops-experience/packs/{packId}/export

导出经验包为 ZIP 下载。需要 accessToken Cookie。packId 不存在时返回业务错误；成功响应 media_type=application/zip，Content-Disposition 同时提供 ASCII 和 UTF-8 文件名，包含 manifest、deployment.md 和附件。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|packId|path|integer| 是 ||经验包主键|

> 返回示例

> 200 Response

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|返回导出的经验包 ZIP；Content-Disposition 提供下载文件名|string|

<a id="opIdknowledgeSummary_ops_experience_knowledge_summary_get"></a>

## GET 读取经验知识摘要

GET /ops-experience/knowledge-summary

读取启用中经验包的紧凑摘要文本。需要 accessToken Cookie。limit 1..50 默认 20；经验库为空时返回冷启动指引，查询异常时返回空字符串，不阻塞会话。

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|limit|query|integer| 否 ||摘要条数，1..50，默认 20|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": "[deployment] Nginx 证书续期 | nginx,ssl | 检查 certbot"
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|string|true|none||none|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

<a id="opIduploadAttachment_ops_experience_packs_packId_attachments_post"></a>

## POST 上传经验包附件

POST /ops-experience/packs/{packId}/attachments

向已有经验包上传 multipart/form-data 附件。需要 accessToken Cookie；file 必填，fileType 可选 script|binary|doc|archive（默认 doc），arch/osType 默认 通用。文件名不能含路径分隔符；同名同内容幂等，同名不同内容拒绝；按 sha256 全局去重。

> Body 请求参数

```yaml
fileType: doc
arch: loongarch64
osType: 麒麟

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|accessToken|cookie|string| 否 ||none|
|refreshToken|cookie|string| 否 ||none|
|packId|path|integer| 是 ||经验包主键|
|body|body|object| 是 ||none|
|» file|body|file| 是 ||附件内容|
|» fileType|body|string| 否 ||script|binary|doc|archive|
|» arch|body|string| 否 ||架构标签|
|» osType|body|string| 否 ||系统标签|

> 返回示例

> 200 Response

```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "id": 10,
    "packId": 1,
    "filename": "runbook.md",
    "fileType": "doc",
    "storagePath": "1/runbook.md",
    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "size": 128,
    "arch": "通用",
    "osType": "通用",
    "createdAt": "2026-08-17T10:00:00Z"
  }
}
```

> 401 Response

```json
{
  "code": 40101,
  "msg": "未携带accessToken",
  "data": null
}
```

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "body"
      ],
      "msg": "参数校验失败",
      "type": "value_error"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|缺少或非法 accessToken Cookie；GlobalInterceptor 返回 code=40101|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|FastAPI/Pydantic 参数校验失败；data 通常为空或包含 validation details|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|
|»» id|integer|false|none||none|
|»» packId|integer|false|none||none|
|»» filename|string|false|none||none|
|»» fileType|string|false|none||none|
|»» storagePath|string|false|none||none|
|»» sha256|string|false|none||none|
|»» size|integer|false|none||none|
|»» arch|string|false|none||none|
|»» osType|string|false|none||none|
|»» createdAt|string(date-time)|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|fileType|script|
|fileType|binary|
|fileType|doc|
|fileType|archive|

状态码 **401**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|null|true|none||none|

状态码 **422**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||业务码，1 成功，0 业务失败，40101/40102 表示 Cookie 鉴权失败|
|» msg|string|true|none||面向用户的提示信息|
|» data|object|true|none||none|

# 数据模型

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

