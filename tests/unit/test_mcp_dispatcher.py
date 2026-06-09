import json, unittest
from ndlmpanel_agent.mcp.protocol.json_rpc import encodeRequest
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher
from agent.shared.types import ToolRiskLevel

def echo(msg: str) -> dict:
    '''Echo.'''
    return {"echo": msg}

class TestDispatcher(unittest.TestCase):
    def setUp(self):
        self.reg = ToolRegistry()
        self.reg.register(echo, ToolRiskLevel.READ_ONLY)
        self.disp = McpDispatcher(self.reg)
    def test_initialize(self):
        d = json.loads(self.disp.handle(encodeRequest("initialize", {}, 1)))
        self.assertEqual(d["result"]["serverInfo"]["name"], "ndlmpanel-agent")
    def test_tools_list(self):
        d = json.loads(self.disp.handle(encodeRequest("tools/list", {}, 2)))
        self.assertEqual(len(d["result"]["tools"]), 1)
    def test_tools_call(self):
        d = json.loads(self.disp.handle(encodeRequest("tools/call",
            {"name": "echo", "arguments": {"msg": "hi"}}, 3)))
        content = json.loads(d["result"]["content"][0]["text"])
        self.assertEqual(content["echo"], "hi")
    def test_unknown(self):
        d = json.loads(self.disp.handle(encodeRequest("bad/method", {}, 4)))
        self.assertIn("error", d)
