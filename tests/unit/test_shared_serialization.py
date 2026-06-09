import unittest
from agent.shared.serialization import canonical_json, safe_truncate

class TestSerialization(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(canonical_json({"b": 2, "a": 1}), '{"a":1,"b":2}')
    def test_safeTruncateShort(self):
        t, ok = safe_truncate("hello", 100)
        self.assertEqual(t, "hello"); self.assertFalse(ok)
    def test_safeTruncateLong(self):
        t, ok = safe_truncate("A" * 100, 50)
        self.assertTrue(ok); self.assertIn("截断", t)
