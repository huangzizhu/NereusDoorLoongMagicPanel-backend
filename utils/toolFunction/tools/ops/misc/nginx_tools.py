"""
Nginx 管理工具函数。

架构说明（双入口）：
  - LLM Agent 入口：函数直接调用，内部通过 useSudo=True 提权（回退兼容）
  - REST API 入口：走 Service → PrivilegedAgent（socket 根进程），函数提供纯逻辑+路径解析

双平台适配：
  - detectNginxLayout() 自动检测 Debian/Ubuntu（sites-enabled）或 RHEL/Kylin（conf.d）布局
  - _is_loongarch() 检测 LoongArch，certbot 相关操作在此架构上静默降级
"""

import os
import platform
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path

from utils.toolFunction.exceptions import (
    ServiceUnavailableException,
    ToolExecutionException,
)
from utils.toolFunction.models.ops.misc.nginx_models import (
    NginxInstallInfo,
    NginxLayout,
    NginxLayoutType,
    NginxSiteCreateResult,
    NginxSiteDeleteResult,
    NginxSiteInfo,
    NginxSslApplyResult,
    NginxSslConfigResult,
    NginxSslRenewResult,
    NginxSiteMode,
    NginxStatus,
)
from utils.toolFunction.tools.ops._command_runner import runCommand

SITES_ENABLED_DIR = Path("/etc/nginx/sites-enabled")
SITES_AVAILABLE_DIR = Path("/etc/nginx/sites-available")
CONF_D_DIR = Path("/etc/nginx/conf.d")
NGINX_CONF_DIR = Path("/etc/nginx")
LETSENCRYPT_LIVE_DIR = Path("/etc/letsencrypt/live")
DEFAULT_WEBROOT_BASE = Path("/var/www")

# ── 缓存：detectNginxLayout 结果，同进程内只检测一次 ──
_nginx_layout_cache: NginxLayout | None = None


# ═══════════════════════════════════════════════════════════
# 平台检测
# ═══════════════════════════════════════════════════════════

def _get_arch() -> str:
    return platform.machine()


def _is_loongarch() -> bool:
    return _get_arch().startswith("loongarch")


def _is_debian_like() -> bool:
    """检测是否为 Debian/Ubuntu 系（用于 certbot 包管理器提示）"""
    try:
        result = runCommand(["which", "apt"], checkReturnCode=False)
        return result.returncode == 0
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# 布局检测
# ═══════════════════════════════════════════════════════════

def detectNginxLayout() -> NginxLayout:
    """检测当前系统的 Nginx 配置目录布局。"""
    global _nginx_layout_cache
    if _nginx_layout_cache is not None:
        return _nginx_layout_cache

    mainConfigPath = None
    try:
        result = runCommand(["nginx", "-t"], checkReturnCode=False)
        cMatch = re.search(r"configuration file (\S+)", result.stderr)
        if cMatch:
            mainConfigPath = cMatch.group(1)
    except Exception:
        pass

    nginxConfDir = str(NGINX_CONF_DIR)

    if SITES_ENABLED_DIR.exists() and SITES_AVAILABLE_DIR.exists():
        layout = NginxLayout(
            layoutType=NginxLayoutType.SITES_ENABLED,
            configDir=str(SITES_AVAILABLE_DIR),
            enabledDir=str(SITES_ENABLED_DIR),
            availableDir=str(SITES_AVAILABLE_DIR),
            mainConfigPath=mainConfigPath,
            nginxConfDir=nginxConfDir,
        )
    elif CONF_D_DIR.exists():
        layout = NginxLayout(
            layoutType=NginxLayoutType.CONF_D,
            configDir=str(CONF_D_DIR),
            mainConfigPath=mainConfigPath,
            nginxConfDir=nginxConfDir,
        )
    else:
        if SITES_ENABLED_DIR.exists():
            layout = NginxLayout(
                layoutType=NginxLayoutType.SITES_ENABLED,
                configDir=str(SITES_AVAILABLE_DIR),
                enabledDir=str(SITES_ENABLED_DIR),
                availableDir=str(SITES_AVAILABLE_DIR),
                mainConfigPath=mainConfigPath,
                nginxConfDir=nginxConfDir,
            )
        else:
            layout = NginxLayout(
                layoutType=NginxLayoutType.UNKNOWN,
                configDir=str(NGINX_CONF_DIR),
                mainConfigPath=mainConfigPath,
                nginxConfDir=nginxConfDir,
            )

    _nginx_layout_cache = layout
    return layout


# ═══════════════════════════════════════════════════════════
# 基础检测
# ═══════════════════════════════════════════════════════════

def checkNginxInstalled() -> NginxInstallInfo:
    try:
        result = runCommand(["nginx", "-v"], checkReturnCode=False)
        output = result.stderr.strip() or result.stdout.strip()

        version = None
        vMatch = re.search(r"nginx/([\d.]+)", output)
        if vMatch:
            version = vMatch.group(1)

        configPath = None
        testResult = runCommand(["nginx", "-t"], checkReturnCode=False)
        cMatch = re.search(r"configuration file (\S+)", testResult.stderr)
        if cMatch:
            configPath = cMatch.group(1)

        return NginxInstallInfo(
            isInstalled=True, version=version, configPath=configPath
        )
    except ToolExecutionException:
        return NginxInstallInfo(isInstalled=False)


def getNginxStatus() -> NginxStatus:
    if not checkNginxInstalled().isInstalled:
        raise ServiceUnavailableException("Nginx 未安装")

    isRunning = False
    workerCount = 0

    try:
        result = runCommand(["systemctl", "is-active", "nginx"], checkReturnCode=False)
        isRunning = result.stdout.strip() == "active"
    except ToolExecutionException:
        pass

    if isRunning:
        try:
            result = runCommand(
                ["pgrep", "-c", "-f", "nginx: worker"], checkReturnCode=False
            )
            workerCount = int(result.stdout.strip())
        except (ToolExecutionException, ValueError):
            pass

    activeConnections = None
    try:
        resp = urllib.request.urlopen("http://127.0.0.1/nginx_status", timeout=2)
        content = resp.read().decode()
        connMatch = re.search(r"Active connections:\s*(\d+)", content)
        if connMatch:
            activeConnections = int(connMatch.group(1))
    except Exception:
        pass

    return NginxStatus(
        isRunning=isRunning,
        workerProcessCount=workerCount,
        activeConnections=activeConnections,
        requestsPerSecond=None,
    )


# ═══════════════════════════════════════════════════════════
# 配置模板生成
# ═══════════════════════════════════════════════════════════

def generateStaticSiteConfig(domain: str, rootPath: str, listenPort: int = 80) -> str:
    return f"""server {{
    listen {listenPort};
    server_name {domain};
    root {rootPath};
    index index.html;
    location / {{
        try_files $uri $uri/ =404;
    }}
}}"""


def generateProxyConfig(domain: str, proxyPass: str, listenPort: int = 80) -> str:
    return f"""server {{
    listen {listenPort};
    server_name {domain};
    location /.well-known/acme-challenge/ {{
        root {DEFAULT_WEBROOT_BASE / domain};
    }}
    location / {{
        proxy_pass {proxyPass};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}"""


# ═══════════════════════════════════════════════════════════
# 路径工具
# ═══════════════════════════════════════════════════════════

def _normalizeSiteName(configName: str) -> str:
    siteName = configName.replace("*.", "").replace("/", "_")
    if siteName.endswith(".conf"):
        siteName = siteName[:-5]
    return siteName


def _resolveConfigPath(configName: str) -> str:
    """
    根据检测到的布局，返回配置文件的完整写入路径。
    Debian: /etc/nginx/sites-available/{name}.conf
    RHEL:   /etc/nginx/conf.d/{name}.conf
    """
    layout = detectNginxLayout()
    siteName = _normalizeSiteName(configName)
    return str(Path(layout.configDir) / f"{siteName}.conf")


def _resolveEnabledPath(configName: str) -> str | None:
    """
    返回启用目录的路径（仅 Debian 风格有 symlink 或直接写 enabled）。
    RHEL 风格 conf.d 即启用，无需分离。
    """
    layout = detectNginxLayout()
    siteName = _normalizeSiteName(configName)
    if layout.enabledDir:
        return str(Path(layout.enabledDir) / f"{siteName}.conf")
    return _resolveConfigPath(configName)


def _findSiteConfigPath(domain: str) -> str | None:
    """
    自适应双布局的配置查找。
    Debian: 搜 sites-enabled → sites-available
    RHEL:   搜 conf.d
    """
    layout = detectNginxLayout()
    siteName = _normalizeSiteName(domain)
    candidates = []

    if layout.enabledDir:
        candidates.append(Path(layout.enabledDir) / f"{siteName}.conf")
    if layout.availableDir:
        candidates.append(Path(layout.availableDir) / f"{siteName}.conf")
    # 也搜 configDir
    candidates.append(Path(layout.configDir) / f"{siteName}.conf")

    # 去重
    seen = set()
    for candidate in candidates:
        p = str(candidate)
        if p in seen:
            continue
        seen.add(p)
        if candidate.exists():
            return p
    return None


def _resolveWebrootFromConfig(configPath: str, domain: str) -> str:
    try:
        content = Path(configPath).read_text(encoding="utf-8")
        rootMatch = re.search(r"^\s*root\s+([^;]+);", content, re.MULTILINE)
        if rootMatch:
            return rootMatch.group(1).strip()
    except OSError:
        pass
    return str(DEFAULT_WEBROOT_BASE / domain)


def _readSiteConfig(configPath: str | None) -> str:
    if not configPath:
        return ""
    try:
        return Path(configPath).read_text(encoding="utf-8")
    except OSError:
        return ""


def _extractNginxDirective(configContent: str, directiveName: str) -> str | None:
    match = re.search(
        rf"^\s*{re.escape(directiveName)}\s+([^;]+);",
        configContent,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else None


# ═══════════════════════════════════════════════════════════
# 获取站点详细配置
# ═══════════════════════════════════════════════════════════

def getNginxSiteConfig(domain: str) -> dict:
    """
    根据域名获取站点配置文件的详细内容。
    返回配置原文 + 已解析的关键字段。

    Args:
        domain: 域名，如 "example.com"

    Returns:
        {
            "domain": str,
            "configPath": str | None,
            "content": str,           # 配置原文
            "parsed": {               # 已解析字段
                "serverName": str | None,
                "listen": str | None,
                "root": str | None,
                "proxyPass": str | None,
                "sslCertPath": str | None,
                "sslKeyPath": str | None,
            }
        }
    """
    configPath = _findSiteConfigPath(domain)
    if not configPath:
        raise ToolExecutionException(f"找不到域名 {domain} 对应的 nginx 配置")

    content = _readSiteConfig(configPath)

    parsed = {
        "serverName": _extractNginxDirective(content, "server_name"),
        "listen": _extractNginxDirective(content, "listen"),
        "root": _extractNginxDirective(content, "root"),
        "proxyPass": _extractNginxDirective(content, "proxy_pass"),
        "sslCertPath": _extractNginxDirective(content, "ssl_certificate"),
        "sslKeyPath": _extractNginxDirective(content, "ssl_certificate_key"),
    }

    return {
        "domain": domain,
        "configPath": configPath,
        "content": content,
        "parsed": parsed,
    }


# ═══════════════════════════════════════════════════════════
# 修改站点配置（双入口：LLM Agent 直调 / Service→PrivilegedAgent）
# ═══════════════════════════════════════════════════════════

def _getNginxSiteUpdateInfo(domain: str, content: str) -> dict:
    """
    返回修改站点配置所需信息（供 Service→PrivilegedAgent 使用）。

    Returns:
        { targetPath, content, layoutType, siteName }
        如果站点不存在则抛出异常。
    """
    configPath = _findSiteConfigPath(domain)
    if not configPath:
        raise ToolExecutionException(f"找不到域名 {domain} 对应的 nginx 配置")

    layout = detectNginxLayout()
    siteName = _normalizeSiteName(domain)
    return {
        "targetPath": configPath,
        "content": content,
        "layoutType": layout.layoutType.value,
        "siteName": siteName,
    }


def updateNginxSiteConfig(domain: str, content: str) -> dict:
    """
    修改 Nginx 站点配置（LLM Agent 入口，内部 useSudo=True）。
    REST API 入口通过 Service → PrivilegedAgent 调用。

    流程：写文件 → nginx -t → reload
    """
    configPath = _findSiteConfigPath(domain)
    if not configPath:
        raise ToolExecutionException(f"找不到域名 {domain} 对应的 nginx 配置")

    # 写文件
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, suffix=".conf",
    ) as tmpFile:
        tmpFile.write(content)
        tmpPath = tmpFile.name

    try:
        runCommand(["install", "-D", "-m", "644", tmpPath, configPath], useSudo=True)
    finally:
        try:
            os.unlink(tmpPath)
        except OSError:
            pass

    # 测试 + reload
    runCommand(["nginx", "-t"], useSudo=True)
    runCommand(["systemctl", "reload", "nginx"], useSudo=True)

    return {
        "domain": domain,
        "configPath": configPath,
        "isUpdated": True,
        "isReloaded": True,
    }


# ═══════════════════════════════════════════════════════════
# 站点创建（双入口：LLM Agent 直调 / Service→PrivilegedAgent）
# ═══════════════════════════════════════════════════════════

def createNginxSite(
    domain: str,
    mode: str,
    listenPort: int,
    rootPath: str | None = None,
    proxyPass: str | None = None,
) -> NginxSiteCreateResult:
    """
    创建 Nginx 站点（LLM Agent 入口，内部 useSudo=True）。
    REST API 入口通过 Service → PrivilegedAgent 调用。
    """
    mode = mode.strip().lower()
    if mode == "static":
        if not rootPath:
            raise ToolExecutionException("静态站点必须提供 rootPath")
        configContent = generateStaticSiteConfig(domain, rootPath, listenPort)
    elif mode == "reverse_proxy":
        if not proxyPass:
            raise ToolExecutionException("反向代理必须提供 proxyPass")
        configContent = generateProxyConfig(domain, proxyPass, listenPort)
    else:
        raise ToolExecutionException("不支持的模式")

    configPath = saveNginxConfig(domain, configContent)
    try:
        runCommand(["nginx", "-t"], useSudo=True)
    except ToolExecutionException:
        runCommand(["rm", "-f", configPath], useSudo=True, checkReturnCode=False)
        raise

    runCommand(["systemctl", "reload", "nginx"], useSudo=True)

    return NginxSiteCreateResult(
        domain=domain,
        mode=NginxSiteMode(mode),
        listenPort=listenPort,
        configPath=configPath,
        enabledPath=_resolveEnabledPath(domain),
        rootPath=rootPath if mode == "static" else None,
        proxyPass=proxyPass if mode == "reverse_proxy" else None,
        isEnabled=True,
        isReloaded=True,
    )


def createNginxReverseProxySite(
    domain: str,
    proxyPort: int,
    proxyPass: str,
    listenPort: int,
    proxyProtocol: str = "http",
) -> NginxSiteCreateResult:
    proxyTarget = f"{proxyProtocol}://{proxyPass}:{proxyPort}"
    return createNginxSite(
        domain=domain,
        mode="reverse_proxy",
        listenPort=listenPort,
        proxyPass=proxyTarget,
    )


# ═══════════════════════════════════════════════════════════
# 配置写入（自适应布局）
# ═══════════════════════════════════════════════════════════

def _getNginxConfigWriteInfo(configName: str, configContent: str) -> dict:
    """
    返回写入配置所需的全部信息（供 Service→PrivilegedAgent 使用）。
    返回 { targetPath, content, layoutType }。
    """
    siteName = _normalizeSiteName(configName)
    layout = detectNginxLayout()
    configPath = str(Path(layout.configDir) / f"{siteName}.conf")
    return {
        "targetPath": configPath,
        "content": configContent,
        "layoutType": layout.layoutType.value,
        "siteName": siteName,
    }


def saveNginxConfig(configName: str, configContent: str) -> str:
    """
    写入 Nginx 配置文件（LLM Agent 入口，内部 useSudo=True）。
    自适应 Debian/RHEL 布局。
    """
    siteName = _normalizeSiteName(configName)
    configPath = _resolveConfigPath(configName)

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, suffix=".conf",
    ) as tmpFile:
        tmpFile.write(configContent)
        tmpPath = tmpFile.name

    try:
        runCommand(["install", "-D", "-m", "644", tmpPath, configPath], useSudo=True)
    finally:
        try:
            os.unlink(tmpPath)
        except OSError:
            pass

    return configPath


# ═══════════════════════════════════════════════════════════
# 配置测试 & 重载
# ═══════════════════════════════════════════════════════════

def testNginxConfig():
    runCommand(["nginx", "-t"], useSudo=True)


def reloadNginx():
    runCommand(["systemctl", "reload", "nginx"], useSudo=True)


def restartNginx():
    runCommand(["systemctl", "restart", "nginx"], useSudo=True)


# ═══════════════════════════════════════════════════════════
# 站点列表（自适应布局）
# ═══════════════════════════════════════════════════════════

def getNginxSiteList() -> list[dict]:
    """
    获取已启用站点列表。
    自适应 Debian（sites-enabled）/ RHEL（conf.d）布局。
    """
    layout = detectNginxLayout()
    sites: list[dict] = []

    # 确定要扫描的目录
    scanDirs = []
    if layout.enabledDir:
        scanDirs.append(Path(layout.enabledDir))
    if layout.layoutType == NginxLayoutType.CONF_D:
        scanDirs.append(Path(layout.configDir))

    seen = set()
    for scanDir in scanDirs:
        if not scanDir.exists():
            continue
        for configPath in sorted(scanDir.glob("*.conf")):
            if str(configPath) in seen:
                continue
            seen.add(str(configPath))
            content = configPath.read_text(encoding="utf-8", errors="ignore")

            serverNameMatch = re.search(r"server_name\s+([^;]+);", content)
            listenMatch = re.search(r"listen\s+([^;]+);", content)
            rootMatch = re.search(r"root\s+([^;]+);", content)
            proxyMatch = re.search(r"proxy_pass\s+([^;]+);", content)

            sites.append({
                "configName": configPath.name,
                "configPath": str(configPath),
                "domain": serverNameMatch.group(1).strip() if serverNameMatch else None,
                "listen": listenMatch.group(1).strip() if listenMatch else None,
                "mode": "reverse_proxy" if proxyMatch else "static" if rootMatch else "unknown",
                "rootPath": rootMatch.group(1).strip() if rootMatch else None,
                "proxyPass": proxyMatch.group(1).strip() if proxyMatch else None,
                "isEnabled": True,
            })

    return sites


# ═══════════════════════════════════════════════════════════
# 站点删除（自适应布局）
# ═══════════════════════════════════════════════════════════

def _getNginxSiteDeleteInfo(configName: str) -> dict:
    """
    返回删除站点所需信息（供 Service→PrivilegedAgent 使用）。
    返回 { configPath, siteName, layoutType }。
    """
    configPath = _resolveConfigPath(configName)
    siteName = _normalizeSiteName(configName)
    layout = detectNginxLayout()
    return {
        "configPath": configPath,
        "siteName": siteName,
        "layoutType": layout.layoutType.value,
    }


def deleteNginxSite(configName: str) -> dict:
    """
    删除指定站点配置（LLM Agent 入口，内部 useSudo=True）。
    自适应双布局。
    """
    siteName = _normalizeSiteName(configName)
    configPath = _resolveConfigPath(configName)

    if not os.path.exists(configPath):
        raise ToolExecutionException(f"站点配置不存在: {configPath}")

    runCommand(["rm", "-f", configPath], useSudo=True)
    try:
        runCommand(["nginx", "-t"], useSudo=True)
    except ToolExecutionException:
        raise
    runCommand(["systemctl", "reload", "nginx"], useSudo=True)

    return {
        "configName": configName,
        "configPath": configPath,
        "isDeleted": True,
        "isReloaded": True,
    }


# ═══════════════════════════════════════════════════════════
# SSL 证书管理（LoongArch 降级支持）
# ═══════════════════════════════════════════════════════════

def _buildCertbotCommand(domain: str, email: str, webroot: str) -> list[str]:
    return [
        "certbot",
        "certonly",
        "--webroot",
        "-w",
        webroot,
        "-d",
        domain,
        "--email",
        email,
        "--agree-tos",
        "--non-interactive",
    ]


def _checkCertbotAvailable() -> bool:
    """检测 certbot 是否可用（LoongArch 上可能没有原生包）"""
    if shutil.which("certbot"):
        return True
    # LoongArch 回退：尝试 pip3 安装的 certbot
    try:
        result = runCommand(["python3", "-m", "certbot", "--version"], checkReturnCode=False)
        return result.returncode == 0
    except Exception:
        return False


def applySslCertificate(domain: str, email: str) -> dict:
    """
    申请 Let's Encrypt 免费证书。
    LoongArch 上 certbot 可能不可用，提前报明确的降级提示。
    """
    if not _checkCertbotAvailable():
        if _is_loongarch():
            raise ServiceUnavailableException(
                "LoongArch 架构上 certbot 暂无官方支持。"
                "请尝试: pip3 install certbot, 或使用 DNS 手动申请"
            )
        raise ServiceUnavailableException("certbot 未安装，请先安装 certbot")

    configPath = _findSiteConfigPath(domain)
    if not configPath:
        raise ToolExecutionException(f"找不到域名 {domain} 对应的 nginx 配置")

    webroot = _resolveWebrootFromConfig(configPath, domain)
    if not webroot:
        raise ToolExecutionException(f"无法为 {domain} 推断 webroot")

    command = _buildCertbotCommand(domain, email, webroot)
    result = runCommand(command, useSudo=True, checkReturnCode=False)

    if result.returncode != 0:
        errorMessage = (result.stderr or result.stdout or "").strip()
        raise ToolExecutionException(
            f"申请证书失败: {' '.join(command)}\n{errorMessage}"
        )

    liveDir = LETSENCRYPT_LIVE_DIR / domain
    return {
        "domain": domain,
        "webroot": webroot,
        "certPath": str(liveDir / "fullchain.pem"),
        "keyPath": str(liveDir / "privkey.pem"),
    }


def configSslForNginx(domain: str, certPath: str, keyPath: str) -> dict:
    """写入 HTTPS 配置（自适应布局）。"""
    certFile = Path(certPath)
    keyFile = Path(keyPath)
    if not certFile.exists():
        raise ToolExecutionException(f"证书文件不存在: {certPath}")
    if not keyFile.exists():
        raise ToolExecutionException(f"私钥文件不存在: {keyPath}")

    existingConfigPath = _findSiteConfigPath(domain)
    existingConfig = _readSiteConfig(existingConfigPath)
    proxyPass = _extractNginxDirective(existingConfig, "proxy_pass")
    webroot = _extractNginxDirective(existingConfig, "root") or str(
        DEFAULT_WEBROOT_BASE / domain
    )

    if proxyPass:
        siteLocation = f"""location / {{
        proxy_pass {proxyPass};
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

    configPath = saveNginxConfig(domain, configContent)
    runCommand(["nginx", "-t"], useSudo=True)
    runCommand(["systemctl", "reload", "nginx"], useSudo=True)

    return {
        "domain": domain,
        "configPath": configPath,
        "certPath": certPath,
        "keyPath": keyPath,
        "isSslConfigured": True,
        "isReloaded": True,
    }


def renewSslCertificate(domain: str) -> dict:
    """续期 SSL 证书（LoongArch 降级）。"""
    if not _checkCertbotAvailable():
        if _is_loongarch():
            raise ServiceUnavailableException(
                "LoongArch 架构上 certbot 暂无官方支持，请手动续期"
            )
        raise ServiceUnavailableException("certbot 未安装，请先安装 certbot")

    result = runCommand(
        ["certbot", "renew", "--cert-name", domain, "--non-interactive"],
        useSudo=True,
        checkReturnCode=False,
    )

    if result.returncode != 0:
        errorMessage = (result.stderr or result.stdout or "").strip()
        raise ToolExecutionException(f"续期证书失败: {errorMessage}")

    runCommand(["nginx", "-t"], useSudo=True)
    runCommand(["systemctl", "reload", "nginx"], useSudo=True)

    return {
        "domain": domain,
        "isRenewed": True,
        "isReloaded": True,
    }
