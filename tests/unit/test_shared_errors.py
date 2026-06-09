import unittest
from agent.shared.errors import ErrorCode, AgentError

class TestErrors(unittest.TestCase):
    def test_values(self):
        self.assertEqual(ErrorCode.INTERNAL_ERROR, "E0001")
        self.assertEqual(ErrorCode.SAFETY_BLOCKED, "E3001")
    def test_exception(self):
        e = AgentError(ErrorCode.TIMEOUT, "timeout", {"limit": 30})
        self.assertEqual(e.code, ErrorCode.TIMEOUT)
        self.assertIn("E0003", str(e))
    def test_no_detail(self):
        e = AgentError(ErrorCode.INTERNAL_ERROR, "oops")
        self.assertEqual(e.detail, {})
