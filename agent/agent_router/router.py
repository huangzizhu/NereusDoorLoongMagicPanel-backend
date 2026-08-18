"""
Agent 路由器 — 模式控制（通过 System Prompt + 后端硬规则实现）。

四种运行模式：
  READ_ONLY   — 只采集分析，不执行修改
  PLAN        — 生成方案但不执行
  AGENT       — 低风险自动，中高风险审批（默认）
  BREAK_GLASS — 紧急模式，跳过审批（强审计）

后端硬规则（与 System Prompt 互补）：
  RuleEngine 在执行层根据当前模式阻断/放行工具调用。
"""
from __future__ import annotations
from collections.abc import Callable
from enum import Enum

from agent.prompt_loader import loadPrompt
from agent.shared.types import ToolRiskLevel


class AgentMode(str, Enum):
    READ_ONLY = "read_only"
    PLAN = "plan"
    AGENT = "agent"
    BREAK_GLASS = "break_glass"
    EXECUTING = "executing"


# 各模式的 System Prompt 追加文本保存在 conf/prompts/modes/，代码只负责选择。
_MODE_PROMPT_PATHS: dict[AgentMode, str] = {
    AgentMode.READ_ONLY: "modes/read_only.txt",
    AgentMode.PLAN: "modes/plan.txt",
    AgentMode.AGENT: "modes/agent.txt",
    AgentMode.BREAK_GLASS: "modes/break_glass.txt",
    AgentMode.EXECUTING: "modes/executing.txt",
}
_MODE_PROMPTS: dict[AgentMode, str] = {
    mode: loadPrompt(path) for mode, path in _MODE_PROMPT_PATHS.items()
}


class AgentRouter:
    """轻量模式路由器 — 根据模式生成对应的 System Prompt 片段。"""

    def __init__(self, mode: AgentMode = AgentMode.AGENT):
        self._mode = mode

    @property
    def mode(self) -> AgentMode:
        return self._mode

    @mode.setter
    def mode(self, m: AgentMode) -> None:
        self._mode = m

    def getPrompt(self) -> str:
        """返回当前模式的 System Prompt 追加文本。"""
        return _MODE_PROMPTS[self._mode]

    @staticmethod
    def getPromptFor(mode: AgentMode) -> str:
        """静态方法：获取指定模式的 Prompt。"""
        return _MODE_PROMPTS[mode]

    @staticmethod
    def getAllowedRiskLevels(mode: AgentMode) -> set[ToolRiskLevel]:
        """根据模式返回允许执行的工具风险等级集合。

        模式门控规则：
          READ_ONLY / PLAN — 只允许只读工具，写入/高危工具被阻断
          AGENT           — 全部允许（由 RuleEngine 逐级判断是否需审批）
          BREAK_GLASS     — 全部允许（跳过审批，但审计日志照常记录）

        Args:
            mode: 当前 Agent 运行模式

        Returns:
            该模式下允许执行的 ToolRiskLevel 集合
        """
        if mode in (AgentMode.READ_ONLY, AgentMode.PLAN):
            return {ToolRiskLevel.READ_ONLY}
        # AGENT / BREAK_GLASS: 全部放行，审批逻辑由 RuleEngine 处理
        return {ToolRiskLevel.READ_ONLY, ToolRiskLevel.WRITE, ToolRiskLevel.DANGEROUS}

    @staticmethod
    def filterToolsByMode(
        mode: AgentMode,
        toolSchemas: list[dict],
        getRiskLevel: Callable[[str], ToolRiskLevel],
    ) -> list[dict]:
        """返回完整工具 schema 列表 — 不再按模式过滤。

        KV-Cache 优化：所有模式暴露相同工具列表 → tools 参数不变 → 前缀缓存命中。
        模式门控完全下沉到 RuleEngine.checkToolCallWithReason（后端硬规则）。
        """
        return toolSchemas


def getModePrompt(mode: AgentMode | str) -> str:
    """便捷函数：根据模式字符串获取对应的 Prompt 文本。"""
    if isinstance(mode, AgentMode):
        return _MODE_PROMPTS[mode]
    try:
        return _MODE_PROMPTS[AgentMode(mode)]
    except ValueError:
        return _MODE_PROMPTS[AgentMode.AGENT]
