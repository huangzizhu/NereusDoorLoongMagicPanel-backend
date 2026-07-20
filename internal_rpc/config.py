from __future__ import annotations

import os
from pathlib import Path

from ProjectRoot import getProjectRootPath

_DOTENV_LOADED = False


def _load_dotenv_once() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True

    env_path = getProjectRootPath().joinpath(".env")
    if not env_path.exists():
        return

    try:
        with open(env_path, encoding="utf-8") as env_file:
            for line in env_file:
                item = line.strip()
                if not item or item.startswith("#") or "=" not in item:
                    continue
                if item.startswith("export "):
                    item = item[len("export "):].strip()
                key, _, value = item.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


def _getenv(name: str, default: str) -> str:
    _load_dotenv_once()
    return os.getenv(name, default)


def backend_rpc_socket_path() -> str:
    return _getenv(
        "NDLM_BACKEND_RPC_SOCKET",
        str(getProjectRootPath().joinpath("runtime", "ndlmpanel-backend-rpc.sock")),
    )


def backend_rpc_socket_group() -> str:
    return _getenv("NDLM_BACKEND_RPC_SOCKET_GROUP", "")


def backend_rpc_socket_mode() -> int:
    return int(_getenv("NDLM_BACKEND_RPC_SOCKET_MODE", "660"), 8)


def backend_rpc_public_key_path() -> str:
    return _getenv(
        "NDLM_BACKEND_RPC_PUBKEY",
        str(getProjectRootPath().joinpath("runtime", "backend_rpc_ed25519_pub.pem")),
    )


def backend_rpc_private_key_path() -> str:
    return _getenv(
        "NDLM_BACKEND_RPC_PRIVKEY",
        str(getProjectRootPath().joinpath("runtime", "backend_rpc_ed25519_priv.pem")),
    )


def backend_rpc_allowed_uids() -> set[int]:
    uid_str = _getenv("NDLM_BACKEND_RPC_ALLOWED_UIDS", str(os.getuid()))
    return {int(u.strip()) for u in uid_str.split(",") if u.strip()}


def backend_rpc_nonce_ttl() -> int:
    return int(_getenv("NDLM_BACKEND_RPC_NONCE_TTL", "300"))


def backend_rpc_timestamp_tolerance() -> int:
    return int(_getenv("NDLM_BACKEND_RPC_TIMESTAMP_TOLERANCE", "30"))


def ensure_socket_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
