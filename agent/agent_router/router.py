"""
Agent 路由器 — 模式控制（通过 System Prompt 实现）。

四种运行模式：
  READ_ONLY   — 只采集分析，不执行修改
  PLAN        — 生成方案但不执行
  AGENT       — 低风险自动，中高风险审批（默认）
  BREAK_GLASS — 紧急模式，跳过审批（强审计）
"""
from __future__ import annotations
from enum import Enum


class AgentMode(str, Enum):
    READ_ONLY = "read_only"
    PLAN = "plan"
    AGENT = "agent"
    BREAK_GLASS = "break_glass"


# 各模式的 System Prompt 追加文本
_MODE_PROMPTS: dict[AgentMode, str] = {
    AgentMode.READ_ONLY: """
## 当前模式：只读模式 (ReadOnly)

严格约束：
1. 只能使用风险等级为 read_only 的工具
2. 绝对禁止执行任何修改系统状态的操作
3. 如果用户要求执行写操作，拒绝并解释当前为只读模式
4. 可以提供分析和建议，但不能执行
""",
    AgentMode.PLAN: """
## 当前模式：计划模式 (Plan)

严格约束：
1. 可以查询系统状态、执行诊断
2. 生成详细的执行方案，但不要执行任何修改操作
3. 方案应包含：步骤、涉及的命令、风险分析、回滚方案
4. 等待用户明确批准后再进入执行模式
""",
    AgentMode.AGENT: """
## 当前模式：Agent 执行模式

行为规则：
1. 低风险操作（只读查询）自动执行
2. 中风险操作（文件写入、服务管理）需用户审批
3. 高风险操作（删除、kill、防火墙变更）必须经过审批
4. 执行前简要说明操作内容和原因
""",
    AgentMode.BREAK_GLASS: """
## 当前模式：紧急模式 (BreakGlass)

⚠ 注意：当前为紧急模式，审批流程已降级。所有操作将被记录到审计日志。

行为规则：
1. 所有操作记录到审计日志（不可篡改的哈希链）
2. 优先完成用户指令，安全校验降级为警告而非阻断
3. 必须在回复开头标明 [紧急模式]
""",
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


def getModePrompt(mode: AgentMode | str) -> str:
    """便捷函数：根据模式字符串获取对应的 Prompt 文本。"""
    if isinstance(mode, AgentMode):
        return _MODE_PROMPTS[mode]
    try:
        return _MODE_PROMPTS[AgentMode(mode)]
    except ValueError:
        return _MODE_PROMPTS[AgentMode.AGENT]
