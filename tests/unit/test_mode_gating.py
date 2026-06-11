"""
Phase 1: Agent 模式执行层门控 — 单元测试。

覆盖四种模式 × 三种风险等级的核心组合，验证硬规则门控正确生效。
"""
import unittest

from agent.safety.rule_engine import RuleEngine
from agent.shared.types import ToolRiskLevel, SafetyVerdict
from agent.agent_router.router import AgentMode, AgentRouter


class TestModeGating(unittest.TestCase):
    """测试 RuleEngine 的模式门控逻辑（优先级最高的检查项）。"""

    def setUp(self):
        self.engine = RuleEngine()

    # ── READ_ONLY 模式 ──

    def test_read_only_mode_allows_readonly_tool(self):
        """READ_ONLY 模式下，只读工具应被 ALLOW。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "readFile", ToolRiskLevel.READ_ONLY, {},
            mode=AgentMode.READ_ONLY,
        )
        self.assertEqual(verdict, SafetyVerdict.ALLOW, reason)

    def test_read_only_mode_blocks_write_tool(self):
        """READ_ONLY 模式下，写入工具应被 BLOCK。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "writeFile", ToolRiskLevel.WRITE, {"path": "/tmp/test.txt"},
            mode=AgentMode.READ_ONLY,
        )
        self.assertEqual(verdict, SafetyVerdict.BLOCK, reason)
        self.assertIn("read_only", reason.lower())

    def test_read_only_mode_blocks_dangerous_tool(self):
        """READ_ONLY 模式下，高危工具应被 BLOCK。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "deleteFile", ToolRiskLevel.DANGEROUS, {"path": "/tmp/x"},
            mode=AgentMode.READ_ONLY,
        )
        self.assertEqual(verdict, SafetyVerdict.BLOCK, reason)
        self.assertIn("read_only", reason.lower())

    # ── PLAN 模式 ──

    def test_plan_mode_allows_readonly_tool(self):
        """PLAN 模式下，只读工具应被 ALLOW。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "searchText", ToolRiskLevel.READ_ONLY, {"pattern": "test"},
            mode=AgentMode.PLAN,
        )
        self.assertEqual(verdict, SafetyVerdict.ALLOW, reason)

    def test_plan_mode_blocks_write_tool(self):
        """PLAN 模式下，写入工具应被 BLOCK。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "writeFile", ToolRiskLevel.WRITE, {"path": "/tmp/test.txt"},
            mode=AgentMode.PLAN,
        )
        self.assertEqual(verdict, SafetyVerdict.BLOCK, reason)
        self.assertIn("plan", reason.lower())

    def test_plan_mode_blocks_dangerous_tool(self):
        """PLAN 模式下，高危工具应被 BLOCK。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "deletePath", ToolRiskLevel.DANGEROUS, {"path": "/tmp/x"},
            mode=AgentMode.PLAN,
        )
        self.assertEqual(verdict, SafetyVerdict.BLOCK, reason)
        self.assertIn("plan", reason.lower())

    # ── AGENT 模式（向后兼容，行为不变）──

    def test_agent_mode_passes_readonly_tool(self):
        """AGENT 模式下，只读工具通过模式门控（走后续规则）。"""
        verdict, _ = self.engine.checkToolCallWithReason(
            "readFile", ToolRiskLevel.READ_ONLY, {},
            mode=AgentMode.AGENT,
        )
        self.assertNotEqual(verdict, SafetyVerdict.BLOCK)

    def test_agent_mode_passes_write_tool(self):
        """AGENT 模式下，写入工具通过模式门控（走后续规则）。"""
        verdict, _ = self.engine.checkToolCallWithReason(
            "writeFile", ToolRiskLevel.WRITE, {"path": "/tmp/ok.txt"},
            mode=AgentMode.AGENT,
        )
        self.assertNotEqual(verdict, SafetyVerdict.BLOCK)

    def test_agent_mode_passes_dangerous_tool(self):
        """AGENT 模式下，高危工具通过模式门控（后续变为 REQUIRE_CONFIRM）。"""
        verdict, _ = self.engine.checkToolCallWithReason(
            "deleteFile", ToolRiskLevel.DANGEROUS, {"path": "/tmp/ok.txt"},
            mode=AgentMode.AGENT,
        )
        self.assertNotEqual(verdict, SafetyVerdict.BLOCK)

    # ── BREAK_GLASS 模式 ──

    def test_break_glass_allows_dangerous_tool(self):
        """BREAK_GLASS 模式下，高危工具直接 ALLOW，不需要审批。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "deleteFile", ToolRiskLevel.DANGEROUS, {"path": "/etc/any"},
            mode=AgentMode.BREAK_GLASS,
        )
        self.assertEqual(verdict, SafetyVerdict.ALLOW, reason)
        self.assertIn("紧急模式", reason)

    def test_break_glass_allows_write_tool(self):
        """BREAK_GLASS 模式下，写入工具直接 ALLOW。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "writeFile", ToolRiskLevel.WRITE, {"path": "/etc/config"},
            mode=AgentMode.BREAK_GLASS,
        )
        self.assertEqual(verdict, SafetyVerdict.ALLOW, reason)
        self.assertIn("紧急模式", reason)

    def test_break_glass_skips_dangerous_pattern_check(self):
        """BREAK_GLASS 模式下，即使参数匹配高危模式也直接放行。"""
        verdict, reason = self.engine.checkToolCallWithReason(
            "runCommand", ToolRiskLevel.DANGEROUS,
            {"command": "rm -rf /"},
            mode=AgentMode.BREAK_GLASS,
        )
        self.assertEqual(verdict, SafetyVerdict.ALLOW, reason)
        self.assertIn("紧急模式", reason)

    # ── 向后兼容：不传 mode 时默认 AGENT ──

    def test_default_mode_is_agent(self):
        """不传 mode 时，默认 AGENT 模式，行为不变。"""
        verdict, _ = self.engine.checkToolCallWithReason(
            "readFile", ToolRiskLevel.READ_ONLY, {},
        )
        self.assertNotEqual(verdict, SafetyVerdict.BLOCK)

    def test_default_mode_via_check_tool_call(self):
        """checkToolCall（单返回裁决）也应默认 AGENT。"""
        verdict = self.engine.checkToolCall(
            "readFile", ToolRiskLevel.READ_ONLY, {},
        )
        self.assertNotEqual(verdict, SafetyVerdict.BLOCK)

    # ── 模式门控优先级高于参数规则 ──

    def test_mode_gate_takes_priority_over_argument_rules(self):
        """模式门控在参数规则之前执行：PLAN 模式阻断写入工具，不检查参数。"""
        # 即使参数完全安全，PLAN 模式也阻断写入
        verdict, reason = self.engine.checkToolCallWithReason(
            "writeFile", ToolRiskLevel.WRITE, {"path": "/tmp/safe.txt"},
            mode=AgentMode.PLAN,
        )
        self.assertEqual(verdict, SafetyVerdict.BLOCK, reason)
        # 原因应来自模式门控，而非参数规则
        self.assertIn("plan", reason.lower())

    def test_read_only_mode_still_checks_arguments_for_readonly_tools(self):
        """READ_ONLY 模式下，只读工具的参数仍受高危规则保护。"""
        # READ_ONLY 工具通过模式门控，但参数触发高危规则
        verdict, reason = self.engine.checkToolCallWithReason(
            "runCommand", ToolRiskLevel.READ_ONLY,
            {"command": "rm -rf /"},
            mode=AgentMode.READ_ONLY,
        )
        # 先通过模式门控，但参数触发高危规则 → REQUIRE_CONFIRM
        self.assertEqual(verdict, SafetyVerdict.REQUIRE_CONFIRM, reason)


# ── filterToolsByMode 测试 ──────────────────────────────────────────

class TestFilterToolsByMode(unittest.TestCase):
    """测试 AgentRouter.filterToolsByMode 工具列表过滤。"""

    def setUp(self):
        # 模拟 registry.listTools() 的输出
        self._all_tools = [
            {"function": {"name": "readFile", "description": "Read a file"}},
            {"function": {"name": "searchText", "description": "Search text"}},
            {"function": {"name": "listFiles", "description": "List files"}},
            {"function": {"name": "writeFile", "description": "Write a file"}},
            {"function": {"name": "createDirectory", "description": "Create dir"}},
            {"function": {"name": "deletePath", "description": "Delete path"}},
            {"function": {"name": "runCommand", "description": "Run command"}},
        ]

        # 模拟 registry.getRiskLevel
        self._risk_levels = {
            "readFile": ToolRiskLevel.READ_ONLY,
            "searchText": ToolRiskLevel.READ_ONLY,
            "listFiles": ToolRiskLevel.READ_ONLY,
            "writeFile": ToolRiskLevel.WRITE,
            "createDirectory": ToolRiskLevel.WRITE,
            "deletePath": ToolRiskLevel.DANGEROUS,
            "runCommand": ToolRiskLevel.DANGEROUS,
        }

    def _getRiskLevel(self, name: str) -> ToolRiskLevel:
        return self._risk_levels.get(name, ToolRiskLevel.WRITE)

    def _filtered_names(self, mode: AgentMode) -> list[str]:
        result = AgentRouter.filterToolsByMode(
            mode, self._all_tools, self._getRiskLevel,
        )
        return [t["function"]["name"] for t in result]

    def test_read_only_mode_only_readonly_tools(self):
        """READ_ONLY 模式只返回只读工具。"""
        names = self._filtered_names(AgentMode.READ_ONLY)
        self.assertEqual(set(names), {"readFile", "searchText", "listFiles"})

    def test_plan_mode_only_readonly_tools(self):
        """PLAN 模式只返回只读工具。"""
        names = self._filtered_names(AgentMode.PLAN)
        self.assertEqual(set(names), {"readFile", "searchText", "listFiles"})

    def test_agent_mode_all_tools(self):
        """AGENT 模式返回全部工具。"""
        names = self._filtered_names(AgentMode.AGENT)
        self.assertEqual(len(names), len(self._all_tools))

    def test_break_glass_mode_all_tools(self):
        """BREAK_GLASS 模式返回全部工具。"""
        names = self._filtered_names(AgentMode.BREAK_GLASS)
        self.assertEqual(len(names), len(self._all_tools))

    def test_read_only_excludes_write_tools(self):
        """READ_ONLY 模式不包含写入工具。"""
        names = self._filtered_names(AgentMode.READ_ONLY)
        self.assertNotIn("writeFile", names)
        self.assertNotIn("createDirectory", names)

    def test_read_only_excludes_dangerous_tools(self):
        """READ_ONLY 模式不包含高危工具。"""
        names = self._filtered_names(AgentMode.READ_ONLY)
        self.assertNotIn("deletePath", names)
        self.assertNotIn("runCommand", names)

    def test_filter_preserves_schema_structure(self):
        """过滤保留完整的 schema 结构（不仅仅是 name）。"""
        result = AgentRouter.filterToolsByMode(
            AgentMode.READ_ONLY, self._all_tools, self._getRiskLevel,
        )
        for t in result:
            self.assertIn("function", t)
            self.assertIn("name", t["function"])
            self.assertIn("description", t["function"])

    def test_empty_tools_list(self):
        """空工具列表应返回空列表。"""
        result = AgentRouter.filterToolsByMode(
            AgentMode.READ_ONLY, [], self._getRiskLevel,
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
