"""序列化工具。"""

import json


def canonical_json(obj) -> str:
    """确定性 JSON 序列化：键排序、紧凑格式。"""
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def safe_truncate(text: str, max_chars: int = 4000) -> tuple[str, bool]:
    """截断文本，保留首尾。返回 (截断后文本, 是否被截断)。"""
    if len(text) <= max_chars:
        return text, False
    half = max_chars // 2 - 20
    skipped = len(text) - max_chars
    truncated = (
        text[:half]
        + f"\n... [截断 {skipped} 字符] ...\n"
        + text[-half:]
    )
    return truncated, True
