import os, unittest
from agent.config_envs.secrets import getSecret

class TestSecrets(unittest.TestCase):
    def test_get(self):
        os.environ["TEST_SECRET"] = "mykey"
        self.assertEqual(getSecret("test", "TEST_SECRET"), "mykey")
        del os.environ["TEST_SECRET"]
    def test_missing(self):
        self.assertEqual(getSecret("missing", "NO_VAR"), "")
