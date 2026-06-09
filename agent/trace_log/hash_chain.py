"""SHA-256 哈希链 — 防篡改审计。"""
from __future__ import annotations
import hashlib
import json


class HashChain:
    """SHA-256 哈希链。

    H₀ = SHA256(entry₀)
    Hₙ = SHA256(Hₙ₋₁ || entryₙ)
    """

    def __init__(self):
        self._prevHash: str | None = None

    def hash(self, entry: dict) -> str:
        """计算本条记录的哈希，更新链条。"""
        canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        if self._prevHash:
            canonical = self._prevHash + "||" + canonical
        h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        self._prevHash = h
        return h

    def reset(self) -> None:
        self._prevHash = None

    @property
    def prevHash(self) -> str | None:
        return self._prevHash
