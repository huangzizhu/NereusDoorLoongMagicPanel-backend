"""stdio MCP client adapter for AgentSession.

This module lets the agent consume an external line-delimited JSON-RPC MCP
server while preserving the existing registry/dispatcher shape used by
AgentCore.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from agent.shared.types import ToolRiskLevel
from ndlmpanel_agent.mcp.protocol.json_rpc import encodeRequest


MCP_PROTOCOL_VERSION = "2025-06-18"


def defaultStdioCommand() -> list[str]:
    return [sys.executable, "-m", "ndlmpanel_agent.mcp"]


def defaultStdioCwd() -> str:
    return str(Path(__file__).resolve().parents[2])


class StdioMcpBridge:
    """Owns one stdio MCP child process and exposes registry/dispatcher views."""

    def __init__(self, command: list[str] | None = None, cwd: str | None = None):
        self._client = StdioMcpClient(
            command or defaultStdioCommand(),
            cwd or defaultStdioCwd(),
        )
        tools = self._client.initialize()
        self.registry = StdioMcpRegistry(tools)
        self.dispatcher = StdioMcpDispatcher(self._client)

    def close(self) -> None:
        self._client.close()


class StdioMcpClient:
    def __init__(self, command: list[str], cwd: str):
        if not command:
            raise ValueError("stdio MCP command cannot be empty")
        self._lock = threading.Lock()
        self._nextId = 1
        self._proc = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

    def initialize(self) -> list[dict]:
        self.request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "ndlmpanel-agent",
                    "version": "0.1.0",
                },
            },
        )
        self.notify("notifications/initialized", {})
        result = self.request("tools/list", {})
        tools = result.get("tools", [])
        if not isinstance(tools, list):
            raise RuntimeError("MCP tools/list returned invalid tools payload")
        return tools

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict:
        reqId = self._nextId
        self._nextId += 1
        raw = encodeRequest(method, params or {}, reqId)
        response = self.handle(raw)
        if response is None:
            raise RuntimeError(f"MCP request {method} returned no response")
        data = json.loads(response)
        if "error" in data:
            message = data["error"].get("message", str(data["error"]))
            raise RuntimeError(f"MCP request {method} failed: {message}")
        result = data.get("result", {})
        if not isinstance(result, dict):
            raise RuntimeError(f"MCP request {method} returned invalid result")
        return result

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self.handle(encodeRequest(method, params or {}, None))

    def handle(self, raw: str) -> str | None:
        with self._lock:
            self._ensureRunning()
            assert self._proc.stdin is not None
            self._proc.stdin.write(raw + "\n")
            self._proc.stdin.flush()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                expectsResponse = True
            else:
                expectsResponse = "id" in data
            if not expectsResponse:
                return None

            assert self._proc.stdout is not None
            line = self._proc.stdout.readline()
            if line == "":
                self._ensureRunning()
                raise RuntimeError("MCP stdio server closed stdout")
            return line.strip()

    def close(self) -> None:
        if self._proc.poll() is not None:
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait(timeout=3)

    def _ensureRunning(self) -> None:
        code = self._proc.poll()
        if code is not None:
            raise RuntimeError(f"MCP stdio server exited with code {code}")


class StdioMcpRegistry:
    def __init__(self, tools: list[dict]):
        self._tools = tools
        self._riskLevels = {
            str(tool.get("name", "")): _riskFromMcpTool(tool)
            for tool in tools
            if tool.get("name")
        }

    def listTools(self) -> list[dict]:
        schemas = [_mcpToolToOpenAiSchema(tool) for tool in self._tools]
        schemas.sort(key=lambda item: item["function"]["name"])
        return schemas

    def getRiskLevel(self, name: str) -> ToolRiskLevel:
        return self._riskLevels.get(name, ToolRiskLevel.WRITE)


class StdioMcpDispatcher:
    def __init__(self, client: StdioMcpClient):
        self._client = client

    def handle(self, raw: str) -> str | None:
        return self._client.handle(raw)


def _mcpToolToOpenAiSchema(tool: dict) -> dict:
    name = str(tool.get("name", ""))
    description = str(tool.get("description", ""))
    inputSchema = tool.get("inputSchema", {})
    if not isinstance(inputSchema, dict):
        inputSchema = {"type": "object", "properties": {}}
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": inputSchema,
        },
    }


def _riskFromMcpTool(tool: dict) -> ToolRiskLevel:
    annotations = tool.get("annotations", {})
    if not isinstance(annotations, dict):
        annotations = {}
    raw = annotations.get("riskLevel")
    if raw is None:
        if annotations.get("destructiveHint") is True:
            raw = ToolRiskLevel.DANGEROUS.value
        elif annotations.get("readOnlyHint") is True:
            raw = ToolRiskLevel.READ_ONLY.value
    try:
        return ToolRiskLevel(raw)
    except ValueError:
        return ToolRiskLevel.WRITE


# ── Multi-Server Aggregation ──


class MultiServerSpec:
    """Descriptor for an external stdio MCP server."""

    def __init__(self, name: str, command: list[str], cwd: str | None = None):
        if not name.strip():
            raise ValueError("MCP server name cannot be empty")
        if not command:
            raise ValueError(f"MCP server {name!r} command cannot be empty")
        self.name = name
        self.command = command
        self.cwd = cwd


class MultiStdioMcpBridge:
    """Aggregate multiple StdioMcpBridge instances into one registry/dispatcher.

    tools/list merges all servers' tools.
    tools/call routes by tool name to the owning server.
    Name conflicts across servers raise a RuntimeError on construction.
    """

    def __init__(self, servers: list[MultiServerSpec]):
        if not servers:
            raise ValueError("MultiStdioMcpBridge requires at least one server")

        self._bridges: list[StdioMcpBridge] = []
        self._toolToServer: dict[str, str] = {}
        self._toolNames: list[str] = []
        self._toolDicts: list[dict] = []
        self._riskLevels: dict[str, ToolRiskLevel] = {}

        errors: list[str] = []
        for spec in servers:
            try:
                bridge = StdioMcpBridge(command=spec.command, cwd=spec.cwd)
            except Exception as exc:
                errors.append(f"server {spec.name!r} failed to start: {exc}")
                continue
            self._bridges.append(bridge)

            for tool in bridge.registry._tools:
                name = str(tool.get("name", ""))
                if not name:
                    continue
                if name in self._toolToServer:
                    errors.append(
                        f"tool name conflict: {name!r} provided by both "
                        f"{self._toolToServer[name]!r} and {spec.name!r}"
                    )
                    continue
                self._toolToServer[name] = spec.name
                self._toolNames.append(name)
                self._toolDicts.append(tool)
                self._riskLevels[name] = bridge.registry.getRiskLevel(name)

        if errors:
            for bridge in self._bridges:
                try:
                    bridge.close()
                except Exception:
                    pass
            self._bridges.clear()
            raise RuntimeError("MCP server initialization failed:\n" + "\n".join(errors))

        self.registry = _AggregatedRegistry(
            tool_dicts=self._toolDicts,
            risk_levels=self._riskLevels,
        )
        self.dispatcher = _AggregatedDispatcher(
            tool_to_server=self._toolToServer,
            bridges={spec.name: bridge for spec, bridge in zip(servers, self._bridges)},
        )

    def close(self) -> None:
        for bridge in reversed(self._bridges):
            try:
                bridge.close()
            except Exception:
                pass
        self._bridges.clear()


class _AggregatedRegistry:
    """Unified registry that delegates to aggregated tool metadata."""

    def __init__(
        self,
        tool_dicts: list[dict],
        risk_levels: dict[str, ToolRiskLevel],
    ):
        self._tool_dicts = tool_dicts
        self._risk_levels = risk_levels

    def listTools(self) -> list[dict]:
        schemas = [_mcpToolToOpenAiSchema(tool) for tool in self._tool_dicts]
        schemas.sort(key=lambda item: item["function"]["name"])
        return schemas

    def getRiskLevel(self, name: str) -> ToolRiskLevel:
        return self._risk_levels.get(name, ToolRiskLevel.WRITE)


class _AggregatedDispatcher:
    """Unified dispatcher that routes tool calls to the owning bridge."""

    def __init__(
        self,
        tool_to_server: dict[str, str],
        bridges: dict[str, StdioMcpBridge],
    ):
        self._tool_to_server = tool_to_server
        self._bridges = bridges

    def handle(self, raw: str) -> str | None:
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            return None

        params = req.get("params", {})
        tool_name = params.get("name", "") if isinstance(params, dict) else ""
        server_name = self._tool_to_server.get(tool_name)

        if server_name is None:
            import json as _json
            from ndlmpanel_agent.mcp.protocol.json_rpc import encodeError, METHOD_NOT_FOUND

            error_payload = encodeError(
                req.get("id"),
                METHOD_NOT_FOUND,
                f"Unknown tool: {tool_name}",
            )
            return error_payload

        bridge = self._bridges.get(server_name)
        if bridge is None:
            from ndlmpanel_agent.mcp.protocol.json_rpc import encodeError, INTERNAL_ERROR

            return encodeError(
                req.get("id"),
                INTERNAL_ERROR,
                f"Server {server_name!r} not available for tool {tool_name!r}",
            )

        return bridge.dispatcher.handle(raw)
