from __future__ import annotations

import internal_rpc.config as rpc_config


def test_backend_rpc_config_loads_dotenv_before_runtime_default(tmp_path, monkeypatch):
    monkeypatch.setattr(rpc_config, "_DOTENV_LOADED", False)
    monkeypatch.setattr(rpc_config, "getProjectRootPath", lambda: tmp_path)
    monkeypatch.delenv("NDLM_BACKEND_RPC_PRIVKEY", raising=False)
    monkeypatch.delenv("NDLM_BACKEND_RPC_PUBKEY", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "NDLM_BACKEND_RPC_PRIVKEY=/etc/nereus/backend_rpc_ed25519_priv.pem",
                "NDLM_BACKEND_RPC_PUBKEY=/etc/nereus/backend_rpc_ed25519_pub.pem",
            ]
        ),
        encoding="utf-8",
    )

    assert rpc_config.backend_rpc_private_key_path() == "/etc/nereus/backend_rpc_ed25519_priv.pem"
    assert rpc_config.backend_rpc_public_key_path() == "/etc/nereus/backend_rpc_ed25519_pub.pem"


def test_backend_rpc_config_env_overrides_dotenv(tmp_path, monkeypatch):
    monkeypatch.setattr(rpc_config, "_DOTENV_LOADED", False)
    monkeypatch.setattr(rpc_config, "getProjectRootPath", lambda: tmp_path)
    monkeypatch.setenv("NDLM_BACKEND_RPC_PRIVKEY", "/custom/private.pem")
    (tmp_path / ".env").write_text(
        "NDLM_BACKEND_RPC_PRIVKEY=/etc/nereus/backend_rpc_ed25519_priv.pem\n",
        encoding="utf-8",
    )

    assert rpc_config.backend_rpc_private_key_path() == "/custom/private.pem"
