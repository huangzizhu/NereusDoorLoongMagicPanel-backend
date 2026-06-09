import unittest
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from agent.shared.types import ToolRiskLevel

def toolA(x: int) -> int:
    '''A.'''
    return x
def toolB() -> str:
    '''B.'''
    return "B"

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = ToolRegistry()
        self.reg.register(toolA, ToolRiskLevel.READ_ONLY)
        self.reg.register(toolB, ToolRiskLevel.DANGEROUS)
    def test_list(self):
        tools = self.reg.listTools()
        self.assertEqual(len(tools), 2)
        names = [t["function"]["name"] for t in tools]
        self.assertEqual(names, sorted(names))
    def test_get(self):
        self.assertIsNotNone(self.reg.getTool("toolA"))
        self.assertIsNone(self.reg.getTool("nonexistent"))
    def test_risk(self):
        self.assertEqual(self.reg.getRiskLevel("toolA"), ToolRiskLevel.READ_ONLY)
        self.assertEqual(self.reg.getRiskLevel("toolB"), ToolRiskLevel.DANGEROUS)
