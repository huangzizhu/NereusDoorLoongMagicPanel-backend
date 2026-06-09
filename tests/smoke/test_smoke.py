import json
import os
import tempfile
import unittest
from agent.config_envs.loader import loadConfig
from ndlmpanel_agent.mcp.protocol.json_rpc import encodeRequest
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher

class TestSmoke(unittest.TestCase):
    def test_fullPipeline(self):
        # 1. Config
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"llm_endpoint": "https://api.test.com"}, tmp)
        tmp.close()
        cfg = loadConfig(tmp.name, envFile=None)
        self.assertEqual(cfg.llm_endpoint, "https://api.test.com")
        os.unlink(tmp.name)

        # 2. Load current project MCP default tools
        reg = ToolRegistry.withDefaultTools()

        # 3. MCP tools/list
        disp = McpDispatcher(reg)
        d = json.loads(disp.handle(encodeRequest("tools/list", {}, 1)))
        names = {tool["name"] for tool in d["result"]["tools"]}
        self.assertIn("getCpuInfo", names)
        self.assertIn("getMemoryInfo", names)

        # 4. MCP tools/call getCpuInfo
        d = json.loads(disp.handle(encodeRequest("tools/call",
            {"name": "getCpuInfo", "arguments": {}}, 2)))
        cpu = json.loads(d["result"]["content"][0]["text"])
        self.assertGreater(cpu["coreCount"], 0)

        # 5. MCP tools/call getMemoryInfo
        d = json.loads(disp.handle(encodeRequest("tools/call",
            {"name": "getMemoryInfo", "arguments": {}}, 3)))
        mem = json.loads(d["result"]["content"][0]["text"])
        self.assertGreater(mem["totalBytes"], 0)

    def test_defaultTools(self):
        """验证当前项目 MCP 默认工具可被 OpenAI schema 列出。"""
        reg = ToolRegistry.withDefaultTools()
        schemas = reg.listTools()
        names = {schema["function"]["name"] for schema in schemas}
        self.assertIn("getCpuInfo", names)
        self.assertIn("readTextFile", names)
