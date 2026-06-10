"""
分层 Prompt 组装器（KV-Cache 优化版）。

编排顺序（从前往后）：
  model → tools → L1 系统提示词 + 安全规则 → L2 策略 → 对话历史 → 当前用户消息

不再内嵌工具定义文本（由 API 的 tools 参数传递）。
不再注入系统快照（agent 按需调用工具获取）。
"""
from __future__ import annotations
from agent.shared.serialization import canonical_json


class PromptBuilder:
    """分层 Prompt 组装器。"""

    def __init__(self, systemPrompt: str, safetyRules: str):
        self._systemPrompt = systemPrompt
        self._safetyRules = safetyRules

    def build(self, userMessage: str,
              conversationHistory: list[dict] | None = None,
              policyProfile: dict | None = None) -> list[dict]:
        """组装 OpenAI messages 列表。

        Returns:
            [{"role": "system", "content": ...}, ...]
        """
        messages: list[dict] = []

        # ── L1: 静态前缀（不包含工具文本，由 API tools 参数传递）──
        content = self._systemPrompt
        content += f"\n\n## 安全规则\n\n{self._safetyRules}"
        messages.append({"role": "system", "content": content})

        # ── L2: 半静态策略 ──
        if policyProfile:
            messages.append({
                "role": "system",
                "content": f"## 当前策略\n{canonical_json(policyProfile)}"
            })

        # ── L3: 会话上下文（对话历史 + 当前用户消息）──
        if conversationHistory:
            messages.extend(conversationHistory)
        messages.append({"role": "user", "content": userMessage})

        return messages
