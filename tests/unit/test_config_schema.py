import unittest
from agent.config_envs.schema import validateConfig
from agent.shared.types import AgentConfig

class TestValidate(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(validateConfig(AgentConfig(llm_endpoint="https://x.com")), [])

    def test_empty(self):
        with self.assertRaises(ValueError):
            AgentConfig(llm_endpoint="")

    def test_bad_scheme(self):
        self.assertTrue(len(validateConfig(AgentConfig(llm_endpoint="ftp://x"))) > 0)

    def test_bounds(self):
        self.assertTrue(len(validateConfig(AgentConfig(llm_endpoint="https://x", max_tool_rounds=200))) > 0)
