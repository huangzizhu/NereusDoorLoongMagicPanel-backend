"""Adapters from utils.toolFunction tools to MCP tool definitions."""

from __future__ import annotations

import dataclasses
import json
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
    "createDirectory",
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
    "manageSystemService",
    "getFirewallStatus",
    "listFirewallPorts",
    "addFirewallPort",
    "removeFirewallPort",
    "checkDockerInstalled",
    "getDockerContainers",
    "getDockerContainerInfo",
    "getDockerContainerLogs",
    "startDockerContainer",
    "stopDockerContainer",
    "restartDockerContainer",
    "checkNginxInstalled",
    "getNginxStatus",
    "testNginxConfig",
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
    "createDirectory": "Create a directory, including missing parents.",
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
    "manageSystemService": "Start, stop, restart, enable, disable, or inspect a systemd service.",
    "getFirewallStatus": "Inspect active firewall backend and status.",
    "listFirewallPorts": "List firewall port rules using the direct tool path. This may require root or passwordless sudo; prefer listFirewallPortsPrivileged when available.",
    "addFirewallPort": "Allow a firewall port rule using the direct sudo fallback. Prefer addFirewallPortPrivileged when available.",
    "removeFirewallPort": "Remove a firewall port rule using the direct sudo fallback. Prefer removeFirewallPortPrivileged when available.",
    "checkDockerInstalled": "Check whether Docker is installed.",
    "getDockerContainers": "List Docker containers.",
    "getDockerContainerInfo": "Inspect one Docker container with full docker inspect output. This may return sensitive or very large data; prefer getDockerContainerSummary.",
    "getDockerContainerLogs": "Read Docker container logs.",
    "startDockerContainer": "Start a Docker container.",
    "stopDockerContainer": "Stop a Docker container.",
    "restartDockerContainer": "Restart a Docker container.",
    "checkNginxInstalled": "Check whether Nginx is installed.",
    "getNginxStatus": "Inspect Nginx runtime status.",
    "testNginxConfig": "Run nginx configuration validation using the direct sudo fallback. Prefer testNginxConfigPrivileged when available.",
    "getNginxSiteList": "List known Nginx site configurations.",
    "getNginxSiteConfig": "Read one Nginx site configuration.",
    "checkDatabaseInstalled": "Check whether a database engine is installed.",
    "getDatabaseStatus": "Inspect database service status.",
    "executeCommand": "Execute one argv-style system command without shell expansion. stdio mode only.",
    "listProcessesBrief": "Return a compact process list for agents with limit, sorting, and optional command text.",
    "getProcessAnomalies": "Return a compact list of zombie processes. Set includeReparented=true to also inspect processes reparented to PID 1.",
    "getDockerContainerSummary": "Return a compact Docker container summary without full docker inspect details.",
    "testNginxConfigPrivileged": "Validate Nginx configuration through the privileged agent.",
    "listFirewallPortsPrivileged": "List firewall port rules through the privileged agent.",
    "addFirewallPortPrivileged": "Add an allow firewall port rule through the privileged agent.",
    "removeFirewallPortPrivileged": "Remove an allow firewall port rule through the privileged agent.",
    "manageSystemServicePrivileged": "Inspect or change an allowed systemd service through the privileged agent for non-status actions.",
}

TOOL_ANNOTATIONS: dict[str, dict[str, Any]] = {
    "listProcesses": {"mayReturnLargeOutput": True, "preferredAlternative": "listProcessesBrief"},
    "getZombieOrphanProcesses": {"preferredAlternative": "getProcessAnomalies"},
    "getDockerContainerInfo": {
        "mayReturnLargeOutput": True,
        "mayExposeSensitiveData": True,
        "preferredAlternative": "getDockerContainerSummary",
    },
    "writeTextFile": {"requiresExistingFile": True, "createFileBeforeWrite": True},
    "testNginxConfig": {"requiresPrivilege": True, "sudoFallback": True},
    "listFirewallPorts": {"requiresPrivilege": True, "sudoFallback": True},
    "addFirewallPort": {"requiresPrivilege": True, "sudoFallback": True},
    "removeFirewallPort": {
        "requiresPrivilege": True,
        "sudoFallback": True,
    },
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

    if includeStdioOnly:
        tools.append(
            AdaptedTool(
                name=executeCommand.__name__,
                func=executeCommand,
                riskLevel=ToolRiskLevel.DANGEROUS,
                stdinOnly=True,
            )
        )

    return tools


def _mcpOnlyRiskLevel(name: str) -> ToolRiskLevel:
    if name in {"addFirewallPortPrivileged", "removeFirewallPortPrivileged", "manageSystemServicePrivileged"}:
        return ToolRiskLevel.DANGEROUS
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
