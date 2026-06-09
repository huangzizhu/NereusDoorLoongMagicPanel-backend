"""审批闭环端到端测试 —— 验证 Phase A P0 Bug 修复。

覆盖三条路径：approve / reject / timeout，全部用 MockProvider 离线运行。
"""
import asyncio
import unittest

from agent.shared.types import AgentConfig, EventType
from agent.integration.session import AgentSession
from agent.llm_providers.mock import MockProvider


def _newSession(approvalTimeout: float = 300.0) -> AgentSession:
    config = AgentConfig(llm_endpoint="https://api.test.com")
    session = AgentSession(config)
    # 第一轮：调用危险工具 deleteFile；第二轮：给出文字结论
    session._core._llm = MockProvider([
        {"tool_calls": [{"id": "tc1", "name": "deleteFile",
                         "arguments": {"targetPath": "/tmp/ndlm_xyz"}}]},
        {"content": "处理完成"},
    ])
    session._core._approvalTimeout = approvalTimeout
    return session


async def _drive(session: AgentSession, decision: str):
    events = []
    tool_output = None
    async def consume():
        nonlocal tool_output
        async for ev in session.submit("删除临时文件"):
            events.append(ev.type.value)
            if ev.type == EventType.APPROVAL_REQUIRED:
                if decision == "approve":
                    session.approve(ev.data["action_id"])
                elif decision == "reject":
                    session.reject(ev.data["action_id"], "不允许")
                # decision == "timeout": 不作处理
            if ev.type == EventType.TOOL_RESULT:
                tool_output = ev.data["output"]
    await asyncio.wait_for(consume(), timeout=15)
    return events, tool_output


class TestApprovalClosure(unittest.TestCase):
    def test_reject_does_not_execute(self):
        session = _newSession()
        self.addCleanup(session.close)
        events, out = asyncio.run(_drive(session, "reject"))
        self.assertIn("approval.required", events)
        self.assertIn("approval.resolved", events)
        self.assertIn("done", events)
        self.assertIn("拒绝", out)

    def test_approve_executes(self):
        session = _newSession()
        self.addCleanup(session.close)
        events, out = asyncio.run(_drive(session, "approve"))
        self.assertIn("approval.resolved", events)
        self.assertIn("done", events)
        # 批准后工具实际执行（文件不存在 → 返回失败信息，但不是"拒绝/超时"）
        self.assertNotIn("用户拒绝", out)
        self.assertNotIn("审批超时", out)

    def test_timeout_skips_execution(self):
        session = _newSession(approvalTimeout=0.3)
        self.addCleanup(session.close)
        events, out = asyncio.run(_drive(session, "timeout"))
        self.assertIn("approval.required", events)
        self.assertIn("done", events)
        self.assertIn("超时", out)

    def test_stream_always_terminates_on_error(self):
        # LLM 抛异常时，stream 仍应收到 ERROR 并终止（不挂起）
        config = AgentConfig(llm_endpoint="https://api.test.com")
        session = AgentSession(config)
        self.addCleanup(session.close)

        class _BoomProvider:
            async def chat(self, messages):
                raise RuntimeError("llm boom")
            async def chatStream(self, messages):
                raise RuntimeError("llm boom")
                yield  # pragma: no cover

        session._core._llm = _BoomProvider()

        async def consume():
            events = []
            async for ev in session.submit("hi"):
                events.append(ev.type.value)
            return events

        events = asyncio.run(asyncio.wait_for(consume(), timeout=10))
        self.assertIn("error", events)


if __name__ == "__main__":
    unittest.main()
