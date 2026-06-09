"""MCP request dispatcher for initialize, tools/list, tools/call and ping."""

from __future__ import annotations

from typing import Any

from ..protocol.json_rpc import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JsonRpcProtocolError,
    decodeRequest,
    encodeError,
    encodeResult,
)
from .registry import ToolRegistry


MCP_PROTOCOL_VERSION = "2025-06-18"


class McpDispatcher:
    def __init__(
        self,
        registry: ToolRegistry,
        serverName: str = "ndlmpanel-agent",
        serverVersion: str = "0.1.0",
    ):
        self._reg = registry
        self._name = serverName
        self._ver = serverVersion
        self._initialized = False

    def handle(self, raw: str) -> str | None:
        try:
            req = decodeRequest(raw)
        except JsonRpcProtocolError as exc:
            return encodeError(exc.reqId, exc.code, exc.message)

        try:
            handler = getattr(self, f"_handle_{req.method.replace('/', '_')}", None)
            if handler is None:
                if req.id is None:
                    return None
                return encodeError(req.id, METHOD_NOT_FOUND, f"Unknown method: {req.method}")

            result = handler(req.params)
            if req.id is None:
                return None
            return encodeResult(req.id, result)
        except JsonRpcProtocolError as exc:
            if req.id is None:
                return None
            return encodeError(req.id, exc.code, exc.message)
        except Exception as exc:
            if req.id is None:
                return None
            return encodeError(req.id, INTERNAL_ERROR, str(exc))

    def _handle_initialize(self, params: dict[str, Any]) -> dict:
        clientVersion = params.get("protocolVersion")
        if clientVersion is not None and not isinstance(clientVersion, str):
            raise JsonRpcProtocolError(INVALID_PARAMS, "protocolVersion must be a string")
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "serverInfo": {"name": self._name, "version": self._ver},
            "capabilities": {"tools": {"listChanged": False}},
        }

    def _handle_notifications_initialized(self, params: dict[str, Any]) -> dict:
        self._initialized = True
        return {}

    def _handle_tools_list(self, params: dict[str, Any]) -> dict:
        listTools = getattr(self._reg, "listMcpTools", self._reg.listTools)
        return {"tools": listTools()}

    def _handle_tools_call(self, params: dict[str, Any]) -> dict:
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise JsonRpcProtocolError(INVALID_PARAMS, "tools/call requires a tool name")

        arguments = params.get("arguments", {})
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise JsonRpcProtocolError(INVALID_PARAMS, "tools/call arguments must be an object")

        try:
            result = self._reg.callTool(name, arguments)
        except KeyError:
            raise JsonRpcProtocolError(INVALID_PARAMS, f"Unknown tool: {name}") from None

        return {"content": result.content, "isError": result.isError}

    def _handle_ping(self, params: dict[str, Any]) -> dict:
        return {}
