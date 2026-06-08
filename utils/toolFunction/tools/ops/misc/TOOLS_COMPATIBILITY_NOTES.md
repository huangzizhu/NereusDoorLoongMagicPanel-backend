# Misc Tools Compatibility Notes

本文记录 `database_tools.py`、`docker_tools.py`、`nginx_tools.py` 当前每个函数的兼容性、鲁棒性和 API 接入状态。

## 架构说明

- **LLM Agent 入口**：函数可直接调用，内部通过 `useSudo=True` 提权
- **REST API 入口**：走 Service → PrivilegedAgent（UNIX socket 根进程提权）
- **双平台适配**：`detectNginxLayout()` 自动检测 Debian/Ubuntu 或 RHEL/Kylin 布局
- **LoongArch 降级**：certbot 等不可用功能返回明确错误提示

判定口径：

- `Ubuntu x86`：以常见 Ubuntu 22.04/24.04 x86_64 宿主机为基线
- `Kylin loongarch`：以 LoongArch 麒麟 / openEuler 风格宿主机为基线
- `API 接入`：`已接入` / `可接` / `有限` / `否` / `🔴高危`

---

## 📊 总体进度

| 模块 | 总函数 | 已接入 API | 未接入（高危/不可用） | 完成率 |
|------|-------|-----------|-------------------|--------|
| **Database** | 9 | 8 | 0 | **89%** |
| **Docker** | 20 | 15 | 5（4 个高危 + 1 个未实现） | **75%** |
| **Nginx** | 17 | 12 | 0 | **71%** |
| **合计** | **46** | **35** | **5** | **76%** |

### 高危/不可用函数摘要

| 函数 | 模块 | 风险等级 | 原因 | 建议 |
|------|------|---------|------|------|
| `updateContainerEnv` | Docker | 🔴高危 | 调用 `reCreateDockerContainer`，会停服重建容器，环境变量可能丢失 | 前端引导用户删了重建 |
| `updateContainerPorts` | Docker | 🔴高危 | 同上，端口映射可能因重建而不一致 | 前端引导用户删了重建 |
| `updateContainerVolumes` | Docker | 🔴高危 | 同上，数据卷挂载可能遗漏 | 前端引导用户删了重建 |
| `reCreateDockerContainer` | Docker | 🔴高危 | 停旧→备份→建新→删备份，有数据丢失和配置偏差风险 | 仅在确认后使用 |
| `connectDocker` | Docker | 🔴不可用 | 函数体为 `pass`，未实现 | 待后续设计远程 Docker 管理 |

---

## database_tools.py

| 函数 | 用途 | Ubuntu x86 | Kylin loongarch | 提权方式 | API 接入 |
|------|------|-----------|----------------|----------|---------|
| `checkDatabaseInstalled` | 检测数据库命令和版本 | 高 | 高 | 直连 | **已接入** `GET /database/install/{type}` |
| `getDatabaseStatus` | 检测服务运行状态 | 中高 | 中高 | 直连 | **已接入** `GET /database/status/{type}` |
| `testMysqlConnection` | 测试 MySQL 连接 | 高 | 中高 | 直连 | **已接入** `POST /database/mysql/test-connection` |
| `_getCreateDbInfo` | 返回建库 SQL 参数（内部） | 高 | 高 | — | 内部辅助 |
| `_getCreateUserInfo` | 返回建用户参数（内部） | 高 | 高 | — | 内部辅助 |
| `_getDatabaseListSql` | 返回查询 SQL（内部） | 高 | 高 | — | 内部辅助 |
| `createMysqlDatabase` | 创建 MySQL 数据库 | 中 | 中低 | **PrivilegedAgent** | **已接入** `POST /database/mysql/database` |
| `createMysqlUserAndGrant` | 创建用户并授权 | 中 | 中低 | **PrivilegedAgent** | **已接入** `POST /database/mysql/user` |
| `getMysqlDatabaseList` | 获取数据库列表 | 中 | 中低 | **PrivilegedAgent** | **已接入** `GET /database/mysql/databases` |

---

## docker_tools.py

| 函数 | 用途 | Ubuntu x86 | Kylin loongarch | 提权方式 | API 接入 |
|------|------|-----------|----------------|----------|---------|
| `checkDockerInstalled` | 检测 Docker 和版本 | 高 | 中高 | 直连 | **已接入** `GET /docker/install` |
| `getDockerContainers` | 获取容器列表（运行中） | 中高 | 中高 | 直连 | **已接入** `GET /docker/containers` |
| `getDockerContainerList` | 获取全部容器列表 | 中高 | 中高 | 直连 | **已接入** `GET /docker/container/list` |
| `getDockerImageList` | 获取镜像列表 | 高 | 中高 | 直连 | **已接入** `GET /docker/images` |
| `getDockerContainerInfo` | 获取容器详情 | 高 | 中高 | 直连 | **已接入** `GET /docker/container/{id}` |
| `getDockerContainerLogs` | 获取容器日志 | 高 | 中高 | 直连 | **已接入** `GET /docker/container/{id}/logs` |
| `startDockerContainer` | 启动容器 | 高 | 中高 | 直连 | **已接入** `POST /docker/container/{id}/start` |
| `stopDockerContainer` | 停止容器 | 高 | 中高 | 直连 | **已接入** `POST /docker/container/{id}/stop` |
| `restartDockerContainer` | 重启容器 | 高 | 中高 | 直连 | **已接入** `POST /docker/container/{id}/restart` |
| `deleteDockerContainer` | 删除容器 | 高 | 中高 | 直连 | **已接入** `DELETE /docker/container/{id}` |
| `pullDockerImage` | 拉取镜像（支持 `--platform` + `registry`） | 高 | 中高 | 直连 | **已接入** `POST /docker/image/pull` |
| `searchDockerImages` | 搜索 Docker Hub 镜像 | 高 | 中高 | 直连 | **已接入** `GET /docker/search?q=nginx` |
| `getDockerDaemonConfig` | 读取 daemon.json 配置 | 高 | 高 | 直连 | **已接入** `GET /docker/mirror` |
| `_buildDaemonConfigPayload` | 生成立即加速配置载荷（内部） | 高 | 高 | — | 内部辅助 |
| `setDockerRegistryMirror` | 设置镜像加速站（重启 Docker） | 中高 | 中高 | **PrivilegedAgent** | **已接入** `POST /docker/mirror` |
| `createDockerContainer` | 创建容器（支持 platform/restartPolicy） | 中高 | 中 | 直连 | **已接入** `POST /docker/container` |
| `updateContainerEnv` | 更新容器环境变量 | 中 | 中 | 直连（高危） | **🔴高危** — 调用 `reCreateDockerContainer` 停服重建，环境变量可能丢失 |
| `updateContainerPorts` | 更新端口映射 | 中 | 中 | 直连（高危） | **🔴高危** — 同上，端口映射可能不一致 |
| `updateContainerVolumes` | 更新卷挂载 | 中 | 中 | 直连（高危） | **🔴高危** — 同上，数据卷挂载可能遗漏 |
| `reCreateDockerContainer` | 重建容器（有回滚） | 中 | 中低 | 直连（高危） | **🔴高危** — 停服窗口 + 配置偏差风险 |
| `connectDocker` | 连接远程 Docker | — | — | — | **🔴不可用** — 函数体为 `pass`，未实现 |

---

## nginx_tools.py

| 函数 | 用途 | Ubuntu x86 | Kylin loongarch | 提权方式 | API 接入 |
|------|------|-----------|----------------|----------|---------|
| `checkNginxInstalled` | 检测 Nginx 安装和路径 | 高 | 中高 | 直连 | **已接入** `GET /nginx/install` |
| `getNginxStatus` | 获取 Nginx 运行状态 | 中高 | 中高 | 直连 | **已接入** `GET /nginx/status` |
| `testNginxConfig` | 测试配置合法性 | 高 | 中高 | **PrivilegedAgent** | **已接入** `POST /nginx/test-config` |
| `reloadNginx` | 重载 Nginx | 高 | 中高 | **PrivilegedAgent** | **已接入** `POST /nginx/reload` |
| `restartNginx` | 重启 Nginx | 高 | 中高 | **PrivilegedAgent** | **已接入** `POST /nginx/restart` |
| `detectNginxLayout` | 检测配置目录布局 | 高 | 高 | 直连 | 内部基准函数 |
| `generateStaticSiteConfig` | 生成静态站配置模板 | 高 | 高 | — | 内部模板函数 |
| `generateProxyConfig` | 生成反代配置模板 | 高 | 高 | — | 内部模板函数 |
| `saveNginxConfig` | 写入配置（自适应布局） | 高 | 中 | **PrivilegedAgent** | 被 `createSite` 内部调用 |
| `createNginxSite` | 创建站点（自适应布局） | 中高 | 中 | **PrivilegedAgent** | **已接入** `POST /nginx/site` |
| `getNginxSiteConfig` | 查看站点详细配置 | 高 | 中高 | 直连 | **已接入** `GET /nginx/site/{domain}` |
| `updateNginxSiteConfig` | 修改站点配置（文本方式） | 中高 | 中 | **PrivilegedAgent** | **已接入** `PUT /nginx/site/{domain}` |
| （下载文件） | 下载站点配置文件 | 高 | 中高 | 直连 | **已接入** `GET /nginx/site/{domain}/download` |
| （上传文件） | 上传并原子化应用配置 | 中高 | 中 | **PrivilegedAgent** | **已接入** `POST /nginx/site/{domain}/upload` |
| `getNginxSiteList` | 获取站点列表（自适应布局） | 高 | 中 | **PrivilegedAgent** | **已接入** `GET /nginx/sites` |
| `deleteNginxSite` | 删除站点（自适应布局） | 中高 | 中 | **PrivilegedAgent** | **已接入** `DELETE /nginx/site/{name}` |
| `applySslCertificate` | 申请 Let's Encrypt 证书 | 中高 | ⚠️ 低 | **PrivilegedAgent** | **已接入** `POST /nginx/ssl/apply` |
| `configSslForNginx` | 写入 HTTPS 配置（自适应布局） | 中高 | 中 | **PrivilegedAgent** | **已接入** `POST /nginx/ssl/config` |
| `renewSslCertificate` | 续期 SSL 证书 | 中高 | ⚠️ 低 | **PrivilegedAgent** | **已接入** `POST /nginx/ssl/renew` |
| `_getNginxConfigWriteInfo` | 返回写入路径+内容（内部） | 高 | 高 | — | 内部辅助 |
| `_getNginxSiteDeleteInfo` | 返回删除路径（内部） | 高 | 高 | — | 内部辅助 |

---

## LoongArch Kylin 注意事项

1. **Nginx 配置目录**：Kylin 使用 `/etc/nginx/conf.d/` 而非 `sites-enabled/`，`detectNginxLayout()` 自动检测，所有路径操作自适应
2. **certbot 生态**：LoongArch 上 certbot 官方不支持原生包，需 `pip3 install certbot` 安装；如未安装返回明确降级提示
3. **MySQL 认证**：Kylin 上 MySQL/MariaDB socket 认证可能不同，已统一通过 PrivilegedAgent 处理
4. **Docker 架构**：`--platform linux/loongarch64` 支持在 pull 和 create 时指定，避免拉取 x86 镜像在 LoongArch 上运行失败
