import unittest
from agent.shared.types import (EventType, ToolRiskLevel, SafetyVerdict,
    AgentEvent, ToolDefinition, ToolCall, ToolResult, TraceEntry, LLMResponse,
    AgentConfig, dataclass_to_dict, dict_to_dataclass)

class TestEnums(unittest.TestCase):
    def test_eventType(self):
        self.assertEqual(EventType.DONE, "done")
        self.assertEqual(EventType.ERROR, "error")
    def test_riskLevel(self):
        self.assertEqual(ToolRiskLevel.READ_ONLY, "read_only")
        self.assertEqual(ToolRiskLevel.DANGEROUS, "dangerous")
    def test_verdict(self):
        self.assertEqual(SafetyVerdict.ALLOW, "allow")
        self.assertEqual(SafetyVerdict.BLOCK, "block")

class TestDataclasses(unittest.TestCase):
    def test_agentEvent(self):
        ev = AgentEvent(type="test", session_id="s1", trace_id="t1")
        self.assertGreater(ev.timestamp, 0)
        self.assertEqual(ev.data, {})
    def test_toolDefinition(self):
        td = ToolDefinition(name="getCpu", description="x", parameters={})
        self.assertEqual(td.risk_level, ToolRiskLevel.WRITE)
    def test_toolCall(self):
        tc = ToolCall(id="tc1", name="disk.usage", arguments={"path": "/"})
        self.assertEqual(tc.name, "disk.usage")
    def test_toolResult(self):
        tr = ToolResult(call_id="tc1", tool_name="test", success=True, output="ok", truncated=True)
        self.assertTrue(tr.truncated)
    def test_llmResponse(self):
        r = LLMResponse(content="hello")
        self.assertEqual(r.content, "hello")
        self.assertEqual(r.tool_calls, [])
    def test_configValidation(self):
        with self.assertRaises(ValueError): AgentConfig(llm_endpoint="")
    def test_dataclassToDict(self):
        tc = ToolCall(id="x", name="n", arguments={"a": 1})
        self.assertEqual(dataclass_to_dict(tc)["name"], "n")
    def test_dictToDataclass(self):
        tc = dict_to_dataclass({"id": "x", "name": "n", "arguments": {"a": 1}}, ToolCall)
        self.assertEqual(tc.name, "n")
