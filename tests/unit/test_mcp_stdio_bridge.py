import json
import unittest

from agent.integration.mcp_stdio import (
    MultiServerSpec,
    MultiStdioMcpBridge,
    StdioMcpBridge,
    defaultStdioCommand,
    defaultStdioCwd,
)
from ndlmpanel_agent.mcp.protocol.json_rpc import encodeRequest


class TestStdioMcpBridge(unittest.TestCase):
    def test_default_stdio_bridge_lists_and_calls_tools(self):
        bridge = StdioMcpBridge()
        try:
            schemas = bridge.registry.listTools()
            names = {schema["function"]["name"] for schema in schemas}
            self.assertIn("getCpuInfo", names)

            raw = bridge.dispatcher.handle(
                encodeRequest("tools/call", {"name": "getCpuInfo", "arguments": {}}, 1)
            )
            data = json.loads(raw)
            payload = json.loads(data["result"]["content"][0]["text"])
            self.assertGreater(payload["coreCount"], 0)
        finally:
            bridge.close()


class TestMultiStdioMcpBridge(unittest.TestCase):
    def test_single_server_aggregation(self):
        """MultiStdioMcpBridge with one server works like StdioMcpBridge."""
        spec = MultiServerSpec("default", defaultStdioCommand(), defaultStdioCwd())
        bridge = MultiStdioMcpBridge([spec])
        try:
            schemas = bridge.registry.listTools()
            names = {schema["function"]["name"] for schema in schemas}
            self.assertIn("getCpuInfo", names)

            raw = bridge.dispatcher.handle(
                encodeRequest("tools/call", {"name": "getCpuInfo", "arguments": {}}, 1)
            )
            data = json.loads(raw)
            payload = json.loads(data["result"]["content"][0]["text"])
            self.assertGreater(payload["coreCount"], 0)
        finally:
            bridge.close()

    def test_name_conflict_rejected(self):
        """Two servers exposing the same tool name raise RuntimeError."""
        spec = MultiServerSpec("a", defaultStdioCommand(), defaultStdioCwd())
        spec2 = MultiServerSpec("b", defaultStdioCommand(), defaultStdioCwd())
        with self.assertRaises(RuntimeError) as ctx:
            MultiStdioMcpBridge([spec, spec2])
        msg = str(ctx.exception)
        self.assertIn("tool name conflict", msg)
        self.assertIn("getCpuInfo", msg)  # common tool likely conflicts

    def test_empty_servers_rejected(self):
        """Empty server list raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            MultiStdioMcpBridge([])
        self.assertIn("at least one server", str(ctx.exception))

    def test_invalid_server_spec(self):
        """Invalid command raises RuntimeError during initialization."""
        spec = MultiServerSpec("bad", ["/nonexistent/binary"])
        with self.assertRaises(RuntimeError) as ctx:
            MultiStdioMcpBridge([spec])
        self.assertIn("failed to start", str(ctx.exception))
