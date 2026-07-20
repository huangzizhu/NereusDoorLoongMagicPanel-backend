from __future__ import annotations

import socket
import struct
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any

from privileged_agent.crypto import (
    load_private_key_pem,
    load_public_key_pem,
    sign,
    verify,
)

from internal_rpc.models import InternalRpcRequest


def signature_payload(request: InternalRpcRequest | dict[str, Any]) -> dict[str, Any]:
    if isinstance(request, InternalRpcRequest):
        data = request.model_dump(mode="json")
    else:
        data = dict(request)
    data.pop("signature", None)
    return {
        "requestId": data.get("requestId"),
        "method": data.get("method"),
        "params": data.get("params", {}),
        "caller": data.get("caller"),
        "timestamp": data.get("timestamp"),
        "nonce": data.get("nonce"),
    }


def load_private_key(path: str):
    return load_private_key_pem(Path(path).read_bytes())


def load_public_key(path: str):
    return load_public_key_pem(Path(path).read_bytes())


def sign_request_payload(payload: dict[str, Any], private_key) -> str:
    return sign(signature_payload(payload), private_key)


def verify_request_signature(request: InternalRpcRequest, public_key) -> bool:
    return verify(signature_payload(request), request.signature, public_key)


def verify_peercred(conn: socket.socket, allowed_uids: set[int]) -> tuple[int, int, int]:
    try:
        cred = conn.getsockopt(
            socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
        )
        pid, uid, gid = struct.unpack("3i", cred)
    except OSError as exc:
        raise PermissionError(f"无法获取对端凭证: {exc}") from exc

    if uid not in allowed_uids:
        raise PermissionError(f"对端 UID={uid} 不在允许列表 {allowed_uids} 中")
    return pid, uid, gid


def check_timestamp_freshness(timestamp_str: str, tolerance_seconds: int) -> bool:
    try:
        ts = datetime.fromisoformat(timestamp_str)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return abs((ts.astimezone(timezone.utc) - now).total_seconds()) <= tolerance_seconds
    except (TypeError, ValueError):
        return False


class NonceStore:
    def __init__(self, ttl_seconds: int):
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._items: dict[str, float] = {}

    def check_and_store(self, nonce: str) -> bool:
        now = time()
        with self._lock:
            expired = [key for key, expiry in self._items.items() if expiry < now]
            for key in expired:
                del self._items[key]
            if nonce in self._items:
                return False
            self._items[nonce] = now + self._ttl_seconds
            return True
