import unittest
from enum import Enum
from ndlmpanel_agent.mcp.protocol.schemas import annotationToJsonSchema, functionToToolSchema

class Color(str, Enum):
    RED = "red"; BLUE = "blue"

def sampleFunc(name: str, count: int = 1, color: Color = Color.RED) -> dict:
    '''Sample tool.'''
    return {}

class TestSchemas(unittest.TestCase):
    def test_primitive(self):
        self.assertEqual(annotationToJsonSchema(str), {"type": "string"})
        self.assertEqual(annotationToJsonSchema(int), {"type": "integer"})
    def test_enum(self):
        s = annotationToJsonSchema(Color)
        self.assertEqual(s["enum"], ["red", "blue"])
    def test_function(self):
        s = functionToToolSchema(sampleFunc)
        self.assertEqual(s["function"]["name"], "sampleFunc")
        self.assertIn("name", s["function"]["parameters"]["properties"])
