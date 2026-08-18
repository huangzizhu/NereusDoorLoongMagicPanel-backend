"""
分层 Prompt 组装器（KV-Cache 优化版）。

编排顺序（从前往后）：
  model → tools → L1 系统提示词 + 安全规则 → L2 策略 → 对话历史 → 当前用户消息

不再内嵌工具定义文本（由 API 的 tools 参数传递）。
不再注入系统快照（agent 按需调用工具获取）。
"""
from __future__ import annotations
from agent.prompt_loader import renderPrompt
from agent.shared.serialization import canonical_json
from agent.safety.canary import CanaryManager


class PromptBuilder:
    """分层 Prompt 组装器。"""

    def __init__(self, systemPrompt: str, safetyRules: str,
                 canary: CanaryManager | None = None,
                 extraKnowledge: str | None = None):
        self._systemPrompt = systemPrompt
        self._safetyRules = safetyRules
        self._canary = canary
        self._extraKnowledge = extraKnowledge

    def build(self, userMessage: str,
              conversationHistory: list[dict] | None = None,
              policyProfile: dict | None = None,
              extraKnowledge: str | None = None) -> list[dict]:
        """组装 OpenAI messages 列表。

        Args:
            userMessage: 当前用户消息
            conversationHistory: 会话历史
            policyProfile: 半静态策略（L2）
            extraKnowledge: 组织记忆摘要（运维经验库）。None 时回退到构造参数，
                保持"摘要按会话固定一次"（KV-Cache 前缀稳定）。

        Returns:
            [{"role": "system", "content": ...}, ...]
        """
        messages: list[dict] = []

        # ── L1: 静态前缀（不包含工具文本，由 API tools 参数传递）──
        content = self._systemPrompt
        content += f"\n\n## 安全规则\n\n{self._safetyRules}"
        # 金丝雀令牌段：部署级固定，仅泄露后轮换 → 不破坏前缀缓存
        if self._canary is not None and self._canary.enabled:
            canaryToken = self._canary.token()
            if canaryToken:
                content += "\n\n" + renderPrompt(
                    "safety/canary.txt", {"TOKEN": canaryToken}
                )
        messages.append({"role": "system", "content": content})

        # ── 组织记忆：运维经验库摘要（L1 之后、L2 策略之前，独立 system 消息层）──
        # 非空才注入；按会话固定一次，跨会话刷新是预期行为（KV-Cache 前缀稳定）
        knowledge = self._extraKnowledge if extraKnowledge is None else extraKnowledge
        if knowledge:
            messages.append({
                "role": "system",
                "content": f"## 运维经验库（组织记忆）\n{knowledge}"
            })

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
