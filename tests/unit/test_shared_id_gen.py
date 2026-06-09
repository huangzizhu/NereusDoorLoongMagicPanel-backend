import unittest
from agent.shared.id_gen import gen_session_id, gen_trace_id, gen_tool_call_id

class TestIdGen(unittest.TestCase):
    def test_prefixes(self):
        self.assertTrue(gen_session_id().startswith("sess_"))
        self.assertTrue(gen_trace_id().startswith("trace_"))
        self.assertTrue(gen_tool_call_id().startswith("tc_"))
    def test_uniqueness(self):
        ids = {gen_session_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)
