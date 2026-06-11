"""
安全规则引擎。

从原 safety_guard.py 迁移，去掉 pydantic 依赖。
四层检查：模式门控 → 高危参数模式 → 策略规则 → 风险等级放行/审批。
"""
from __future__ import annotations
import re
from typing import Any

from agent.safety.policy import SafetyPolicy, loadPolicy
from agent.shared.types import ToolRiskLevel, SafetyVerdict
from agent.agent_router.router import AgentMode, AgentRouter

_DANGEROUS_PATTERNS: list[tuple[re.Pattern, str]] = [
    # ── 路径类 ──
    (re.compile(r"(^|[/\\])\.\.\s*$"), "路径包含 .. 可能导致目录穿越"),
    (re.compile(r"^/$"), "操作根目录 / 极其危险"),
    (re.compile(r"^/(etc|boot|usr|lib|sbin|bin|proc|sys)\b"), "操作系统关键目录"),
    (re.compile(r"^/home$"), "操作 /home 根目录"),
    (re.compile(r"/etc/(shadow|passwd|sudoers|gshadow)\b"), "操作认证/权限关键文件"),
    (re.compile(r"~?/\.ssh\b"), "操作 SSH 密钥目录"),
    # ── 权限类 ──
    (re.compile(r"\b777\b"), "chmod 777 权限过于宽松"),
    (re.compile(r"\b000\b"), "chmod 000 会导致文件不可访问"),
    (re.compile(r"\bchmod\s+-R\s", re.IGNORECASE), "递归修改权限风险高"),
    (re.compile(r"\bchown\s+(-R\s+)?root\b", re.IGNORECASE), "变更属主为 root"),
    # ── 信号/进程类 ──
    (re.compile(r"\b(SIGKILL|9)\b"), "SIGKILL 无法被进程捕获，可能导致数据丢失"),
    # ── 删除/格式化类（命令级，匹配命令字符串任意位置）──
    (re.compile(r"\brm\s+(-\w*[rRfF]\w*\s+)+/(\s|$|\*)"), "rm -rf 作用于根/系统路径"),
    (re.compile(r"\bmkfs\.\w+"), "格式化文件系统"),
    (re.compile(r"\bdd\s+if=\S*\s+of=/dev/(sd|nvme|vd|hd)", re.IGNORECASE),
     "dd 直接写裸磁盘设备"),
    (re.compile(r">\s*/dev/(sd|nvme|vd|hd)\w*"), "重定向覆盖磁盘设备"),
    (re.compile(r"\bwipefs\b"), "擦除文件系统签名"),
    # ── 网络/数据外传类 ──
    (re.compile(r"\b(curl|wget)\b.+\|\s*(ba|z|k)?sh\b", re.IGNORECASE),
     "下载内容直接管道执行（远程代码执行风险）"),
    (re.compile(r"\biptables\s+-F\b", re.IGNORECASE), "清空防火墙规则"),
    (re.compile(r"\bnc\b.+-e\b", re.IGNORECASE), "netcat 反弹 shell 风险"),
    # ── 提权类 ──
    (re.compile(r"\bsudo\s+su\b", re.IGNORECASE), "提权到 root 交互式 shell"),
    (re.compile(r"\bsu\s+-\s*root\b", re.IGNORECASE), "切换到 root 用户"),
    # ── Fork bomb / 任意代码执行 ──
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"), "fork bomb"),
    (re.compile(r"\b(python|perl|ruby|php)\d?\s+-c\b", re.IGNORECASE),
     "解释器 -c 执行任意代码"),
    (re.compile(r"\beval\b", re.IGNORECASE), "eval 执行动态拼接命令"),
    # ── 系统状态类 ──
    (re.compile(r"\b(shutdown|reboot|halt|poweroff)\b", re.IGNORECASE),
     "关机/重启系统"),
    (re.compile(r"\bsystemctl\s+(stop|disable|mask)\b", re.IGNORECASE),
     "停用关键系统服务"),
]

class RuleEngine:
    """安全规则引擎。"""

    def __init__(self, policy: SafetyPolicy | str | None = None):
        self._policy = (
            policy if isinstance(policy, SafetyPolicy) else loadPolicy(policy)
        )
        self._policyPatterns = [
            self._compilePattern(pattern)
            for pattern in self._policy.block_patterns + self._policy.require_approval
            if pattern and pattern != "all_write"
        ]

    def checkToolCall(self, toolName: str, riskLevel: ToolRiskLevel,
                      arguments: dict,
                      mode: AgentMode = AgentMode.AGENT) -> SafetyVerdict:
        """校验工具调用安全性。

        Args:
            toolName: 工具名
            riskLevel: 工具风险等级
            arguments: 工具参数字典
            mode: 当前 Agent 运行模式（默认 AGENT，向后兼容）
        """
        verdict, _ = self.checkToolCallWithReason(toolName, riskLevel, arguments, mode)
        return verdict

    def checkToolCallWithReason(self, toolName: str, riskLevel: ToolRiskLevel,
                                arguments: dict,
                                mode: AgentMode = AgentMode.AGENT) -> tuple[SafetyVerdict, str]:
        """与 checkToolCall 相同，但额外返回原因字符串。

        检查顺序（优先级从高到低）：
          1. 模式门控 — 当前模式是否允许该风险等级的工具
          2. BREAK_GLASS — 紧急模式跳过所有审批
          3. 保护路径检查 — 是否命中 policy.protected_paths
          4. 高危参数模式 — 是否命中 _DANGEROUS_PATTERNS
          5. 安全策略 — 是否命中 policy 中的 block/approval 规则
          6. 风险等级放行 — READ_ONLY 自动放行 / DANGEROUS 需审批
        """
        # ── 1. 模式门控：检查当前模式是否允许该风险等级的工具 ──
        allowed_levels = AgentRouter.getAllowedRiskLevels(mode)
        if riskLevel not in allowed_levels:
            return (
                SafetyVerdict.BLOCK,
                f"当前模式 [{mode.value}] 不允许 {riskLevel.value} 操作"
            )

        # ── 2. BREAK_GLASS：紧急模式跳过所有审批，直接放行 ──
        if mode == AgentMode.BREAK_GLASS:
            return SafetyVerdict.ALLOW, "紧急模式，操作已放行"

        # ── 3~6: 现有安全规则（不变） ──
        values = list(self._flattenValues(arguments))

        for value in values:
            for protectedPath in self._policy.protected_paths:
                if protectedPath and protectedPath in value:
                    return (
                        SafetyVerdict.REQUIRE_CONFIRM,
                        f"参数触发安全策略: 访问受保护路径 {protectedPath}",
                    )

        for value in values:
            for pat, reason in _DANGEROUS_PATTERNS:
                if pat.search(value):
                    return SafetyVerdict.REQUIRE_CONFIRM, f"参数触发安全规则: {reason}"

        for value in values:
            for pat, rawPattern in self._policyPatterns:
                if pat.search(value):
                    return SafetyVerdict.REQUIRE_CONFIRM, f"参数触发安全策略: {rawPattern}"

        if riskLevel == ToolRiskLevel.READ_ONLY:
            return SafetyVerdict.ALLOW, "只读操作，自动放行"

        if (
            "all_write" in self._policy.require_approval
            and riskLevel in {ToolRiskLevel.WRITE, ToolRiskLevel.DANGEROUS}
        ):
            return SafetyVerdict.REQUIRE_CONFIRM, "安全策略要求所有写入/高危操作审批"

        if riskLevel == ToolRiskLevel.DANGEROUS:
            return SafetyVerdict.REQUIRE_CONFIRM, f"高危操作 [{toolName}] 需要人工确认"

        return SafetyVerdict.ALLOW, "校验通过"

    @staticmethod
    def _flattenValues(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, (int, float)):
            return [str(value)]
        if isinstance(value, dict):
            values: list[str] = []
            for key, item in value.items():
                values.extend(RuleEngine._flattenValues(key))
                values.extend(RuleEngine._flattenValues(item))
            return values
        if isinstance(value, (list, tuple)):
            values: list[str] = []
            for item in value:
                values.extend(RuleEngine._flattenValues(item))
            return values
        return []

    @staticmethod
    def _compilePattern(pattern: str) -> tuple[re.Pattern, str]:
        try:
            return re.compile(pattern, re.IGNORECASE), pattern
        except re.error:
            return re.compile(re.escape(pattern), re.IGNORECASE), pattern
