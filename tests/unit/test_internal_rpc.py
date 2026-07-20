from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone

from internal_rpc.security import sign_request_payload
import internal_rpc.server as server_module
from internal_rpc.server import InternalRpcServer
from privileged_agent.crypto import (
    dump_private_key_pem,
    dump_public_key_pem,
    generate_keypair,
    load_private_key_pem,
)


def _server_and_key(tmp_path, allowed_uids: set[int] | None = None):
    keypair = generate_keypair()
    priv_path = tmp_path / "rpc_priv.pem"
    pub_path = tmp_path / "rpc_pub.pem"
    priv_path.write_bytes(dump_private_key_pem(keypair.priv))
    pub_path.write_bytes(dump_public_key_pem(keypair.pub))
    server = InternalRpcServer(
        {"echo": lambda params, _request: {"echo": params}},
        socket_path=str(tmp_path / "rpc.sock"),
        public_key_path=str(pub_path),
        allowed_uids=allowed_uids if allowed_uids is not None else {os.getuid()},
    )
    return server, load_private_key_pem(priv_path.read_bytes())


def _signed_raw(private_key, method: str = "echo", **overrides) -> bytes:
    payload = {
        "requestId": "req-1",
        "method": method,
        "params": {"value": "ok"},
        "caller": {"source": "unit_test", "userId": 0},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": "nonce-12345678",
    }
    payload.update(overrides)
    payload["signature"] = sign_request_payload(payload, private_key)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _call(server: InternalRpcServer, raw: bytes):
    client_sock, server_sock = socket.socketpair()
    try:
        return server._handle_raw(raw, server_sock, "audit-test")
    finally:
        client_sock.close()
        server_sock.close()


def _allow_peercred(monkeypatch):
    monkeypatch.setattr(
        server_module,
        "verify_peercred",
        lambda _conn, _allowed_uids: (123, os.getuid(), os.getgid()),
    )


def _deny_peercred(monkeypatch):
    def _raise(_conn, _allowed_uids):
        raise PermissionError("denied")

    monkeypatch.setattr(server_module, "verify_peercred", _raise)


def test_internal_rpc_accepts_valid_signed_request(tmp_path, monkeypatch):
    _allow_peercred(monkeypatch)
    server, private_key = _server_and_key(tmp_path)
    response = _call(server, _signed_raw(private_key))
    assert response.success is True
    assert response.data == {"echo": {"value": "ok"}}


def test_internal_rpc_rejects_denied_uid(tmp_path, monkeypatch):
    _deny_peercred(monkeypatch)
    server, private_key = _server_and_key(tmp_path, allowed_uids={999999})
    response = _call(server, _signed_raw(private_key))
    assert response.success is False
    assert response.errorCode == "PEER_UID_DENIED"


def test_internal_rpc_rejects_invalid_signature(tmp_path, monkeypatch):
    _allow_peercred(monkeypatch)
    server, private_key = _server_and_key(tmp_path)
    raw_data = json.loads(_signed_raw(private_key).decode("utf-8"))
    raw_data["params"] = {"value": "tampered"}
    response = _call(server, json.dumps(raw_data).encode("utf-8"))
    assert response.success is False
    assert response.errorCode == "SIGNATURE_INVALID"


def test_internal_rpc_rejects_expired_timestamp(tmp_path, monkeypatch):
    _allow_peercred(monkeypatch)
    server, private_key = _server_and_key(tmp_path)
    response = _call(
        server,
        _signed_raw(private_key, timestamp="2000-01-01T00:00:00+00:00"),
    )
    assert response.success is False
    assert response.errorCode == "SIGNATURE_EXPIRED"


def test_internal_rpc_rejects_replayed_nonce(tmp_path, monkeypatch):
    _allow_peercred(monkeypatch)
    server, private_key = _server_and_key(tmp_path)
    raw = _signed_raw(private_key)
    assert _call(server, raw).success is True
    response = _call(server, raw)
    assert response.success is False
    assert response.errorCode == "NONCE_REPLAY"


def test_internal_rpc_rejects_unknown_method(tmp_path, monkeypatch):
    _allow_peercred(monkeypatch)
    server, private_key = _server_and_key(tmp_path)
    response = _call(server, _signed_raw(private_key, method="missing.method"))
    assert response.success is False
    assert response.errorCode == "UNKNOWN_METHOD"
