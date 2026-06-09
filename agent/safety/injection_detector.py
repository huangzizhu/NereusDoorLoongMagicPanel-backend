"""
Prompt Injection 检测器。

基于正则模式匹配，不依赖 LLM。
"""
from __future__ import annotations
import re

_INJECTION_PATTERNS = [
    # 英文
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"forget\s+everything", re.IGNORECASE),
    # 中文
    re.compile(r"忽略(之前|上面|以上).{0,4}(指令|规则|提示|约束)"),
    re.compile(r"你现在是[一一个]"),
    re.compile(r"新的指令\s*[：:]"),
    re.compile(r"关闭安全(检查|校验|护栏)"),
    re.compile(r"不要(记录|写)日志"),
    re.compile(r"假装你是"),
    re.compile(r"作为\s*root"),
]

def checkPromptInjection(text: str) -> bool:
    """检测用户输入是否包含 Prompt Injection。

    Returns:
        True = 检测到注入风险
    """
    for pat in _INJECTION_PATTERNS:
        if pat.search(text):
            return True
    return False
