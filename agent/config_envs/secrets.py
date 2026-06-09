"""密钥管理 — 从环境变量读取。"""
import os

def getSecret(key: str, envVar: str | None = None) -> str:
    if envVar is None:
        envVar = f"NDLM_{key.upper()}"
    return os.environ.get(envVar, "")
