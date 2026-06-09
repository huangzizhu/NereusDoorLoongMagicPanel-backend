import json, os, tempfile, unittest
from agent.config_envs.loader import loadConfig, mergeConfigs
from agent.shared.errors import AgentError

class TestMerge(unittest.TestCase):
    def test_shallow(self):
        self.assertEqual(mergeConfigs({"a": 1}, {"b": 2}), {"a": 1, "b": 2})
    def test_deep(self):
        self.assertEqual(mergeConfigs({"a": {"x": 1}}, {"a": {"y": 2}}), {"a": {"x": 1, "y": 2}})
    def test_override(self):
        self.assertEqual(mergeConfigs({"a": 1}, {"a": 99})["a"], 99)

class TestLoad(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"llm_endpoint": "https://api.test.com", "llm_model": "test-model"}, self.tmp)
        self.tmp.close()
    def tearDown(self):
        os.unlink(self.tmp.name)
    def test_valid(self):
        c = loadConfig(self.tmp.name, envFile=None)
        self.assertEqual(c.llm_endpoint, "https://api.test.com")
    def test_missing(self):
        with self.assertRaises(AgentError): loadConfig("/nonexistent.json", envFile=None)
    def test_envOverride(self):
        os.environ["NDLM_LLM_MODEL"] = "env-model"
        c = loadConfig(self.tmp.name, envFile=None)
        self.assertEqual(c.llm_model, "env-model")
        del os.environ["NDLM_LLM_MODEL"]
    def test_runtimeOverride(self):
        c = loadConfig(self.tmp.name, overrides={"llm_max_tokens": 8192}, envFile=None)
        self.assertEqual(c.llm_max_tokens, 8192)
