"""
服务与中间件管理工具 — 纯 subprocess，零外部依赖。

合并原 service_tools + firewall_tools + docker_tools + nginx_tools
    + database_tools + log_tools，去掉 pydantic / _command_runner。
"""
from __future__ import annotations
import json
import re
import subprocess
import urllib.request

from ndlmpanel_agent.shared.ops_types import (
    ServiceOperationResult, LogQueryResult,
    FirewallStatus, FirewallPortRule, FirewallPortOperationResult,
    FirewallBackendType,
    DockerInstallInfo, DockerContainer,
    NginxInstallInfo, NginxStatus,
    DatabaseInstallInfo, DatabaseStatus,
)
from ndlmpanel_agent.shared.types import ToolRiskLevel

TOOLS = {
    # systemctl
    "getServiceStatus": ToolRiskLevel.READ_ONLY,
    "listFailedServices": ToolRiskLevel.READ_ONLY,
    "manageSystemService": ToolRiskLevel.DANGEROUS,
    # logs
    "querySystemLogs": ToolRiskLevel.READ_ONLY,
    # firewall
    "getFirewallStatus": ToolRiskLevel.READ_ONLY,
    "listFirewallPorts": ToolRiskLevel.READ_ONLY,
    "addFirewallPort": ToolRiskLevel.DANGEROUS,
    "removeFirewallPort": ToolRiskLevel.DANGEROUS,
    # docker
    "checkDockerInstalled": ToolRiskLevel.READ_ONLY,
    "getDockerContainers": ToolRiskLevel.READ_ONLY,
    # nginx
    "checkNginxInstalled": ToolRiskLevel.READ_ONLY,
    "getNginxStatus": ToolRiskLevel.READ_ONLY,
    # database
    "checkDatabaseInstalled": ToolRiskLevel.READ_ONLY,
    "getDatabaseStatus": ToolRiskLevel.READ_ONLY,
}


def _run(argv: list[str], timeout: int = 15,
         check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"超时: {' '.join(argv)}") from None
    except FileNotFoundError:
        raise RuntimeError(f"命令不存在: {argv[0]}") from None


# ── systemd 服务 ──

def getServiceStatus(serviceName: str) -> ServiceOperationResult:
    try:
        r = _run(["systemctl", "is-active", serviceName], check=False)
        return ServiceOperationResult(success=True, serviceName=serviceName,
                                       currentStatus=r.stdout.strip())
    except RuntimeError:
        return ServiceOperationResult(success=False, serviceName=serviceName,
                                       currentStatus="unknown")


def listFailedServices() -> list[dict]:
    try:
        r = _run(["systemctl", "list-units", "--failed", "--no-legend"],
                 check=False)
        svcs = []
        for line in r.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                svcs.append({"name": parts[0], "status": parts[1]})
        return svcs
    except RuntimeError:
        return []


def manageSystemService(serviceName: str, action: str = "status"
                        ) -> ServiceOperationResult:
    if action == "status" or action not in ("start", "stop", "restart",
                                              "enable", "disable"):
        return getServiceStatus(serviceName)
    _run(["sudo", "-n", "systemctl", action, serviceName])
    # 查询后状态
    try:
        sr = _run(["systemctl", "is-active", serviceName], check=False)
        st = sr.stdout.strip()
    except RuntimeError:
        st = "unknown"
    return ServiceOperationResult(success=True, serviceName=serviceName,
                                   currentStatus=st, message=f"已执行 {action}")


# ── 日志 ──

_LOG_TYPE_ARGS: dict[str, list[str]] = {
    "syslog": [], "auth": ["--facility=auth"],
    "kern": ["-k"], "dmesg": ["-k"],
}


def querySystemLogs(logType: str = "syslog", keyword: str | None = None,
                    since: str | None = None, until: str | None = None,
                    lineLimit: int = 100) -> LogQueryResult:
    cmd = ["journalctl", "--no-pager", "-n", str(lineLimit)]
    if logType in _LOG_TYPE_ARGS:
        cmd.extend(_LOG_TYPE_ARGS[logType])
    else:
        cmd.extend(["-u", logType])
    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])
    if keyword:
        cmd.extend(["--grep", keyword])
    try:
        r = _run(cmd, check=False)
    except RuntimeError:
        return LogQueryResult(lines=[], totalLines=0, logSource=f"journalctl({logType})")
    lines = [l for l in r.stdout.strip().splitlines() if l]
    return LogQueryResult(lines=lines, totalLines=len(lines),
                           logSource=f"journalctl({logType})")


# ── 防火墙 ──

def _detectFirewallBackend() -> FirewallBackendType:
    for argv, bt in [(["firewall-cmd", "--version"], FirewallBackendType.FIREWALLD),
                     (["ufw", "version"], FirewallBackendType.UFW)]:
        try:
            _run(argv, check=False)
            return bt
        except RuntimeError:
            continue
    return FirewallBackendType.UNKNOWN


def _requireBackend() -> FirewallBackendType:
    bt = _detectFirewallBackend()
    if bt == FirewallBackendType.UNKNOWN:
        raise RuntimeError("未检测到 firewalld/ufw")
    return bt


def getFirewallStatus() -> FirewallStatus:
    backend = _detectFirewallBackend()
    if backend == FirewallBackendType.FIREWALLD:
        r = _run(["firewall-cmd", "--state"], check=False)
        active = "running" in r.stdout.strip().lower()
        policy = "unknown"
        if active:
            try:
                policy = _run(["firewall-cmd", "--get-default-zone"]).stdout.strip()
            except RuntimeError:
                pass
        return FirewallStatus(isActive=active, defaultPolicy=policy, backendType=backend)
    if backend == FirewallBackendType.UFW:
        r = _run(["ufw", "status", "verbose"], check=False)
        active = "Status: active" in r.stdout
        m = re.search(r"Default:\s*(.+)", r.stdout)
        return FirewallStatus(isActive=active, defaultPolicy=m.group(1).strip() if m else "unknown",
                              backendType=backend)
    return FirewallStatus(isActive=False, backendType=FirewallBackendType.UNKNOWN)


def listFirewallPorts() -> list[FirewallPortRule]:
    backend = _requireBackend()
    ports: list[FirewallPortRule] = []
    if backend == FirewallBackendType.FIREWALLD:
        r = _run(["firewall-cmd", "--list-ports"])
        for entry in r.stdout.strip().split():
            if "/" in entry:
                ps, proto = entry.split("/", 1)
                ports.append(FirewallPortRule(port=int(ps), protocol=proto))
        rich = _run(["firewall-cmd", "--list-rich-rules"], check=False)
        for line in rich.stdout.strip().splitlines():
            pm = re.search(r'port port="(\d+)" protocol="(\w+)"', line)
            sm = re.search(r'source address="([^"]+)"', line)
            am = re.search(r'(accept|reject|drop)', line)
            if pm:
                ports.append(FirewallPortRule(port=int(pm.group(1)),
                              protocol=pm.group(2),
                              policy=am.group(1) if am else "accept",
                              sourceIp=sm.group(1) if sm else None))
        return ports
    # ufw
    r = _run(["ufw", "status", "numbered"])
    for line in r.stdout.strip().splitlines():
        m = re.match(r"\[\s*\d+\]\s+(\d+)/(tcp|udp)\s+(\w+)\s+IN\s+(.*)", line)
        if m:
            src = m.group(4).strip()
            ports.append(FirewallPortRule(port=int(m.group(1)), protocol=m.group(2),
                          policy=m.group(3).lower(),
                          sourceIp=src if src != "Anywhere" else None))
    return ports


def addFirewallPort(port: int, protocol: str = "tcp") -> FirewallPortOperationResult:
    backend = _requireBackend()
    if backend == FirewallBackendType.FIREWALLD:
        _run(["sudo", "-n", "firewall-cmd", f"--add-port={port}/{protocol}", "--permanent"])
        _run(["sudo", "-n", "firewall-cmd", "--reload"])
    else:
        _run(["sudo", "-n", "ufw", "allow", f"{port}/{protocol}"])
    return FirewallPortOperationResult(success=True, port=port, protocol=protocol,
                                        message=f"已放行 {port}/{protocol}")


def removeFirewallPort(port: int, protocol: str = "tcp") -> FirewallPortOperationResult:
    backend = _requireBackend()
    if backend == FirewallBackendType.FIREWALLD:
        _run(["sudo", "-n", "firewall-cmd", f"--remove-port={port}/{protocol}", "--permanent"])
        _run(["sudo", "-n", "firewall-cmd", "--reload"])
    else:
        _run(["sudo", "-n", "ufw", "delete", "allow", f"{port}/{protocol}"])
    return FirewallPortOperationResult(success=True, port=port, protocol=protocol,
                                        message=f"已移除 {port}/{protocol}")


# ── Docker ──

def checkDockerInstalled() -> DockerInstallInfo:
    try:
        r = _run(["docker", "--version"])
        v = r.stdout.strip().split(",")[0].replace("Docker version ", "")
        return DockerInstallInfo(isInstalled=True, version=v)
    except RuntimeError:
        return DockerInstallInfo(isInstalled=False)


def getDockerContainers(includeStopped: bool = False) -> list[DockerContainer]:
    if not checkDockerInstalled().isInstalled:
        return []
    argv = ["docker", "ps", "--format", "{{json .}}", "--no-trunc"]
    if includeStopped:
        argv.insert(2, "-a")
    try:
        r = _run(argv)
    except RuntimeError:
        return []
    containers: list[DockerContainer] = []
    for line in r.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        c = DockerContainer(containerId=d.get("ID", ""), imageName=d.get("Image", ""),
                            status=d.get("Status", ""), ports=d.get("Ports", ""))
        if "Up" in c.status:
            try:
                sr = _run(["docker", "stats", "--no-stream", "--format",
                           "{{.CPUPerc}},{{.MemUsage}}", c.containerId], timeout=10)
                parts = sr.stdout.strip().split(",")
                if len(parts) >= 2:
                    c.cpuPercent = float(parts[0].strip().rstrip("%"))
                    memParts = parts[1].strip().split("/")
                    c.memoryUsageMB = _parseMem(memParts[0])
                    if len(memParts) > 1:
                        c.memoryLimitMB = _parseMem(memParts[1])
            except (RuntimeError, ValueError, IndexError):
                pass
        containers.append(c)
    return containers


def _parseMem(v: str) -> float:
    for suf, mul in [("GiB", 1024), ("MiB", 1), ("KiB", 0.001),
                     ("GB", 1000), ("MB", 1), ("KB", 0.001)]:
        if suf in v:
            try:
                return float(v.replace(suf, "").strip()) * mul
            except ValueError:
                return 0.0
    return 0.0


# ── Nginx ──

def checkNginxInstalled() -> NginxInstallInfo:
    try:
        r = _run(["nginx", "-v"], check=False)
        out = r.stderr.strip() or r.stdout.strip()
        vm = re.search(r"nginx/([\d.]+)", out)
        cfg = None
        tr = _run(["nginx", "-t"], check=False)
        cm = re.search(r"configuration file (\S+)", tr.stderr)
        if cm:
            cfg = cm.group(1)
        return NginxInstallInfo(isInstalled=True, version=vm.group(1) if vm else None,
                                configPath=cfg)
    except RuntimeError:
        return NginxInstallInfo(isInstalled=False)


def getNginxStatus() -> NginxStatus:
    if not checkNginxInstalled().isInstalled:
        return NginxStatus(isRunning=False)
    running = False
    workers = 0
    try:
        r = _run(["systemctl", "is-active", "nginx"], check=False)
        running = r.stdout.strip() == "active"
    except RuntimeError:
        pass
    if running:
        try:
            r = _run(["pgrep", "-c", "-f", "nginx: worker"], check=False)
            workers = int(r.stdout.strip())
        except (RuntimeError, ValueError):
            pass
    conns = None
    try:
        resp = urllib.request.urlopen("http://127.0.0.1/nginx_status", timeout=2)
        cm = re.search(r"Active connections:\s*(\d+)", resp.read().decode())
        if cm:
            conns = int(cm.group(1))
    except Exception:
        pass
    return NginxStatus(isRunning=running, workerProcessCount=workers,
                        activeConnections=conns)


# ── 数据库 ──

_VERSION_CMDS: dict[str, list[str]] = {
    "mysql": ["mysql", "--version"], "mariadb": ["mysql", "--version"],
    "postgresql": ["psql", "--version"], "postgres": ["psql", "--version"],
    "redis": ["redis-server", "--version"], "mongodb": ["mongod", "--version"],
}

_SVC_NAMES: dict[str, list[str]] = {
    "mysql": ["mysql", "mysqld", "mariadb"],
    "mariadb": ["mariadb", "mysql", "mysqld"],
    "postgresql": ["postgresql", "postgres"],
    "postgres": ["postgresql", "postgres"],
    "redis": ["redis", "redis-server"],
    "mongodb": ["mongod", "mongodb"],
}


def checkDatabaseInstalled(databaseType: str = "mysql") -> DatabaseInstallInfo:
    dt = databaseType.lower()
    cmd = _VERSION_CMDS.get(dt)
    if not cmd:
        return DatabaseInstallInfo(isInstalled=False, databaseType=databaseType)
    try:
        r = _run(cmd, check=False)
        out = r.stdout.strip() or r.stderr.strip()
        vm = re.search(r"(\d+\.\d+\.\d+)", out)
        return DatabaseInstallInfo(isInstalled=True, version=vm.group(1) if vm else out[:50],
                                   databaseType=databaseType)
    except RuntimeError:
        return DatabaseInstallInfo(isInstalled=False, databaseType=databaseType)


def getDatabaseStatus(databaseType: str = "mysql") -> DatabaseStatus:
    dt = databaseType.lower()
    svcs = _SVC_NAMES.get(dt, [dt])
    running = False
    for name in svcs:
        try:
            r = _run(["systemctl", "is-active", name], check=False)
            if r.stdout.strip() == "active":
                running = True
                break
        except RuntimeError:
            continue
    conns = squeries = None
    if running and dt in ("mysql", "mariadb"):
        try:
            r = _run(["mysqladmin", "status"], check=False, timeout=5)
            if r.returncode == 0:
                tm = re.search(r"Threads:\s*(\d+)", r.stdout)
                sm = re.search(r"Slow queries:\s*(\d+)", r.stdout)
                if tm:
                    conns = int(tm.group(1))
                if sm:
                    squeries = int(sm.group(1))
        except RuntimeError:
            pass
    return DatabaseStatus(isRunning=running, databaseType=databaseType,
                          currentConnections=conns, slowQueryCount=squeries)
