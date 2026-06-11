"""
Plan 数据结构 — 两阶段 Plan 模式的结构化计划定义。

PLAN 模式下 LLM 通过 submitPlan tool call 提交计划，
参数直接映射为本模块的 dataclass，无需文本解析。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PlanStep:
    """计划中的单个执行步骤。"""
    step_id: str                  # 唯一标识，如 "step-1"
    title: str                    # 简短标题，如 "修改 Nginx 配置"
    action: str                   # 具体操作描述
    tool: str | None = None       # 预期使用的工具名，如 "edit_file"
    target: str | None = None     # 目标文件或路径
    risk: str = "medium"          # "low" / "medium" / "high"


@dataclass
class AgentPlan:
    """完整的执行计划。"""
    summary: str                                      # 计划概述
    steps: list[PlanStep]                             # 执行步骤列表
    risks: list[str] = field(default_factory=list)    # 整体风险说明
    files: list[str] = field(default_factory=list)    # 涉及的文件路径列表


def planFromSubmitArgs(args: dict) -> AgentPlan:
    """从 submitPlan 工具调用的参数字典构造 AgentPlan。

    Args:
        args: submitPlan 的原始参数 dict，包含
            summary, steps, risks, files

    Returns:
        解析后的 AgentPlan 对象

    Raises:
        ValueError: 参数格式不合法
    """
    summary = str(args.get("summary", "")).strip()
    if not summary:
        raise ValueError("plan.summary 不能为空")

    raw_steps = args.get("steps", [])
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError("plan.steps 不能为空")

    steps = []
    for i, s in enumerate(raw_steps):
        if not isinstance(s, dict):
            raise ValueError(f"plan.steps[{i}] 必须是 dict")
        step_id = str(s.get("step_id", f"step-{i + 1}"))
        title = str(s.get("title", "")).strip()
        if not title:
            raise ValueError(f"plan.steps[{i}].title 不能为空")
        steps.append(PlanStep(
            step_id=step_id,
            title=title,
            action=str(s.get("action", "")),
            tool=str(s.get("tool")) if s.get("tool") else None,
            target=str(s.get("target")) if s.get("target") else None,
            risk=str(s.get("risk", "medium")),
        ))

    risks = [str(r) for r in (args.get("risks") or []) if r]
    files = [str(f) for f in (args.get("files") or []) if f]

    return AgentPlan(summary=summary, steps=steps, risks=risks, files=files)


def planToDict(plan: AgentPlan) -> dict[str, Any]:
    """将 AgentPlan 序列化为 dict（用于事件推送）。"""
    return asdict(plan)


def formatPlanForPrompt(plan: AgentPlan) -> str:
    """将已批准的 Plan 格式化为助记文本，注入第二阶段 system prompt。

    Args:
        plan: 已批准的 AgentPlan

    Returns:
        格式化的计划文本
    """
    lines = [f"## 已批准的执行计划\n"]
    lines.append(f"概述: {plan.summary}")
    if plan.files:
        lines.append(f"涉及文件: {', '.join(plan.files)}")
    if plan.risks:
        lines.append(f"风险: {'; '.join(plan.risks)}")
    lines.append("")
    lines.append("执行步骤:")
    for step in plan.steps:
        tags = []
        if step.tool:
            tags.append(f"工具={step.tool}")
        if step.target:
            tags.append(f"目标={step.target}")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  [{step.step_id}] {step.title}{tag_str}")
        lines.append(f"      {step.action}")
    lines.append("")
    lines.append("请严格按照以上计划逐步执行。不要跳过任何步骤。")
    return "\n".join(lines)
