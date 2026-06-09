"""
分层 Prompt 组装器。

4层结构（KV Cache 优化）：
  L1 静态前缀 — System Prompt + Tool Definitions + Safety Rules
  L2 半静态层 — Policy Profile + Skills
  L3 会话上下文 — OS Snapshot + 对话历史
  L4 当前请求 — 用户消息 + 本轮证据

关键规则：
- Tool Definitions 按 name 字母序排列 → 前缀稳定
- System Prompt 不含动态变量（时间戳、session_id）→ 前缀可缓存
- 当前时间放 L4
"""
from __future__ import annotations
import json
from agent.shared.serialization import canonical_json


class PromptBuilder:
    """分层 Prompt 组装器。"""

    def __init__(self, systemPrompt: str, safetyRules: str,
                 toolSchemas: list[dict]):
        self._systemPrompt = systemPrompt
        self._safetyRules = safetyRules
        # 字母序排列保证前缀稳定
        self._toolSchemas = sorted(toolSchemas,
                                   key=lambda s: s.get("function", {}).get("name", ""))

    def build(self, userMessage: str,
              systemInfo: dict | None = None,
              conversationHistory: list[dict] | None = None,
              policyProfile: dict | None = None) -> list[dict]:
        """组装 OpenAImessages 列表。

        Returns:
            [{"role": "system", "content": ...}, ...]
        """
        messages: list[dict] = []

        # ── L1: 静态前缀 ──
        content = self._systemPrompt
        content += "\n\n## 可用工具\n\n"
        content += self._formatToolDefinitions()
        content += f"\n\n## 安全规则\n\n{self._safetyRules}"
        messages.append({"role": "system", "content": content})

        # ── L2: 半静态策略 ──
        if policyProfile:
            messages.append({
                "role": "system",
                "content": f"## 当前策略\n{canonical_json(policyProfile)}"
            })

        # ── L3: 会话上下文 ──
        if systemInfo:
            messages.append({
                "role": "system",
                "content": f"## 当前系统信息\n{canonical_json(systemInfo)}"
            })
        if conversationHistory:
            messages.extend(conversationHistory)

        # ── L4: 当前请求 ──
        messages.append({"role": "user", "content": userMessage})

        return messages

    def _formatToolDefinitions(self) -> str:
        """格式化工具定义块（字母序，prefix-stable）。"""
        lines = []
        for schema in self._toolSchemas:
            fn = schema.get("function", {})
            name = fn.get("name", "?")
            desc = fn.get("description", "")
            params = fn.get("parameters", {})
            lines.append(f"### {name}")
            lines.append(f"  {desc}")
            lines.append(f"  Parameters: {canonical_json(params)}")
            lines.append("")
        return "\n".join(lines)
