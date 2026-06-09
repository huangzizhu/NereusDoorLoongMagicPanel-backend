import os
import tempfile
import unittest

from agent.config_envs.dotenv import parseEnvFile, loadDotenv


class TestDotenv(unittest.TestCase):
    def _write(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".env")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_basic_keyvalue(self):
        path = self._write("KEY=value\nNUM=42\n")
        parsed = parseEnvFile(path)
        self.assertEqual(parsed["KEY"], "value")
        self.assertEqual(parsed["NUM"], "42")

    def test_export_prefix(self):
        path = self._write("export FOO=bar\n")
        self.assertEqual(parseEnvFile(path)["FOO"], "bar")

    def test_quoted_values(self):
        path = self._write("A=\"hello world\"\nB='single'\n")
        parsed = parseEnvFile(path)
        self.assertEqual(parsed["A"], "hello world")
        self.assertEqual(parsed["B"], "single")

    def test_double_quote_escape(self):
        path = self._write('A="line1\\nline2"\n')
        self.assertEqual(parseEnvFile(path)["A"], "line1\nline2")

    def test_inline_comment(self):
        path = self._write("KEY=value  # trailing comment\n")
        self.assertEqual(parseEnvFile(path)["KEY"], "value")

    def test_hash_in_quotes_not_comment(self):
        path = self._write('KEY="a#b"\n')
        self.assertEqual(parseEnvFile(path)["KEY"], "a#b")

    def test_comment_and_blank_lines_skipped(self):
        path = self._write("# comment\n\n   \nKEY=v\n")
        parsed = parseEnvFile(path)
        self.assertEqual(parsed, {"KEY": "v"})

    def test_invalid_lines_skipped(self):
        path = self._write("NO EQUALS HERE\n1BADKEY=x\nGOOD=ok\n")
        parsed = parseEnvFile(path)
        self.assertEqual(parsed, {"GOOD": "ok"})

    def test_missing_file_returns_empty(self):
        self.assertEqual(parseEnvFile("/no/such/file.env"), {})

    def test_loadDotenv_no_override(self):
        os.environ["NDLM_TEST_DOTENV_X"] = "preset"
        self.addCleanup(os.environ.pop, "NDLM_TEST_DOTENV_X", None)
        path = self._write("NDLM_TEST_DOTENV_X=fromfile\n")
        loadDotenv(path, override=False)
        self.assertEqual(os.environ["NDLM_TEST_DOTENV_X"], "preset")

    def test_loadDotenv_override(self):
        os.environ["NDLM_TEST_DOTENV_Y"] = "preset"
        self.addCleanup(os.environ.pop, "NDLM_TEST_DOTENV_Y", None)
        path = self._write("NDLM_TEST_DOTENV_Y=fromfile\n")
        loadDotenv(path, override=True)
        self.assertEqual(os.environ["NDLM_TEST_DOTENV_Y"], "fromfile")


if __name__ == "__main__":
    unittest.main()
