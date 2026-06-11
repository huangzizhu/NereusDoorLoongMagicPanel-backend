"""
Phase 3: 两阶段 Plan 模式 — 单元测试。

覆盖 Plan Schema 解析、Plan 格式化、审批流程。
"""
import unittest

from agent.agent_router.plan_schema import (
    AgentPlan, PlanStep,
    planFromSubmitArgs, planToDict, formatPlanForPrompt,
)
from agent.agent_router.router import AgentMode, AgentRouter
from agent.shared.types import ToolRiskLevel


class TestPlanSchema(unittest.TestCase):
    """测试 Plan Schema 解析与序列化。"""

    def test_plan_from_valid_args(self):
        """正常参数应正确解析为 AgentPlan。"""
        args = {
            "summary": "修改 Nginx 配置",
            "steps": [
                {"step_id": "step-1", "title": "读取配置", "action": "读 nginx.conf",
                 "tool": "readFile", "target": "/etc/nginx/nginx.conf", "risk": "low"},
                {"step_id": "step-2", "title": "修改配置", "action": "修改 worker_processes",
                 "tool": "replaceText", "risk": "medium"},
            ],
            "risks": ["重启 Nginx 会导致短暂断连"],
            "files": ["/etc/nginx/nginx.conf"],
        }
        plan = planFromSubmitArgs(args)
        self.assertEqual(plan.summary, "修改 Nginx 配置")
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].step_id, "step-1")
        self.assertEqual(plan.steps[0].tool, "readFile")
        self.assertEqual(plan.steps[0].target, "/etc/nginx/nginx.conf")
        self.assertEqual(plan.steps[0].risk, "low")
        self.assertEqual(plan.steps[1].step_id, "step-2")
        self.assertEqual(plan.steps[1].tool, "replaceText")
        self.assertIsNone(plan.steps[1].target)
        self.assertEqual(len(plan.risks), 1)
        self.assertEqual(len(plan.files), 1)

    def test_plan_empty_summary(self):
        """空 summary 应抛出 ValueError。"""
        with self.assertRaises(ValueError, msg="plan.summary 不能为空"):
            planFromSubmitArgs({"summary": "", "steps": [{"title": "x"}]})

    def test_plan_empty_steps(self):
        """空 steps 应抛出 ValueError。"""
        with self.assertRaises(ValueError, msg="plan.steps 不能为空"):
            planFromSubmitArgs({"summary": "test", "steps": []})

    def test_plan_missing_step_title(self):
        """步骤缺少 title 应抛出 ValueError。"""
        with self.assertRaises(ValueError):
            planFromSubmitArgs({
                "summary": "test",
                "steps": [{"step_id": "s1", "action": "do something"}],
            })

    def test_plan_minimal_steps(self):
        """步骤只有 title 也应能解析（其他字段可选）。"""
        plan = planFromSubmitArgs({
            "summary": "test",
            "steps": [{"title": "do something"}],
        })
        self.assertEqual(plan.steps[0].title, "do something")
        self.assertIsNone(plan.steps[0].tool)
        self.assertIsNone(plan.steps[0].target)

    def test_plan_to_dict(self):
        """planToDict 应返回可 JSON 序列化的字典。"""
        plan = AgentPlan(
            summary="test",
            steps=[PlanStep(step_id="s1", title="Step 1", action="do it")],
            risks=["risk1"],
            files=["f1.txt"],
        )
        d = planToDict(plan)
        self.assertEqual(d["summary"], "test")
        self.assertEqual(len(d["steps"]), 1)
        self.assertEqual(d["steps"][0]["step_id"], "s1")
        self.assertIn("risk1", d["risks"])

    def test_format_plan_for_prompt(self):
        """formatPlanForPrompt 应生成可读的计划文本。"""
        plan = AgentPlan(
            summary="部署新版本",
            steps=[
                PlanStep(step_id="s1", title="备份", action="备份数据库",
                         tool="runCommand", risk="medium"),
                PlanStep(step_id="s2", title="部署", action="部署新代码",
                         tool="runCommand", target="/opt/app"),
            ],
            risks=["可能短暂停机"],
            files=["/opt/app/main.py"],
        )
        text = formatPlanForPrompt(plan)
        self.assertIn("部署新版本", text)
        self.assertIn("s1", text)
        self.assertIn("s2", text)
        self.assertIn("备份数据库", text)
        self.assertIn("部署新代码", text)
        self.assertIn("可能短暂停机", text)
        self.assertIn("可能短暂停机", text)


class TestPlanMode(unittest.TestCase):
    """测试 PLAN 模式的工具过滤行为。"""

    def setUp(self):
        self._tools = [
            {"function": {"name": "readFile"}},
            {"function": {"name": "submitPlan"}},
            {"function": {"name": "writeFile"}},
        ]
        self._risk = {
            "readFile": ToolRiskLevel.READ_ONLY,
            "submitPlan": ToolRiskLevel.READ_ONLY,
            "writeFile": ToolRiskLevel.WRITE,
        }

    def test_plan_mode_includes_submit_plan(self):
        """PLAN 模式应包含 submitPlan 工具。"""
        result = AgentRouter.filterToolsByMode(
            AgentMode.PLAN, self._tools, self._risk.get,
        )
        names = [t["function"]["name"] for t in result]
        self.assertIn("submitPlan", names)
        self.assertIn("readFile", names)
        self.assertNotIn("writeFile", names)

    def test_executing_mode_includes_all_tools(self):
        """EXECUTING 模式应包含全部工具。"""
        result = AgentRouter.filterToolsByMode(
            AgentMode.EXECUTING, self._tools, self._risk.get,
        )
        names = [t["function"]["name"] for t in result]
        self.assertEqual(len(names), 3)
        self.assertIn("writeFile", names)

    def test_executing_mode_allows_dangerous(self):
        """EXECUTING 模式门控应允许高危工具（同 AGENT）。"""
        levels = AgentRouter.getAllowedRiskLevels(AgentMode.EXECUTING)
        self.assertIn(ToolRiskLevel.DANGEROUS, levels)

    def test_executing_prompt_defined(self):
        """EXECUTING 模式的 prompt 应存在且可读。"""
        from agent.agent_router.router import getModePrompt
        prompt = getModePrompt(AgentMode.EXECUTING)
        self.assertIn("执行模式", prompt)
        self.assertIn("已批准的计划", prompt)


if __name__ == "__main__":
    unittest.main()
