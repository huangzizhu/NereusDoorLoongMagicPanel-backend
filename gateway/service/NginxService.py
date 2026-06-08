from gateway.Singleton import Singleton, singletonInit
from utils.toolFunction import (
    checkNginxInstalled,
    getNginxStatus,
    generateStaticSiteConfig,
    generateProxyConfig,
    detectNginxLayout,
    _getNginxConfigWriteInfo,
    _getNginxSiteDeleteInfo,
)
from utils.toolFunction.exceptions import (
    PermissionDeniedException,
    ServiceUnavailableException,
    ToolExecutionException,
)
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from Exception.ExecutePermissionDeniedException import ExecutePermissionDeniedException
from gateway.service.PrivilegedAgentClient import (
    PrivilegedAgentClient,
    PrivilegedAgentRemoteError,
)
from privileged_agent.models import PrivilegedAction


class NginxService(Singleton):
    @singletonInit
    def __init__(self):
        self.privilegedAgentClient = PrivilegedAgentClient()

    def _agentContext(self):
        return self.privilegedAgentClient.defaultContext("gateway.nginx")

    def _callPrivilegedAgent(self, action: PrivilegedAction, payload: dict, userMessage: str):
        try:
            return self.privilegedAgentClient.call(action, payload, self._agentContext())
        except PrivilegedAgentRemoteError as e:
            if e.code in ["PERMISSION_DENIED", "PROXY_PERMISSION_DENIED"]:
                raise ExecutePermissionDeniedException(
                    innerMessage=e.details or e.message,
                    userMessage=userMessage,
                    cause=e,
                )
            raise BuiltinToolExecutionException(
                innerMessage=e.details or e.message,
                userMessage=userMessage,
                cause=e,
            )

    def _wrap(self, userMessage: str, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(
                innerMessage=e.innerMessage,
                userMessage=userMessage,
                cause=e,
            )
        except ServiceUnavailableException as e:
            raise BuiltinToolExecutionException(
                innerMessage=e.innerMessage,
                userMessage=e.userMessage or userMessage,
                cause=e,
            )
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(
                innerMessage=e.innerMessage,
                userMessage=userMessage,
                cause=e,
            )

    # ── 基础信息（直连工具函数） ──

    def getInstallInfo(self):
        return self._wrap("读取 Nginx 安装信息失败", checkNginxInstalled)

    def getStatus(self):
        return self._wrap("读取 Nginx 运行状态失败", getNginxStatus)

    # ── 配置测试 & 控制（特权代理） ──

    def testConfig(self):
        return self._callPrivilegedAgent(
            PrivilegedAction.NGINX_TEST_CONFIG, {},
            "测试 Nginx 配置失败",
        )

    def reload(self):
        return self._callPrivilegedAgent(
            PrivilegedAction.NGINX_RELOAD, {},
            "重载 Nginx 失败",
        )

    def restart(self):
        return self._callPrivilegedAgent(
            PrivilegedAction.NGINX_RESTART, {},
            "重启 Nginx 失败",
        )

    # ── 站点列表 ──

    def getSiteList(self):
        """
        获取站点列表。
        读操作用直连工具函数（nginx 配置通常 644 权限可读），
        不需要走 PrivilegedAgent，效率更高。
        """
        from utils.toolFunction.tools.ops.misc.nginx_tools import getNginxSiteList as _getSiteList
        return self._wrap("读取 Nginx 站点列表失败", _getSiteList)

    # ── 获取站点详细配置 ──

    def getSiteConfig(self, domain: str) -> dict:
        """
        获取指定站点的配置文件原文 + 解析字段。
        读操作用直连工具函数。
        """
        from utils.toolFunction.tools.ops.misc.nginx_tools import getNginxSiteConfig as _getConfig
        return self._wrap(f"读取站点 {domain} 配置失败", _getConfig, domain)

    # ── 修改站点配置（原子化：备份→写入→测试→回滚/重载） ──

    def updateSiteConfigAtomic(self, domain: str, content: str) -> dict:
        """
        修改站点配置，原子化操作：
        备份 → 写入 → nginx -t → 失败回滚 / 成功 reload
        """
        from utils.toolFunction.tools.ops.misc.nginx_tools import _getNginxSiteUpdateInfo
        updateInfo = _getNginxSiteUpdateInfo(domain, content)

        return self._callPrivilegedAgent(
            PrivilegedAction.NGINX_SAVE_CONFIG_ATOMIC,
            {
                "targetPath": updateInfo["targetPath"],
                "content": content,
                "layoutType": updateInfo.get("layoutType", ""),
                "siteName": updateInfo.get("siteName", ""),
            },
            f"修改站点 {domain} 配置失败",
        )

    # ── 修改站点配置（旧版文本编辑，保留 LLM agent 入口） ──

    def updateSiteConfig(self, domain: str, content: str) -> dict:
        """
        修改指定站点的配置内容。
        通过 PrivilegedAgent 写文件 → nginx -t → reload。
        """
        from utils.toolFunction.tools.ops.misc.nginx_tools import _getNginxSiteUpdateInfo
        updateInfo = _getNginxSiteUpdateInfo(domain, content)

        # 写入 + nginx -t
        self._callPrivilegedAgent(
            PrivilegedAction.NGINX_SAVE_CONFIG,
            {
                "targetPath": updateInfo["targetPath"],
                "content": content,
                "layoutType": updateInfo.get("layoutType", ""),
                "siteName": updateInfo.get("siteName", ""),
            },
            f"修改站点 {domain} 配置失败",
        )

        # reload
        self._callPrivilegedAgent(
            PrivilegedAction.NGINX_RELOAD, {},
            "重载 Nginx 失败",
        )

        return {
            "domain": domain,
            "configPath": updateInfo["targetPath"],
            "isUpdated": True,
            "isReloaded": True,
        }

    # ── 创建站点 ──

    def createSite(self, domain: str, mode: str, listenPort: int,
                   rootPath: str | None = None, proxyPass: str | None = None) -> dict:
        """
        创建 Nginx 站点（通过 PrivilegedAgent 写配置）。
        """
        # 1. 生成配置内容（纯逻辑，不需要提权）
        if mode == "static":
            if not rootPath:
                raise BuiltinToolExecutionException(
                    userMessage="静态站点必须提供 rootPath",
                    innerMessage="rootPath is required for static site",
                )
            configContent = generateStaticSiteConfig(domain, rootPath, listenPort)
        elif mode == "reverse_proxy":
            if not proxyPass:
                raise BuiltinToolExecutionException(
                    userMessage="反向代理必须提供 proxyPass",
                    innerMessage="proxyPass is required for reverse proxy",
                )
            configContent = generateProxyConfig(domain, proxyPass, listenPort)
        else:
            raise BuiltinToolExecutionException(
                userMessage=f"不支持的模式: {mode}",
                innerMessage=f"Unsupported mode: {mode}",
            )

        # 2. 获取写入信息
        writeInfo = _getNginxConfigWriteInfo(domain, configContent)

        # 3. 通过 PrivilegedAgent 写入 + 测试（传递 layout 信息用于创建 symlink）
        self._callPrivilegedAgent(
            PrivilegedAction.NGINX_SAVE_CONFIG,
            {
                "targetPath": writeInfo["targetPath"],
                "content": configContent,
                "layoutType": writeInfo.get("layoutType", ""),
                "siteName": writeInfo.get("siteName", ""),
            },
            "创建 Nginx 站点失败",
        )

        # 4. 重载
        self._callPrivilegedAgent(
            PrivilegedAction.NGINX_RELOAD, {},
            "重载 Nginx 失败",
        )

        layout = detectNginxLayout()
        return {
            "domain": domain,
            "mode": mode,
            "listenPort": listenPort,
            "configPath": writeInfo["targetPath"],
            "enabledPath": writeInfo["targetPath"],
            "rootPath": rootPath if mode == "static" else None,
            "proxyPass": proxyPass if mode == "reverse_proxy" else None,
            "isEnabled": True,
            "isReloaded": True,
        }

    # ── 删除站点 ──

    def deleteSite(self, configName: str) -> dict:
        """删除 Nginx 站点（通过 PrivilegedAgent）。"""
        deleteInfo = _getNginxSiteDeleteInfo(configName)

        self._callPrivilegedAgent(
            PrivilegedAction.NGINX_DELETE_SITE,
            {
                "configPath": deleteInfo["configPath"],
                "layoutType": deleteInfo.get("layoutType", ""),
                "siteName": deleteInfo.get("siteName", ""),
            },
            "删除 Nginx 站点失败",
        )

        return {
            "configName": configName,
            "configPath": deleteInfo["configPath"],
            "isDeleted": True,
            "isReloaded": True,
        }

    # ── SSL ──

    def applySsl(self, domain: str, email: str) -> dict:
        """申请 SSL 证书（通过 PrivilegedAgent）。"""
        # 在应用层先检测 webroot
        configPath_result = self._callPrivilegedAgent(
            PrivilegedAction.NGINX_READ_FILE,
            {"filePath": f"/etc/nginx/sites-enabled/{domain}.conf"},
            "读取站点配置失败",
        )
        # 使用工具函数解析 webroot
        from utils.toolFunction.tools.ops.misc.nginx_tools import _resolveWebrootFromConfig
        # 写一个临时文件来解析（更干净的方式：把内容传给工具函数）
        content = configPath_result.get("content", "")
        import re, tempfile, os
        tmp = tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False)
        tmp.write(content)
        tmp.close()
        try:
            webroot = _resolveWebrootFromConfig(tmp.name, domain)
        finally:
            os.unlink(tmp.name)

        return self._callPrivilegedAgent(
            PrivilegedAction.NGINX_APPLY_SSL,
            {"domain": domain, "email": email, "webroot": webroot},
            "申请 SSL 证书失败",
        )

    def configSsl(self, domain: str, certPath: str, keyPath: str) -> dict:
        """写入 HTTPS 配置（通过 PrivilegedAgent）。"""
        # 生成 SSL 配置内容
        from utils.toolFunction.tools.ops.misc.nginx_tools import (
            _resolveWebrootFromConfig, _findSiteConfigPath, configSslForNginx
        )
        # 读取现有配置
        config_path = _findSiteConfigPath(domain)
        if not config_path:
            raise BuiltinToolExecutionException(
                userMessage=f"找不到域名 {domain} 的配置",
                innerMessage="config not found",
            )
        content_result = self._callPrivilegedAgent(
            PrivilegedAction.NGINX_READ_FILE,
            {"filePath": config_path},
            "读取站点配置失败",
        )
        content = content_result.get("content", "")
        import re, tempfile, os
        tmp = tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False)
        tmp.write(content)
        tmp.close()
        try:
            webroot = _resolveWebrootFromConfig(tmp.name, domain)
        finally:
            os.unlink(tmp.name)

        # 解析 proxy_pass
        proxyMatch = re.search(r"proxy_pass\s+([^;]+);", content)

        if proxyMatch:
            siteLocation = f"""location / {{
        proxy_pass {proxyMatch.group(1).strip()};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}"""
        else:
            siteLocation = f"""root {webroot};
    index index.html;

    location / {{
        try_files $uri $uri/ =404;
    }}"""

        configContent = f"""server {{
    listen 80;
    server_name {domain};

    location /.well-known/acme-challenge/ {{
        root {webroot};
    }}

    location / {{
        return 301 https://$host$request_uri;
    }}
}}

server {{
    listen 443 ssl;
    server_name {domain};

    ssl_certificate {certPath};
    ssl_certificate_key {keyPath};

    {siteLocation}
}}"""

        # 获取写入路径
        from utils.toolFunction.tools.ops.misc.nginx_tools import _getNginxConfigWriteInfo
        writeInfo = _getNginxConfigWriteInfo(domain, configContent)

        return self._callPrivilegedAgent(
            PrivilegedAction.NGINX_CONFIG_SSL,
            {"targetPath": writeInfo["targetPath"], "content": configContent},
            "配置 SSL 失败",
        )

    def renewSsl(self, domain: str) -> dict:
        """续期 SSL 证书（通过 PrivilegedAgent）。"""
        return self._callPrivilegedAgent(
            PrivilegedAction.NGINX_RENEW_SSL,
            {"domain": domain},
            "续期 SSL 证书失败",
        )
