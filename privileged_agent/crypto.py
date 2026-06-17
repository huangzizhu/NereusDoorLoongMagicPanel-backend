"""Ed25519 非对称密码学模块

为特权模型 V2 提供签名与验签能力。

密钥对生成:
    python -m privileged_agent.crypto generate --priv /etc/nereus/ed25519_priv.pem --pub /etc/nereus/ed25519_pub.pem

策略引擎（后端）持有私钥 → 签名请求。
特权代理（root）   持有公钥 → 验签请求。
"""

import base64
import json
from dataclasses import dataclass
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


@dataclass
class KeyPair:
    priv: ed25519.Ed25519PrivateKey
    pub: ed25519.Ed25519PublicKey


def generate_keypair() -> KeyPair:
    """生成 Ed25519 密钥对。"""
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    return KeyPair(priv=priv, pub=pub)


def load_private_key_pem(pem_bytes: bytes) -> ed25519.Ed25519PrivateKey:
    """从 PEM 字节加载 Ed25519 私钥。"""
    return serialization.load_pem_private_key(pem_bytes, password=None)


def load_public_key_pem(pem_bytes: bytes) -> ed25519.Ed25519PublicKey:
    """从 PEM 字节加载 Ed25519 公钥。"""
    key = serialization.load_pem_public_key(pem_bytes)
    if not isinstance(key, ed25519.Ed25519PublicKey):
        raise TypeError(f"expected Ed25519PublicKey, got {type(key).__name__}")
    return key


def dump_private_key_pem(priv: ed25519.Ed25519PrivateKey) -> bytes:
    """将 Ed25519 私钥导出为 PEM 字节。"""
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def dump_public_key_pem(pub: ed25519.Ed25519PublicKey) -> bytes:
    """将 Ed25519 公钥导出为 PEM 字节。"""
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


# ── 高层签名/验签 API ──


def sign(payload: dict, priv: ed25519.Ed25519PrivateKey) -> str:
    """对 dict payload 签名，返回 base64 签名字符串。

    签名内容 = canonical_json(payload)
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = priv.sign(canonical)
    return base64.b64encode(sig).decode("ascii")


def verify(payload: dict, signature_b64: str, pub: ed25519.Ed25519PublicKey) -> bool:
    """验证 dict payload 的 base64 签名。

    Returns:
        True 验签通过
        False 验签失败
    """
    try:
        sig = base64.b64decode(signature_b64)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        pub.verify(sig, canonical)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


# ── Hash 工具 ──


def hash_payload(payload: dict) -> str:
    """对 dict 做 SHA256，返回 hex 字符串。

    用于计算 args_hash 绑定 token。
    """
    import hashlib

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ── CLI 入口：生成密钥对 ──


def _cli_generate(args: list[str]) -> None:
    import sys

    priv_path: Optional[str] = None
    pub_path: Optional[str] = None

    i = 0
    while i < len(args):
        if args[i] == "--priv" and i + 1 < len(args):
            priv_path = args[i + 1]
            i += 2
        elif args[i] == "--pub" and i + 1 < len(args):
            pub_path = args[i + 1]
            i += 2
        else:
            i += 1

    kp = generate_keypair()

    priv_pem = dump_private_key_pem(kp.priv)
    pub_pem = dump_public_key_pem(kp.pub)

    if priv_path:
        with open(priv_path, "wb") as f:
            f.write(priv_pem)
        print(f"私钥已写入: {priv_path}")
    else:
        print("=== 私钥 (PRIVATE — 后端持有) ===")
        print(priv_pem.decode())

    if pub_path:
        with open(pub_path, "wb") as f:
            f.write(pub_pem)
        print(f"公钥已写入: {pub_path}")
    else:
        print("\n=== 公钥 (PUBLIC — 特权代理持有) ===")
        print(pub_pem.decode())

    print("\n✅ 密钥对生成完毕。")


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m privileged_agent.crypto generate [--priv <path>] [--pub <path>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "generate":
        _cli_generate(sys.argv[2:])
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
