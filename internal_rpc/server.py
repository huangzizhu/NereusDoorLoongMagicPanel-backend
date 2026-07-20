from __future__ import annotations

import grp
import json
import logging
import os
import socket
import threading
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from internal_rpc.config import (
    backend_rpc_allowed_uids,
    backend_rpc_nonce_ttl,
    backend_rpc_public_key_path,
    backend_rpc_socket_group,
    backend_rpc_socket_mode,
    backend_rpc_socket_path,
    backend_rpc_timestamp_tolerance,
    ensure_socket_parent,
)
from internal_rpc.models import (
    InternalRpcErrorCode,
    InternalRpcRequest,
    InternalRpcResponse,
)
from internal_rpc.security import (
    NonceStore,
    check_timestamp_freshness,
    load_public_key,
    verify_peercred,
    verify_request_signature,
)

Handler = Callable[[dict[str, Any], InternalRpcRequest], Any]

_logger = logging.getLogger("internal_rpc.server")


class InternalRpcServer:
    def __init__(
        self,
        handlers: dict[str, Handler],
        *,
        socket_path: str | None = None,
        public_key_path: str | None = None,
        allowed_uids: set[int] | None = None,
    ):
        self.handlers = handlers
        self.socket_path = socket_path or backend_rpc_socket_path()
        self.public_key_path = public_key_path or backend_rpc_public_key_path()
        self.allowed_uids = allowed_uids if allowed_uids is not None else backend_rpc_allowed_uids()
        self.socket_group = backend_rpc_socket_group()
        self.socket_mode = backend_rpc_socket_mode()
        self.timestamp_tolerance = backend_rpc_timestamp_tolerance()
        self._nonce_store = NonceStore(backend_rpc_nonce_ttl())
        self._public_key = self._load_public_key()
        self._server_socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._prepare_socket_path()
        server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_socket.bind(self.socket_path)
        self._server_socket = server_socket
        self._apply_socket_permissions()
        server_socket.listen(32)
        self._running.set()
        self._thread = threading.Thread(
            target=self._serve_loop,
            name="internal-rpc-server",
            daemon=True,
        )
        self._thread.start()
        _logger.info(
            "internal RPC listening on %s allowed_uids=%s pubkey=%s",
            self.socket_path,
            sorted(self.allowed_uids),
            "loaded" if self._public_key else "missing",
        )

    def stop(self) -> None:
        self._running.clear()
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as wake_sock:
                wake_sock.settimeout(0.2)
                wake_sock.connect(self.socket_path)
        except OSError:
            pass
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=2)
        try:
            Path(self.socket_path).unlink(missing_ok=True)
        except OSError:
            _logger.exception("failed to unlink internal RPC socket: %s", self.socket_path)
        self._server_socket = None
        self._thread = None

    def _serve_loop(self) -> None:
        assert self._server_socket is not None
        while self._running.is_set():
            try:
                conn, _ = self._server_socket.accept()
            except OSError:
                if self._running.is_set():
                    _logger.exception("internal RPC accept failed")
                break
            if not self._running.is_set():
                conn.close()
                break
            self._serve_client(conn)

    def _serve_client(self, conn: socket.socket) -> None:
        with conn:
            audit_id = str(uuid.uuid4())
            response: InternalRpcResponse
            try:
                raw = self._read_line(conn)
                response = self._handle_raw(raw, conn, audit_id)
            except Exception as exc:
                _logger.exception("audit_id=%s internal RPC unhandled error", audit_id)
                response = self._error(
                    audit_id,
                    InternalRpcErrorCode.INTERNAL_ERROR,
                    "后端内部 RPC 处理失败",
                    str(exc),
                )
            conn.sendall((response.model_dump_json() + "\n").encode("utf-8"))

    def _handle_raw(
        self,
        raw: bytes,
        conn: socket.socket,
        audit_id: str,
    ) -> InternalRpcResponse:
        if not raw:
            return self._error(audit_id, InternalRpcErrorCode.INVALID_REQUEST, "空请求")

        try:
            _, uid, _ = verify_peercred(conn, self.allowed_uids)
        except PermissionError as exc:
            _logger.warning("audit_id=%s peercred_denied: %s", audit_id, exc)
            return self._error(
                audit_id,
                InternalRpcErrorCode.PEER_UID_DENIED,
                "连接方不在允许的 UID 列表中",
                str(exc),
            )

        try:
            raw_data = json.loads(raw.decode("utf-8"))
            request = InternalRpcRequest(**raw_data)
        except Exception as exc:
            return self._error(
                audit_id,
                InternalRpcErrorCode.INVALID_REQUEST,
                "请求格式非法",
                str(exc),
            )

        if self._public_key is None:
            return self._error(
                audit_id,
                InternalRpcErrorCode.SIGNATURE_INVALID,
                "内部 RPC 公钥未配置",
                self.public_key_path,
            )

        if not verify_request_signature(request, self._public_key):
            _logger.warning(
                "audit_id=%s uid=%d method=%s signature_invalid",
                audit_id,
                uid,
                request.method,
            )
            return self._error(
                audit_id,
                InternalRpcErrorCode.SIGNATURE_INVALID,
                "签名验证失败",
            )

        if not check_timestamp_freshness(request.timestamp, self.timestamp_tolerance):
            return self._error(
                audit_id,
                InternalRpcErrorCode.SIGNATURE_EXPIRED,
                "请求时间戳已过期或偏差过大",
            )

        if not self._nonce_store.check_and_store(request.nonce):
            return self._error(
                audit_id,
                InternalRpcErrorCode.NONCE_REPLAY,
                "Nonce 重复",
            )

        handler = self.handlers.get(request.method)
        if handler is None:
            return self._error(
                audit_id,
                InternalRpcErrorCode.UNKNOWN_METHOD,
                "未知内部 RPC 方法",
                request.method,
            )

        try:
            data = handler(request.params, request)
            return InternalRpcResponse(success=True, auditId=audit_id, data=data)
        except Exception as exc:
            _logger.exception(
                "audit_id=%s uid=%d method=%s handler_error",
                audit_id,
                uid,
                request.method,
            )
            return self._error(
                audit_id,
                InternalRpcErrorCode.INTERNAL_ERROR,
                "内部 RPC 方法执行失败",
                _exception_message(exc),
            )

    @staticmethod
    def _read_line(conn: socket.socket) -> bytes:
        raw = b""
        while not raw.endswith(b"\n"):
            chunk = conn.recv(65536)
            if not chunk:
                break
            raw += chunk
        return raw.rstrip(b"\n")

    def _prepare_socket_path(self) -> None:
        ensure_socket_parent(self.socket_path)
        socket_file = Path(self.socket_path)
        if socket_file.exists() or socket_file.is_socket():
            socket_file.unlink()

    def _apply_socket_permissions(self) -> None:
        try:
            os.chmod(self.socket_path, self.socket_mode)
            if self.socket_group:
                group = grp.getgrnam(self.socket_group)
                os.chown(self.socket_path, os.getuid(), group.gr_gid)
        except Exception:
            _logger.exception("failed to apply internal RPC socket permissions")

    def _load_public_key(self):
        path = Path(self.public_key_path)
        if not path.exists():
            _logger.warning("internal RPC public key missing: %s", self.public_key_path)
            return None
        try:
            return load_public_key(self.public_key_path)
        except Exception:
            _logger.exception("failed to load internal RPC public key: %s", self.public_key_path)
            return None

    @staticmethod
    def _error(
        audit_id: str,
        code: InternalRpcErrorCode,
        message: str,
        details: str | None = None,
    ) -> InternalRpcResponse:
        return InternalRpcResponse(
            success=False,
            auditId=audit_id,
            errorCode=code.value,
            errorMessage=message,
            errorDetails=details,
        )


def _exception_message(exc: Exception) -> str:
    user_message = getattr(exc, "userMessage", None)
    inner_message = getattr(exc, "innerMessage", None)
    return str(user_message or inner_message or exc)
