"""
风险评分器 — 多维加权风险评估。

独立于 RuleEngine 的快速路径，提供更细粒度的风险量化：
将一次工具调用拆解为 6 个风险维度，加权求和得到 0-100 的综合分，
再映射到 5 级风险等级（Safe/Low/Medium/High/Critical）与安全裁决。

设计原则（参考 Design-2 §4.2.4 安全纵深）：
- 评分纯函数、无副作用、不依赖 LLM，保证确定性与可测试性
- 权重集中声明，便于按 safety_policy 调整
- 与 RuleEngine 互补：RuleEngine 命中硬规则直接拦截；
  未命中硬规则的灰色地带交由本模块量化决策
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from agent.shared.types import SafetyVerdict, ToolRiskLevel


@dataclass
class RiskProfile:
    """6 维风险画像，每维取值 0-100。"""
    intent_risk: float = 0.0        # 意图风险（操作的破坏性意图）
    command_risk: float = 0.0       # 命令风险（命令本身的危险程度）
    path_risk: float = 0.0          # 路径风险（涉及的文件系统位置）
    privilege_risk: float = 0.0     # 权限风险（是否提权/越权）
    exfiltration_risk: float = 0.0  # 数据外传风险
    injection_risk: float = 0.0     # 注入风险


# 各维度权重，总和为 1.0。命令与路径是运维场景最主要的风险来源。
_WEIGHTS = {
    "command_risk": 0.30,
    "path_risk": 0.20,
    "privilege_risk": 0.15,
    "intent_risk": 0.15,
    "exfiltration_risk": 0.10,
    "injection_risk": 0.10,
}

# 风险等级阈值（含上界）。
_THRESHOLDS = [
    (20.0, "safe", SafetyVerdict.ALLOW, "低风险，自动执行"),
    (40.0, "low", SafetyVerdict.ALLOW, "较低风险，执行并记录日志"),
    (60.0, "medium", SafetyVerdict.REQUIRE_CONFIRM, "中等风险，需要人工审批"),
    (80.0, "high", SafetyVerdict.REQUIRE_CONFIRM, "高风险，强烈建议人工复核"),
    (100.01, "critical", SafetyVerdict.BLOCK, "严重风险，默认阻断"),
]


def calculateRiskScore(profile: RiskProfile) -> float:
    """按权重计算综合风险分（0-100）。"""
    score = (
        _WEIGHTS["command_risk"] * profile.command_risk
        + _WEIGHTS["path_risk"] * profile.path_risk
        + _WEIGHTS["privilege_risk"] * profile.privilege_risk
        + _WEIGHTS["intent_risk"] * profile.intent_risk
        + _WEIGHTS["exfiltration_risk"] * profile.exfiltration_risk
        + _WEIGHTS["injection_risk"] * profile.injection_risk
    )
    return round(min(100.0, max(0.0, score)), 2)


def classifyRisk(score: float) -> tuple[str, SafetyVerdict, str]:
    """将分数映射到 (等级名, 安全裁决, 原因描述)。"""
    for upper, level, verdict, reason in _THRESHOLDS:
        if score < upper:
            return level, verdict, f"{reason}（评分 {score}）"
    # 理论不可达（阈值已覆盖到 100.01）
    return "critical", SafetyVerdict.BLOCK, f"评分越界 {score}，默认阻断"


# ── 启发式打分：从工具调用推导各维度分值 ──

_HIGH_RISK_PRIVILEGE = re.compile(
    r"\b(sudo|su|chmod|chown|setcap|visudo)\b", re.IGNORECASE)
_EXFIL = re.compile(
    r"\b(curl|wget|scp|nc|ncat|ftp|rsync)\b", re.IGNORECASE)
_DESTRUCTIVE = re.compile(
    r"\b(rm|mkfs|dd|wipefs|shred|truncate|fdisk|parted)\b", re.IGNORECASE)
_SENSITIVE_PATH = re.compile(
    r"(/etc/(shadow|passwd|sudoers)|/boot|/dev/(sd|nvme|vd)|~?/\.ssh|/root)\b")
_SYSTEM_PATH = re.compile(r"^/(etc|usr|lib|sbin|bin|proc|sys|boot)\b")


def profileFromToolCall(
    toolName: str,
    riskLevel: ToolRiskLevel,
    arguments: dict,
    injectionDetected: bool = False,
) -> RiskProfile:
    """从工具调用上下文构造 RiskProfile（启发式，确定性）。

    Args:
        toolName: 工具名
        riskLevel: 工具静态风险等级
        arguments: 调用参数
        injectionDetected: 上游注入检测结果
    """
    # 聚合所有字符串参数，便于模式扫描
    blob = " ".join(
        str(v) for v in arguments.values()
        if isinstance(v, (str, int, float))
    )

    profile = RiskProfile()

    # intent_risk：由静态风险等级决定基线
    if riskLevel == ToolRiskLevel.DANGEROUS:
        profile.intent_risk = 80.0
    elif riskLevel == ToolRiskLevel.WRITE:
        profile.intent_risk = 40.0
    else:
        profile.intent_risk = 5.0

    # command_risk：破坏性命令关键字
    if _DESTRUCTIVE.search(blob):
        profile.command_risk = 85.0
    elif riskLevel == ToolRiskLevel.DANGEROUS:
        profile.command_risk = 60.0
    elif riskLevel == ToolRiskLevel.WRITE:
        profile.command_risk = 35.0
    else:
        profile.command_risk = 5.0

    # path_risk：敏感/系统路径
    if _SENSITIVE_PATH.search(blob):
        profile.path_risk = 90.0
    elif _SYSTEM_PATH.search(blob):
        profile.path_risk = 65.0
    elif ".." in blob:
        profile.path_risk = 50.0
    else:
        profile.path_risk = 10.0

    # privilege_risk：提权关键字
    profile.privilege_risk = 75.0 if _HIGH_RISK_PRIVILEGE.search(blob) else 10.0

    # exfiltration_risk：外传工具 + 管道
    if _EXFIL.search(blob):
        profile.exfiltration_risk = 70.0 if "|" in blob else 45.0
    else:
        profile.exfiltration_risk = 5.0

    # injection_risk：上游检测结果
    profile.injection_risk = 100.0 if injectionDetected else 0.0

    return profile


def scoreToolCall(
    toolName: str,
    riskLevel: ToolRiskLevel,
    arguments: dict,
    injectionDetected: bool = False,
) -> tuple[float, str, SafetyVerdict, str]:
    """一站式：工具调用 -> (分数, 等级, 裁决, 原因)。"""
    profile = profileFromToolCall(
        toolName, riskLevel, arguments, injectionDetected)
    score = calculateRiskScore(profile)
    level, verdict, reason = classifyRisk(score)
    return score, level, verdict, reason
