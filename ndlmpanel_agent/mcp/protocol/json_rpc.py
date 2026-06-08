"""JSON-RPC 2.0 helpers used by the MCP transports."""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any

JSONRPC_VERSION = "2.0"
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class JsonRpcProtocolError(Exception):
    def __init__(self, code: int, message: str, reqId: int | str | None = None):
        self.code = code
        self.message = message
        self.reqId = reqId
        super().__init__(message)


@dataclass
class JsonRpcRequest:
    jsonrpc: str = JSONRPC_VERSION
    id: int | str | None = None
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)


def encodeRequest(
    method: str, params: dict | None = None, reqId: int | str | None = None
) -> str:
    req = {"jsonrpc": JSONRPC_VERSION, "method": method, "params": params or {}}
    if reqId is not None:
        req["id"] = reqId
    return json.dumps(req, ensure_ascii=False)


def decodeRequest(raw: str) -> JsonRpcRequest:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JsonRpcProtocolError(PARSE_ERROR, f"JSON parse error: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise JsonRpcProtocolError(INVALID_REQUEST, "JSON-RPC message must be an object")

    reqId = data.get("id")
    if data.get("jsonrpc") != JSONRPC_VERSION:
        raise JsonRpcProtocolError(INVALID_REQUEST, "jsonrpc must be '2.0'", reqId)

    method = data.get("method")
    if not isinstance(method, str) or not method:
        raise JsonRpcProtocolError(INVALID_REQUEST, "method must be a non-empty string", reqId)

    params = data.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise JsonRpcProtocolError(INVALID_PARAMS, "params must be an object", reqId)

    return JsonRpcRequest(
        id=reqId,
        method=method,
        params=params,
    )


def encodeResult(reqId: int | str | None, result: Any) -> str:
    return json.dumps(
        {"jsonrpc": JSONRPC_VERSION, "id": reqId, "result": result}, ensure_ascii=False
    )


def encodeError(reqId: int | str | None, code: int, message: str) -> str:
    return json.dumps(
        {
            "jsonrpc": JSONRPC_VERSION,
            "id": reqId,
            "error": {"code": code, "message": message},
        },
        ensure_ascii=False,
    )
