"""Adapters from utils.toolFunction tools to MCP tool definitions."""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - project dependency should provide this.
    BaseModel = None  # type: ignore

from ..protocol.schemas import functionToMcpToolSchema


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# 特权脚本目录是协议的一部分：提示词、MCP 工具和特权代理必须使用同一个
# 根路径，避免某个旧入口把脚本落到工作区或 /tmp 后再以 root 执行。
PRIVILEGED_SCRIPT_DIR = Path("/opt/ndlmpanel/tmp_scripts")
_SHELL_CONTROL_RE = re.compile(r"[;&|`$()\n\r]")


def _isUnderDirectory(path: str, directory: Path) -> bool:
    try:
        Path(path).expanduser().resolve().relative_to(directory.resolve())
        return True
    except (OSError, RuntimeError, ValueError):
        return False


from gateway.service.PrivilegedAgentClient import (  # noqa: E402
    PrivilegedAgentClient,
    PrivilegedAgentRemoteError,
)
from privileged_agent.models import PrivilegedAction  # noqa: E402
from utils.toolFunction import ALL_TOOL_FUNCTIONS  # noqa: E402
from utils.toolFunction.exceptions import GatewayAbstractException  # noqa: E402
from utils.toolFunction.models.agent.tool_models import ToolRiskLevel  # noqa: E402
from utils.toolFunction.models.ops.process.process_models import ProcessSortBy  # noqa: E402
from utils.toolFunction.tools.ops._command_runner import runCommand  # noqa: E402
from utils.toolFunction.tools.tool_registry import RISK_LEVEL_MAP  # noqa: E402


SELECTED_TOOL_NAMES: tuple[str, ...] = (
    # General file tools.
    "listDirectory",
    "listSingleFileOrDirectory",
    "getDirectoryTree",
    "grepFileOrDirectory",
    "isTextFile",
    "readTextFile",
    "writeTextFile",
    "createFile",
    # createDirectory: 与 agent-core-mcp 冲突，由 agent-core-mcp 提供
    "renameFileOrDirectory",
    "copyFile",
    "deleteFile",
    "deleteDirectory",
    # System observation.
    "getSystemVersion",
    "getUptime",
    "getCpuInfo",
    "getMemoryInfo",
    "getDiskInfo",
    "getNetworkInfo",
    # Process and network diagnostics.
    "listProcesses",
    "getProcessDetail",
    "getZombieOrphanProcesses",
    "pingHost",
    "checkPortConnectivity",
    "querySystemLogs",
    # Ops-specific tools.
    "getFirewallStatus",
    "checkDockerInstalled",
    "getDockerContainers",
    "getDockerContainerInfo",
    "getDockerContainerLogs",
    "startDockerContainer",
    "stopDockerContainer",
    "restartDockerContainer",
    "checkNginxInstalled",
    "getNginxStatus",
    # testNginxConfig: 由特权版本 testNginxConfigPrivileged 覆盖
    "getNginxSiteList",
    "getNginxSiteConfig",
    "checkDatabaseInstalled",
    "getDatabaseStatus",
)

MCP_ONLY_TOOL_NAMES: tuple[str, ...] = (
    "listProcessesBrief",
    "getProcessAnomalies",
    "getDockerContainerSummary",
    "testNginxConfigPrivileged",
    "listFirewallPortsPrivileged",
    "addFirewallPortPrivileged",
    "removeFirewallPortPrivileged",
    "manageSystemServicePrivileged",
    "writePrivilegedFile",
    "nginxWriteStaticFile",
    # V2 特权提权工具
    "submitElevation",
    "runPrivileged",
    # 运维经验包（阶段 8）
    "searchOpsExperience",
    "getOpsExperienceDetail",
    "submitOpsExperience",
)


TOOL_DESCRIPTIONS: dict[str, str] = {
    "listDirectory": "List files and directories in a target directory.",
    "listSingleFileOrDirectory": "Inspect metadata for one file or directory.",
    "getDirectoryTree": "Return a bounded directory tree for a target path.",
    "grepFileOrDirectory": "Search file names or file contents with a regular expression.",
    "isTextFile": "Check whether a target path is a readable text file.",
    "readTextFile": "Read text file content.",
    "writeTextFile": "Write text content to an existing file. If the file does not exist, call createFile first.",
    "createFile": "Create an empty file.",
    # createDirectory description removed — tool provided by agent-core-mcp
    "renameFileOrDirectory": "Rename or move a file or directory.",
    "copyFile": "Copy a file.",
    "deleteFile": "Delete a file or symbolic link.",
    "deleteDirectory": "Delete a directory.",
    "getSystemVersion": "Return operating system, kernel, and host information.",
    "getUptime": "Return system uptime and timezone-aware boot time.",
    "getCpuInfo": "Return CPU model, core count, usage, and load averages.",
    "getMemoryInfo": "Return memory and swap usage.",
    "getDiskInfo": "Return mounted disk usage.",
    "getNetworkInfo": "Return network interface status and addresses.",
    "listProcesses": "List running processes with full details. This can return a large response; prefer listProcessesBrief for agent summaries.",
    "getProcessDetail": "Return detailed information for one process.",
    "getZombieOrphanProcesses": "List zombie processes. Prefer getProcessAnomalies for compact anomaly diagnostics or reparented-process inspection.",
    "pingHost": "Ping a host and summarize reachability and packet loss.",
    "checkPortConnectivity": "Check TCP connectivity to a host and port.",
    "querySystemLogs": "Query system logs from journalctl.",
    "getFirewallStatus": "Inspect active firewall backend and status.",
    "checkDockerInstalled": "Check whether Docker is installed.",
    "getDockerContainers": "List Docker containers.",
    "getDockerContainerInfo": "Inspect one Docker container with full docker inspect output. This may return sensitive or very large data; prefer getDockerContainerSummary.",
    "getDockerContainerLogs": "Read Docker container logs.",
    "startDockerContainer": "Start a Docker container.",
    "stopDockerContainer": "Stop a Docker container.",
    "restartDockerContainer": "Restart a Docker container.",
    "checkNginxInstalled": "Check whether Nginx is installed.",
    "getNginxStatus": "Inspect Nginx runtime status.",
    # testNginxConfig: 由特权版本 testNginxConfigPrivileged 覆盖
    "getNginxSiteList": "List known Nginx site configurations.",
    "getNginxSiteConfig": "Read one Nginx site configuration.",
    "checkDatabaseInstalled": "Check whether a database engine is installed.",
    "getDatabaseStatus": "Inspect database service status.",
    # executeCommand: 由 agent-core-mcp 的 runCommand/runShellCommand 覆盖
    "listProcessesBrief": "Return a compact process list for agents with limit, sorting, and optional command text.",
    "getProcessAnomalies": "Return a compact list of zombie processes. Set includeReparented=true to also inspect processes reparented to PID 1.",
    "getDockerContainerSummary": "Return a compact Docker container summary without full docker inspect details.",
    "testNginxConfigPrivileged": "Validate Nginx configuration through the privileged agent.",
    "listFirewallPortsPrivileged": "List firewall port rules through the privileged agent. Return results as a markdown table with columns: 序号(No.), 端口(Port), 协议(Protocol), 策略(Policy), IP版本(IP Version), 源IP(Source IP), 目标IP(Destination IP).",
    "addFirewallPortPrivileged": "Add an allow firewall port rule through the privileged agent.",
    "removeFirewallPortPrivileged": "Remove an allow firewall port rule through the privileged agent.",
    "manageSystemServicePrivileged": "Inspect or change an allowed systemd service through the privileged agent for non-status actions.",
    "writePrivilegedFile": "Write a file to a privileged path (whitelist protected: nginx/var/www/docker etc.). Requires reason for approval. If the file is a script that will later run with root, targetPath MUST be under /opt/ndlmpanel/tmp_scripts/; never use the workspace or /tmp.",
    "nginxWriteStaticFile": "Write a static file (html/css/js) to Nginx webroot (/etc/nginx/html/ or /var/www/). Requires reason for approval.",
    "submitElevation": "Submit a privilege elevation request. Generates a one-time approval code that the admin must approve via 'sudo nereus approve <CODE>'. Three mutually exclusive channels: (A) commands=[] ONLY for exactly one simple preset command, (B) inline_cmd='...' ONLY for exactly one simple shell command, (C) script_path='/opt/ndlmpanel/tmp_scripts/xxx.sh' for any two-or-more related privileged actions or multi-step logic. For multiple related actions, first write ONE auditable script with writePrivilegedFile, then call submitElevation ONCE with script_path; do not submit one command at a time or use a commands array as a substitute. After approval, use runPrivileged().",
    "runPrivileged": "Execute a privileged command using an approved elevation token. Call only after a real admin approval event provides token_id; use the exact approved command_index, args, and session_id, without modifying them.",
    "searchOpsExperience": "按症状/关键词检索组织运维经验库（启用中的经验包），返回标题+分类+标签+摘要+质量分，供诊断参考。遇到疑似已知问题（如 Nginx 502、证书过期、磁盘告警）时优先检索。默认排除 negative 教训包。",
    "getOpsExperienceDetail": "取单个运维经验包完整内容（deploymentDoc 正文 + stages 阶段 + pitfalls 坑 + earlyWarnings 预警特征 + 附件路径），供处置方案参考。附件为只读参考，执行需走审批流程。",
    "submitOpsExperience": "处置成功后主动沉淀运维经验包（source=ai）。将本次处置写成 Markdown 正文（现象/原因/步骤/验证），并按需提供 stages/pitfalls/earlyWarnings 结构化字段，反哺组织记忆。",
}

TOOL_ANNOTATIONS: dict[str, dict[str, Any]] = {
    "submitElevation": {"requiresPrivilege": True, "usesElevationFlow": True},
    "runPrivileged": {"requiresPrivilege": True, "usesElevationFlow": True, "usesPrivilegedAgent": True},
    "searchOpsExperience": {"agentOptimized": True, "readsOrganizationMemory": True},
    "getOpsExperienceDetail": {"agentOptimized": True, "readsOrganizationMemory": True},
    "submitOpsExperience": {"writesOrganizationMemory": True},
    "listProcesses": {"mayReturnLargeOutput": True, "preferredAlternative": "listProcessesBrief"},
    "getZombieOrphanProcesses": {"preferredAlternative": "getProcessAnomalies"},
    "getDockerContainerInfo": {
        "mayReturnLargeOutput": True,
        "mayExposeSensitiveData": True,
        "preferredAlternative": "getDockerContainerSummary",
    },
    "writeTextFile": {"requiresExistingFile": True, "createFileBeforeWrite": True},
    # testNginxConfig / listFirewallPorts / addFirewallPort / removeFirewallPort: 由特权版本覆盖
    "listProcessesBrief": {"agentOptimized": True},
    "getProcessAnomalies": {"agentOptimized": True},
    "getDockerContainerSummary": {"agentOptimized": True},
    "testNginxConfigPrivileged": {"requiresPrivilege": True, "usesPrivilegedAgent": True},
    "listFirewallPortsPrivileged": {"requiresPrivilege": True, "usesPrivilegedAgent": True},
    "addFirewallPortPrivileged": {"requiresPrivilege": True, "usesPrivilegedAgent": True},
    "removeFirewallPortPrivileged": {"requiresPrivilege": True, "usesPrivilegedAgent": True},
    "manageSystemServicePrivileged": {"requiresPrivilege": True, "usesPrivilegedAgent": True},
}


class McpToolExecutionError(Exception):
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        super().__init__(str(payload.get("errorMessage") or payload.get("errorCode")))


@dataclass(frozen=True)
class ToolCallResult:
    content: list[dict[str, str]]
    isError: bool = False

    @classmethod
    def text(cls, text: str, isError: bool = False) -> "ToolCallResult":
        return cls(content=[{"type": "text", "text": text}], isError=isError)

    @classmethod
    def json(cls, payload: dict, isError: bool = False) -> "ToolCallResult":
        return cls.text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), isError)


@dataclass(frozen=True)
class AdaptedTool:
    name: str
    func: Callable[..., Any]
    riskLevel: ToolRiskLevel
    stdinOnly: bool = False
    annotations: dict[str, Any] = dataclasses.field(default_factory=dict)

    def toMcpSchema(self) -> dict:
        schema = functionToMcpToolSchema(self.func, self.riskLevel.value)
        schema["description"] = TOOL_DESCRIPTIONS.get(self.name, schema["description"])
        schema["annotations"].update(TOOL_ANNOTATIONS.get(self.name, {}))
        schema["annotations"].update(self.annotations)
        if self.stdinOnly:
            schema["annotations"]["transport"] = "stdio"
        return schema

    def call(self, arguments: dict[str, Any]) -> ToolCallResult:
        try:
            return ToolCallResult.text(_serializeResult(self.func(**arguments)))
        except McpToolExecutionError as exc:
            return ToolCallResult.json(exc.payload, isError=True)
        except GatewayAbstractException as exc:
            message = exc.innerMessage or exc.userMessage or exc.__class__.__name__
            return ToolCallResult.json(
                _errorPayload(
                    errorCode=exc.__class__.__name__,
                    errorMessage=message,
                    requiresPrivilege=_looksPrivilegeFailure(message),
                    backend="direct",
                ),
                isError=True,
            )
        except TypeError as exc:
            return ToolCallResult.json(
                _errorPayload(
                    errorCode="INVALID_ARGUMENTS",
                    errorMessage=f"Invalid tool arguments: {exc}",
                ),
                isError=True,
            )
        except Exception as exc:
            message = f"{exc.__class__.__name__}: {exc}"
            return ToolCallResult.json(
                _errorPayload(
                    errorCode=exc.__class__.__name__,
                    errorMessage=message,
                    requiresPrivilege=_looksPrivilegeFailure(message),
                    backend="direct",
                ),
                isError=True,
            )


def executeCommand(
    command: list[str],
    timeout: int = 30,
    useSudo: bool = False,
) -> dict:
    """Execute one argv-style command without shell expansion. stdio mode only."""
    if not command:
        raise ValueError("command must not be empty")
    result = runCommand(
        command,
        timeout=timeout,
        checkReturnCode=False,
        useSudo=useSudo,
    )
    return {
        "command": command,
        "returnCode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def listProcessesBrief(
    limit: int = 30,
    sortBy: str = "cpu",
    keyword: str | None = None,
    includeCommand: bool = False,
) -> dict:
    """Return a compact process list for agents."""
    limit = max(1, min(int(limit), 200))
    sort = _parseProcessSortBy(sortBy)
    processes = _toolFunc("listProcesses")(sortBy=sort, keyword=keyword)
    rows = []
    for proc in processes[:limit]:
        row = {
            "pid": proc.pid,
            "name": proc.processName,
            "user": proc.userName,
            "cpuPercent": proc.cpuPercent,
            "memoryPercent": proc.memoryPercent,
            "status": proc.status,
            "listeningPorts": [
                f"{port.protocol}/{port.listenAddress}:{port.port}"
                for port in (proc.ports or [])
            ],
        }
        if includeCommand:
            row["command"] = _truncate(proc.command, 220)
        rows.append(row)
    return {"totalReturned": len(rows), "limit": limit, "sortBy": sort.value, "processes": rows}


def getProcessAnomalies(limit: int = 50, includeReparented: bool = False) -> dict:
    """Return compact process anomaly data for agents."""
    import psutil

    limit = max(1, min(int(limit), 200))
    anomalies: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "username", "status", "cmdline", "ppid"]):
        try:
            info = proc.info
            status = info.get("status") or ""
            ppid = int(info.get("ppid") or 0)
            isZombie = status == psutil.STATUS_ZOMBIE
            isReparented = includeReparented and ppid == 1 and int(info["pid"]) != 1
            if not isZombie and not isReparented:
                continue
            command = " ".join(info.get("cmdline") or []) or (info.get("name") or "")
            reasons = []
            if isZombie:
                reasons.append("zombie")
            if isReparented:
                reasons.append("reparented_to_pid_1")
            anomalies.append(
                {
                    "pid": info["pid"],
                    "ppid": ppid,
                    "name": info.get("name") or "",
                    "user": info.get("username") or "",
                    "status": status,
                    "reasons": reasons,
                    "command": _truncate(command, 220),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            continue
    anomalies.sort(key=lambda item: (0 if "zombie" in item["reasons"] else 1, item["pid"]))
    return {
        "totalReturned": min(len(anomalies), limit),
        "totalMatched": len(anomalies),
        "limit": limit,
        "includeReparented": includeReparented,
        "anomalies": anomalies[:limit],
    }


def getDockerContainerSummary(containerId: str) -> dict:
    """Return compact Docker container information."""
    info = _toolFunc("getDockerContainerInfo")(containerId)
    data = _toJsonable(info)
    if isinstance(data, list) and data:
        data = data[0]
    if not isinstance(data, dict):
        return {"containerId": containerId, "rawType": type(data).__name__, "data": data}

    state = data.get("State") or {}
    config = data.get("Config") or {}
    hostConfig = data.get("HostConfig") or {}
    networkSettings = data.get("NetworkSettings") or {}
    networks = networkSettings.get("Networks") or {}
    mounts = data.get("Mounts") or []
    return {
        "id": data.get("Id", containerId),
        "name": str(data.get("Name") or "").lstrip("/"),
        "image": config.get("Image") or data.get("Image"),
        "status": state.get("Status"),
        "running": state.get("Running"),
        "restartPolicy": (hostConfig.get("RestartPolicy") or {}).get("Name"),
        "ports": networkSettings.get("Ports"),
        "networks": list(networks.keys()) if isinstance(networks, dict) else [],
        "mountCount": len(mounts) if isinstance(mounts, list) else 0,
        "startedAt": state.get("StartedAt"),
        "finishedAt": state.get("FinishedAt"),
        "exitCode": state.get("ExitCode"),
    }


def testNginxConfigPrivileged() -> dict:
    """Validate Nginx config through the privileged agent."""
    return _callPrivileged(PrivilegedAction.NGINX_TEST_CONFIG, {})


def listFirewallPortsPrivileged() -> dict:
    """List firewall rules through the privileged agent."""
    rules = _callPrivileged(PrivilegedAction.FIREWALL_LIST_RULES, {})
    return {"rules": rules, "total": len(rules) if isinstance(rules, list) else None}


def addFirewallPortPrivileged(
    port: int,
    protocol: str = "tcp",
    sourceIp: str | None = None,
    destinationIp: str | None = None,
    ipVersion: int = 4,
) -> dict:
    """Add an allow firewall port rule through the privileged agent."""
    return _callPrivileged(
        PrivilegedAction.FIREWALL_ADD_PORT_RULE,
        {
            "port": port,
            "protocol": protocol,
            "sourceIp": sourceIp,
            "destinationIp": destinationIp,
            "ipVersion": ipVersion,
            "action": 1,
        },
    )


def removeFirewallPortPrivileged(
    port: int,
    protocol: str = "tcp",
    sourceIp: str | None = None,
    destinationIp: str | None = None,
    ipVersion: int = 4,
) -> dict:
    """Remove an allow firewall port rule through the privileged agent."""
    return _callPrivileged(
        PrivilegedAction.FIREWALL_REMOVE_PORT_RULE,
        {
            "port": port,
            "protocol": protocol,
            "sourceIp": sourceIp,
            "destinationIp": destinationIp,
            "ipVersion": ipVersion,
        },
    )


def manageSystemServicePrivileged(serviceName: str, action: str = "status") -> dict:
    """Inspect or change an allowed systemd service through the privileged agent."""
    normalizedAction = action.strip().lower()
    if normalizedAction == "status":
        result = runCommand(["systemctl", "is-active", serviceName], checkReturnCode=False)
        return {
            "serviceName": serviceName,
            "action": normalizedAction,
            "currentStatus": result.stdout.strip(),
            "returnCode": result.returncode,
        }
    return _callPrivileged(
        PrivilegedAction.SERVICE_SET_STATE,
        {"serviceName": serviceName, "action": normalizedAction},
    )


def writePrivilegedFile(
    targetPath: str,
    content: str,
    reason: str = "",
) -> dict:
    """向特权路径写入文件；多步特权操作的脚本必须写入 /opt/ndlmpanel/tmp_scripts/。

    适用于：
    - 向 /etc/nginx/ 写入站点配置
    - 向 /var/www/ 写入静态文件
    - 向 /etc/docker/ 写入 daemon.json

    不适用于普通路径 — 普通路径请用 writeTextFile。

    Args:
        targetPath: 目标路径（必须在特权代理的白名单内）
        content: 文件内容
        reason: 调用原因说明（供审批展示）
    """
    # 只要内容看起来是将来会被 root 执行的脚本，就强制使用统一目录。
    # 这是工具入口的快速失败；特权代理和命令注册表仍会再次校验。
    looksLikeScript = (
        Path(targetPath).suffix.lower() in {".sh", ".bash"}
        or content.lstrip().startswith("#!")
    )
    if looksLikeScript and not _isUnderDirectory(
        targetPath, PRIVILEGED_SCRIPT_DIR
    ):
        return _errorPayload(
            errorCode="PRIVILEGED_SCRIPT_PATH_INVALID",
            errorMessage=(
                "需要特权执行的脚本只能写入 "
                f"{PRIVILEGED_SCRIPT_DIR}/，禁止工作区和 /tmp"
            ),
            requiresPrivilege=True,
            backend="mcp.guard",
        )
    try:
        result = _callPrivileged(
            PrivilegedAction.FILE_WRITE_TO_ALLOWED,
            {"targetPath": targetPath, "content": content},
        )
        return {"success": True, "data": result}
    except McpToolExecutionError:
        raise
    except Exception as exc:
        return {
            "success": False,
            "error": f"{exc.__class__.__name__}: {exc}",
            "requiresPrivilege": True,
        }


def nginxWriteStaticFile(
    targetPath: str,
    content: str,
    reason: str = "",
) -> dict:
    """向 Nginx webroot 写入静态文件（html/css/js）。

    Args:
        targetPath: 目标路径（必须在 /etc/nginx/html/ 或 /var/www/ 下）
        content: 文件内容
        reason: 调用原因说明
    """
    try:
        result = _callPrivileged(
            PrivilegedAction.NGINX_WRITE_STATIC_FILE,
            {"targetPath": targetPath, "content": content},
        )
        return {"success": True, "data": result}
    except McpToolExecutionError:
        raise
    except Exception as exc:
        return {
            "success": False,
            "error": f"{exc.__class__.__name__}: {exc}",
            "requiresPrivilege": True,
        }


def buildDefaultTools(includeStdioOnly: bool = True) -> list[AdaptedTool]:
    byName = {fn.__name__: fn for fn in ALL_TOOL_FUNCTIONS}
    tools: list[AdaptedTool] = []
    for name in SELECTED_TOOL_NAMES:
        fn = byName.get(name)
        if fn is None:
            continue
        tools.append(
            AdaptedTool(
                name=name,
                func=fn,
                riskLevel=RISK_LEVEL_MAP.get(name, ToolRiskLevel.WRITE),
            )
        )

    for name in MCP_ONLY_TOOL_NAMES:
        fn = globals()[name]
        tools.append(
            AdaptedTool(
                name=name,
                func=fn,
                riskLevel=_mcpOnlyRiskLevel(name),
            )
        )

    return tools


def _mcpOnlyRiskLevel(name: str) -> ToolRiskLevel:
    if name in {"addFirewallPortPrivileged", "removeFirewallPortPrivileged", "manageSystemServicePrivileged"}:
        return ToolRiskLevel.DANGEROUS
    if name in {"writePrivilegedFile", "nginxWriteStaticFile"}:
        return ToolRiskLevel.WRITE
    if name in {"submitElevation", "runPrivileged"}:
        return ToolRiskLevel.DANGEROUS
    if name == "submitOpsExperience":
        return ToolRiskLevel.WRITE  # 沉淀经验包属写操作，registry 自动强制 reason，天然可审计
    return ToolRiskLevel.READ_ONLY


def _toolFunc(name: str) -> Callable[..., Any]:
    for fn in ALL_TOOL_FUNCTIONS:
        if fn.__name__ == name:
            return fn
    raise KeyError(f"Tool function not found: {name}")


def _parseProcessSortBy(sortBy: str) -> ProcessSortBy:
    try:
        return ProcessSortBy(str(sortBy).lower())
    except ValueError as exc:
        raise ValueError("sortBy must be one of: cpu, memory, pid") from exc


def _truncate(value: str, maxLength: int) -> str:
    if len(value) <= maxLength:
        return value
    return value[: maxLength - 3] + "..."


# ════════════════════════════════════════════════════════════
#  V2 特权提权工具 — 通过 ElevationService + PrivilegedAgentClient
# ════════════════════════════════════════════════════════════


def submitElevation(
    commands: list[dict[str, Any]] | None = None,
    reason: str = "",
    ttl_seconds: int = 3600,
    max_ops: int = 10,
    inline_cmd: str = "",
    script_path: str = "",
    session_id: str = "",
) -> dict:
    """提交特权提权申请；同一目标的多个相关动作应合并为一个脚本并一次申请。
    生成一个一次性审批码，管理员需在 SSH 中执行
    `sudo nereus approve <CODE>` 批准。批准后使用 runPrivileged() 执行。

    支持三种互斥的提权通道；多个通道同时传入会直接拒绝，不做隐式优先级覆盖：

    选择决策:
    ├─ 恰好一个已注册的稳定命令 → 通道A
    ├─ 恰好一个简单的一次性 shell 命令 → 通道B
    └─ 两个或以上相关动作，或多步逻辑/条件/循环 → 先写脚本到 /opt/ndlmpanel/tmp_scripts/, 再通道C

    **通道 A — 预设命令（commands）**:
    高频稳定操作，使用注册命令列表:
    submitElevation(commands=[{"command": "mkdir", "args": ["-p", "/var/www/app"]}])

    **通道 B — 简单命令（inline_cmd）**:
    恰好一个不含 shell 控制符的一次性命令：
    submitElevation(inline_cmd="tar -czf /var/www/backup.tar.gz /var/www/html")

    **通道 C — 自由脚本（script_path）**:
    复杂多步操作，先用 writePrivilegedFile 写脚本到 /opt/ndlmpanel/tmp_scripts/, 再提交:
    submitElevation(script_path="/opt/ndlmpanel/tmp_scripts/migrate_logs.sh")

    ⚠ 三通道互斥：不要同时传 commands、inline_cmd、script_path。
    ⚠ commands 只能包含一个命令；两个或以上相关动作必须先写脚本。
    ⚠ inline_cmd 和 script_path 会触发 AI 安全审计（管理员可见完整命令/脚本）。
    ⚠ MCP 子进程不存储任何状态。code 由工具生成后返回，
      由 Gateway 进程的 _handleElevationResult 同步到 ElevationService。

    Args:
        commands: [通道A] 注册命令列表 [{"command": "mkdir", "args": [...]}, ...]
        reason: 申请原因说明（显示给管理员）
        ttl_seconds: code 有效期（秒），默认 1 小时
        max_ops: 批准后最大执行次数，默认 10
        inline_cmd: [通道B] 完整的 shell 命令字符串
        script_path: [通道C] 脚本文件路径（必须在 /opt/ndlmpanel/tmp_scripts/ 下）

    Returns:
        {"code": "NGA7-K3X9", "status": "pending", "commands": [...], ...}
    """
    import secrets as _secrets

    selectedChannels = sum(
        bool(value)
        for value in (commands, inline_cmd.strip(), script_path.strip())
    )
    if selectedChannels > 1:
        return _errorPayload(
            errorCode="ELEVATION_CHANNEL_CONFLICT",
            errorMessage=(
                "commands、inline_cmd、script_path 三种提权通道互斥，"
                "请只选择一种"
            ),
            requiresPrivilege=True,
            backend="mcp.guard",
        )
    if commands and len(commands) != 1:
        return _errorPayload(
            errorCode="MULTI_ACTION_REQUIRES_SCRIPT",
            errorMessage=(
                "多个特权动作必须合并为一个可审计脚本，写入 "
                f"{PRIVILEGED_SCRIPT_DIR}/ 后一次申请"
            ),
            requiresPrivilege=True,
            backend="mcp.guard",
        )
    if script_path and not _isUnderDirectory(
        script_path, PRIVILEGED_SCRIPT_DIR
    ):
        return _errorPayload(
            errorCode="PRIVILEGED_SCRIPT_PATH_INVALID",
            errorMessage=(
                "script_path 必须位于 "
                f"{PRIVILEGED_SCRIPT_DIR}/ 下，禁止工作区和 /tmp"
            ),
            requiresPrivilege=True,
            backend="mcp.guard",
        )
    if inline_cmd and _SHELL_CONTROL_RE.search(inline_cmd):
        return _errorPayload(
            errorCode="INLINE_COMMAND_NOT_SIMPLE",
            errorMessage=(
                "inline_cmd 仅允许一个简单命令；多步逻辑、管道、"
                "重定向或条件处理必须改用特权脚本"
            ),
            requiresPrivilege=True,
            backend="mcp.guard",
        )
    _chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    _code = "".join(_secrets.choice(_chars) for _ in range(4)) + "-" + "".join(_secrets.choice(_chars) for _ in range(4))

    _normalized_commands = []

    if inline_cmd:
        # 通道 B：自由命令
        _normalized_commands.append({"command": "exec_arbitrary_cmd", "args": [inline_cmd]})
    elif script_path:
        # 通道 C：脚本执行
        _normalized_commands.append({"command": "exec_arbitrary_script", "args": [script_path]})
    else:
        # 通道 A：注册命令
        if commands is None:
            commands = []
        for _c in commands:
            _cmd = _c["command"]
            if isinstance(_cmd, list):
                _cmd = " ".join(str(x) for x in _cmd)
            _normalized_commands.append({"command": _cmd, "args": _c.get("args", [])})

    _result = {
        "code": _code,
        "status": "pending",
        "commands": _normalized_commands,
        "reason": reason,
        "ttl_seconds": ttl_seconds,
        "max_ops": max_ops,
    }
    if inline_cmd:
        _result["inline_cmd"] = inline_cmd
    if script_path:
        _result["script_path"] = script_path
    return _result


def runPrivileged(
    token_id: str,
    command_index: int,
    args: list[str],
    session_id: str,
    reason: str = "",
) -> dict:
    """使用已批准的 token 执行特权命令。

    调用此工具前必须先通过 submitElevation 申请 + 管理员 approve。

    ⚠ 主执行逻辑不在 MCP 子进程！
    AgentCore._executeTool() 在 Gateway 进程中拦截此工具调用，
    直接在 Gateway 进程内调用本函数（不经过 stdio 发给 MCP 子进程），
    确保 ElevationService 的 token 存储与 AdminController 在同一进程。
    MCP 子进程中保留此函数仅用于 tools/list 注册 schema。

    如需执行特权命令的完整链路：
    LLM → AgentCore._runLoop → _handleApproval → _executeTool
    → [Gateway 进程] runPrivileged() → ElevationService.create_signed_request()
    → PrivilegedAgentClient.call_v2() → [Unix socket] → PrivilegedAgentServer

    Args:
        token_id: 管理员 approve 后返回的 token ID
        command_index: 命令在申请列表中的索引（0 开始）
        args: 实际执行的参数（必须与申请时一致，否则被拒绝）
        session_id: 当前 Agent session ID
        reason: 调用原因说明（仅用于审批展示，不参与执行逻辑）

    Returns:
        命令执行结果
    """
    from gateway.service.elevation_service import ElevationService

    svc = ElevationService()
    signed_req = svc.create_signed_request(
        token_id=token_id,
        command_index=command_index,
        actual_args=args,
        session_id=session_id,
    )
    if signed_req is None:
        raise McpToolExecutionError(
            _errorPayload(
                errorCode="ELEVATION_FAILED",
                errorMessage="Token 无效、过期、次数用尽或参数不匹配",
                backend="elevation",
            )
        )

    # 发送给特权代理执行
    client = PrivilegedAgentClient()
    try:
        return client.call_v2(signed_req)
    except PrivilegedAgentRemoteError as exc:
        raise McpToolExecutionError(
            _errorPayload(
                errorCode=exc.code,
                errorMessage=exc.message,
                details=exc.details,
                requiresPrivilege=True,
                backend="privileged_agent",
            )
        ) from exc


# ════════════════════════════════════════════════════════════
#  运维经验包工具（阶段 8）— OpsExperienceService 共用业务层
# ════════════════════════════════════════════════════════════


def searchOpsExperience(
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> dict:
    """按症状/关键词检索组织运维经验库（启用中的经验包）。

    返回标题+分类+标签+摘要+质量分，供诊断参考。默认排除 negative 教训包；
    显式传 category="negative" 时返回教训包（带 negativeOf 提示，二期做方案相似度匹配）。
    命中即计入 hitCount 反馈统计。

    Args:
        query: 症状/关键词，如 "nginx 502"、"证书过期"、"磁盘告警"
        category: 可选过滤 deployment|fault|optimization|security|negative
        limit: 返回条数上限（默认 10，最大 50）

    Returns:
        {"success": True, "data": [{"id", "title", "category", "osType", "tags",
                                    "riskLevel", "qualityScore", "hitCount", "summary"}, ...]}
    """
    from gateway.service.OpsExperienceService import OpsExperienceService

    svc = OpsExperienceService()
    try:
        items = svc.searchPacks(query=query, category=category, limit=limit)
        return {"success": True, "data": items}
    except Exception as exc:
        return _errorPayload(
            errorCode=exc.__class__.__name__,
            errorMessage=str(exc),
        )


def getOpsExperienceDetail(packId: int) -> dict:
    """取单个运维经验包完整内容，供处置方案参考。

    返回 deploymentDoc 正文 + stages 阶段 + pitfalls 坑 + earlyWarnings 预警特征
    + 附件清单（含绝对路径，可 readTextFile 只读参考；执行附件需走审批流程）。

    Args:
        packId: 经验包 id（来自 searchOpsExperience 返回）

    Returns:
        {"success": True, "data": {完整经验包}}
    """
    from gateway.service.OpsExperienceService import OpsExperienceService

    svc = OpsExperienceService()
    try:
        return {"success": True, "data": svc.getPackDetail(packId)}
    except Exception as exc:
        return _errorPayload(
            errorCode=exc.__class__.__name__,
            errorMessage=str(exc),
        )


def submitOpsExperience(
    title: str,
    category: str,
    deploymentDoc: str,
    tags: list[str] | None = None,
    stages: list[dict] | None = None,
    pitfalls: list[dict] | None = None,
    earlyWarnings: list[dict] | None = None,
    riskLevel: str = "medium",
    session_id: str = "",
    reason: str = "",
) -> dict:
    """处置成功后主动沉淀运维经验包（source=ai），反哺组织记忆。

    将本次处置写成 Markdown 正文（现象/原因/处置步骤/验证），并按需提供
    结构化字段：stages（阶段）、pitfalls（坑）、earlyWarnings（预警特征）。
    写入 source=ai，sourceSessionId 记录当前会话（可溯源审计）。
    WRITE 风险：registry 自动强制 reason 参数。

    Args:
        title: 标题（一句话），如 "Nginx SSL 证书过期导致 502"
        category: deployment|fault|optimization|security|negative
        deploymentDoc: 正文 Markdown（部署/处置完整说明，主体）
        tags: 标签，如 ["nginx", "ssl", "证书"]
        stages: [{"name", "goal", "steps", "verify", "pitfallsRef"}]
        pitfalls: [{"phenomenon", "cause", "solution", "stageRef"}]
        earlyWarnings: [{"metric", "condition", "threshold", "severity", "hint"}]
        riskLevel: low|medium|high（默认 medium；高危方案命中时提示人工复核）
        session_id: 当前 Agent 会话 id（溯源审计）
        reason: 沉淀经验包的原因（由 Agent 安全层注入并记录；不写入正文）

    Returns:
        {"success": True, "data": {创建的经验包}}
    """
    from gateway.service.OpsExperienceService import OpsExperienceService

    svc = OpsExperienceService()
    try:
        payload = {
            "title": title,
            "category": category,
            "deploymentDoc": deploymentDoc,
            "tags": tags or [],
            "stages": stages or [],
            "pitfalls": pitfalls or [],
            "earlyWarnings": earlyWarnings or [],
            "riskLevel": riskLevel,
        }
        pack = svc.submitPack(payload, sourceSessionId=session_id or None)
        return {"success": True, "data": pack}
    except Exception as exc:
        return _errorPayload(
            errorCode=exc.__class__.__name__,
            errorMessage=str(exc),
        )


def _callPrivileged(action: PrivilegedAction, payload: dict[str, Any]) -> Any:
    client = PrivilegedAgentClient()
    try:
        return client.call(
            action,
            payload,
            client.defaultContext("mcp.ndlmpanel_agent"),
        )
    except PrivilegedAgentRemoteError as exc:
        raise McpToolExecutionError(
            _errorPayload(
                errorCode=exc.code,
                errorMessage=exc.message,
                details=exc.details,
                requiresPrivilege=True,
                backend="privileged_agent",
            )
        ) from exc


def _errorPayload(
    errorCode: str,
    errorMessage: str,
    details: str | None = None,
    requiresPrivilege: bool = False,
    backend: str | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "errorCode": errorCode,
        "errorMessage": errorMessage,
        "details": details,
        "requiresPrivilege": requiresPrivilege,
        "backend": backend,
    }


def _looksPrivilegeFailure(message: str | None) -> bool:
    text = (message or "").lower()
    markers = (
        "sudo",
        "permission denied",
        "not permitted",
        "operation not permitted",
        "requires root",
        "need root",
        "权限",
        "root",
    )
    return any(marker in text for marker in markers)


def _toJsonable(value: Any) -> Any:
    if BaseModel is not None and isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, list):
        return [_toJsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_toJsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _toJsonable(item) for key, item in value.items()}
    return value


def _serializeResult(result: Any) -> str:
    if result is None:
        return "(no result)"
    if isinstance(result, str):
        return result
    return json.dumps(_toJsonable(result), ensure_ascii=False, indent=2, default=str)
