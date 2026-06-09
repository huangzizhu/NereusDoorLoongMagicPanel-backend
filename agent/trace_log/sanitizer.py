"""敏感信息脱敏。"""
from __future__ import annotations
import re

_SENSITIVE_PATTERNS = [
    (re.compile(r"(api_key|apikey|secret|token|password|passwd)\s*[:=]\s*\S+", re.IGNORECASE),
     lambda m: m.group(0).split(":")[0] + ": ***REDACTED***"),
]

_SENSITIVE_KEYS = {"api_key", "apikey", "secret", "token", "password", "passwd"}


def sanitize(data: dict) -> dict:
    """深度脱敏字典中的敏感字段。"""
    result = {}
    for k, v in data.items():
        if k.lower() in _SENSITIVE_KEYS:
            result[k] = "***REDACTED***"
        elif isinstance(v, dict):
            result[k] = sanitize(v)
        elif isinstance(v, str):
            result[k] = _redactString(v)
        else:
            result[k] = v
    return result


def _redactString(s: str) -> str:
    for pat, replacer in _SENSITIVE_PATTERNS:
        s = pat.sub(replacer, s)
    return s
