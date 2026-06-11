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

from agent.shared.types import ToolRiskLevel


class AgentMode(str, Enum):
    READ_ONLY = "read_only"
    PLAN = "plan"
    AGENT = "agent"
    BREAK_GLASS = "break_glass"
    EXECUTING = "executing"


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

### ⚠ 强制规则
**严禁在回复中以文本形式向用户提问。** 如果你需要用户提供信息或做出选择，必须调用 ask_choice 工具。文本提问会导致前端无法结构化展示，系统会视为违规。

### 核心流程
1. 先使用只读工具分析系统状态（诊断、查询、搜索等）
2. **必须**使用 ask_choice 工具向用户提问，澄清需求和关键细节
3. 根据用户的回答，发现矛盾或模糊点→继续追问
4. 当信息足够时，调用 submitPlan 提交结构化计划

### 提问要求
- 每个 ask_choice 调用只能问**一个问题**，但可以提供 2-6 个选项
- 选项使用 `id`（字母 A/B/C...）+ `title`（展示文本）+ `summary`（可选说明）结构
- 对需要探索的开放性问题，开启 allow_custom=true 让用户自由输入
- 对选择题（A/B/C），关闭 allow_custom（仅限选项内选择）
- 一次只聚焦一个决策维度，不要在一个问题中混入多个主题

### 发现矛盾
如果用户的新回答与你之前收集的信息矛盾，不要忽略——追问澄清：
- "您之前提到 X，现在又说 Y，请问哪一项是您的真实意图？"
- 或者将矛盾点作为选项提供给用户确认

### 何时提交计划
当你对以下问题都有明确答案后，再调用 submitPlan：
- 用户想要什么（目标）
- 优先级（哪些先做、哪些可以延后）
- 边界条件（不要动什么、避开什么）
- 确认了关键假设

### 提交计划
调用 submitPlan 提交结构化执行计划。
参数：
- summary: 计划概述（一句话）
- steps: 执行步骤列表，每步包含 step_id, title, action, tool(可选), target(可选), risk
- risks: 整体风险说明列表
- files: 涉及的所有文件路径列表
""",
    AgentMode.AGENT: """
## 当前模式：Agent 执行模式

行为规则：
1. 低风险操作（只读查询）自动执行
2. 中风险操作（文件写入、服务管理）需用户审批
3. 高风险操作（删除、kill、防火墙变更）必须经过审批
4. 执行前简要说明操作内容和原因

### ⚠ 工具调用规则
调用 write 或 dangerous 等级的工具时，**必须在参数中填写 `reason` 字段**，说明你为什么调用此工具、要做什么。这用于审批弹窗向用户展示你的意图，帮助用户快速判断是否放行。
""",
    AgentMode.BREAK_GLASS: """
## 当前模式：紧急模式 (BreakGlass)

⚠ 注意：当前为紧急模式，审批流程已降级。所有操作将被记录到审计日志。

行为规则：
1. 所有操作记录到审计日志（不可篡改的哈希链）
2. 优先完成用户指令，安全校验降级为警告而非阻断
3. 必须在回复开头标明 [紧急模式]
""",
    AgentMode.EXECUTING: """
## 当前模式：执行模式 (Executing)

行为规则：
1. 你正在执行一个已批准的计划
2. 严格按照计划的步骤顺序执行，不要跳过或修改步骤
3. 低风险操作自动执行，中高风险操作需用户审批
4. 如果某步骤失败，说明原因并询问用户下一步
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
        """根据模式过滤 LLM 可见的工具 schema 列表。

        READ_ONLY / PLAN — 只暴露只读工具，让 LLM 根本看不见写入/高危工具
        AGENT / BREAK_GLASS — 暴露全部工具

        Args:
            mode: 当前 Agent 运行模式
            toolSchemas: 从 registry.listTools() 获取的完整工具 schema 列表
                （OpenAI function-calling 格式，每条含 {"function": {"name": ...}}）
            getRiskLevel: 根据工具名获取风险等级的回调函数
                （通常是 registry.getRiskLevel）

        Returns:
            过滤后的工具 schema 列表
        """
        allowed_levels = AgentRouter.getAllowedRiskLevels(mode)
        # 全部放行 → 跳过遍历
        if len(allowed_levels) == 3:
            return toolSchemas
        return [
            t for t in toolSchemas
            if getRiskLevel(t["function"]["name"]) in allowed_levels
        ]


def getModePrompt(mode: AgentMode | str) -> str:
    """便捷函数：根据模式字符串获取对应的 Prompt 文本。"""
    if isinstance(mode, AgentMode):
        return _MODE_PROMPTS[mode]
    try:
        return _MODE_PROMPTS[AgentMode(mode)]
    except ValueError:
        return _MODE_PROMPTS[AgentMode.AGENT]
