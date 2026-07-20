from __future__ import annotations

import json
import os
import socket
import uuid
from datetime import datetime, timezone
from typing import Any

from internal_rpc.config import (
    backend_rpc_private_key_path,
    backend_rpc_socket_path,
)
from internal_rpc.models import InternalRpcResponse
from internal_rpc.security import load_private_key, sign_request_payload


class BackendRpcError(RuntimeError):
    def __init__(
        self,
        error_code: str,
        error_message: str,
        error_details: str | None = None,
    ):
        super().__init__(error_message)
        self.errorCode = error_code
        self.errorMessage = error_message
        self.errorDetails = error_details


class BackendRpcClient:
    def __init__(
        self,
        socket_path: str | None = None,
        private_key_path: str | None = None,
        timeout: float = 5.0,
    ):
        self.socket_path = socket_path or backend_rpc_socket_path()
        self.private_key_path = private_key_path or backend_rpc_private_key_path()
        self.timeout = timeout
        self._private_key = None

    def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        caller: dict[str, Any] | None = None,
    ) -> Any:
        if not os.path.exists(self.socket_path):
            raise BackendRpcError(
                "SERVICE_UNAVAILABLE",
                "后端内部 RPC socket 不存在",
                self.socket_path,
            )
        request = self._build_request(method, params or {}, caller or {})
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect(self.socket_path)
                raw = json.dumps(
                    request,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8") + b"\n"
                sock.sendall(raw)
                response_raw = self._read_line(sock)
        except FileNotFoundError as exc:
            raise BackendRpcError(
                "SERVICE_UNAVAILABLE",
                "后端内部 RPC socket 不存在",
                self.socket_path,
            ) from exc
        except (ConnectionRefusedError, TimeoutError, socket.timeout, OSError) as exc:
            raise BackendRpcError(
                "SERVICE_UNAVAILABLE",
                "后端内部 RPC 不可用",
                str(exc),
            ) from exc

        try:
            response = InternalRpcResponse(**json.loads(response_raw.decode("utf-8")))
        except Exception as exc:
            raise BackendRpcError(
                "INVALID_RESPONSE",
                "后端内部 RPC 响应格式非法",
                str(exc),
            ) from exc

        if not response.success:
            raise BackendRpcError(
                response.errorCode or "INTERNAL_ERROR",
                response.errorMessage or "后端内部 RPC 调用失败",
                response.errorDetails,
            )
        return response.data

    def _build_request(
        self,
        method: str,
        params: dict[str, Any],
        caller: dict[str, Any],
    ) -> dict[str, Any]:
        base = {
            "requestId": str(uuid.uuid4()),
            "method": method,
            "params": params,
            "caller": {
                "source": caller.get("source", "agent_mcp"),
                "userId": caller.get("userId", 0),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nonce": str(uuid.uuid4()),
        }
        try:
            private_key = self._get_private_key()
            base["signature"] = sign_request_payload(base, private_key)
        except Exception as exc:
            raise BackendRpcError(
                "SIGNING_FAILED",
                "后端内部 RPC 请求签名失败",
                str(exc),
            ) from exc
        return base

    def _get_private_key(self):
        if self._private_key is None:
            self._private_key = load_private_key(self.private_key_path)
        return self._private_key

    @staticmethod
    def _read_line(sock: socket.socket) -> bytes:
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if chunk.endswith(b"\n"):
                break
        return b"".join(chunks).rstrip(b"\n")
