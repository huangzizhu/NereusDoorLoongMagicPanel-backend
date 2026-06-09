import json
import os
import tempfile
import unittest

from agent.trace_log.logging_setup import (
    setupLogging,
    getLogger,
    StructuredFormatter,
    _resetForTest,
)


class TestLoggingSetup(unittest.TestCase):
    def setUp(self):
        _resetForTest()
        self._dir = tempfile.mkdtemp()
        self._logFile = os.path.join(self._dir, "agent.log")

    def tearDown(self):
        _resetForTest()

    def test_setup_creates_logfile(self):
        setupLogging(logFile=self._logFile, console=False)
        getLogger("t").info("hi")
        self.assertTrue(os.path.exists(self._logFile))

    def test_structured_output_is_json(self):
        setupLogging(level="DEBUG", logFile=self._logFile, console=False)
        getLogger("t").info("message one")
        with open(self._logFile, encoding="utf-8") as f:
            line = f.readline()
        entry = json.loads(line)
        self.assertEqual(entry["message"], "message one")
        self.assertEqual(entry["level"], "INFO")
        self.assertIn("ts", entry)

    def test_extra_fields_included(self):
        setupLogging(logFile=self._logFile, console=False)
        getLogger("t").warning("w", extra={"session_id": "s1", "tool": "x"})
        with open(self._logFile, encoding="utf-8") as f:
            entry = json.loads(f.readline())
        self.assertEqual(entry["session_id"], "s1")
        self.assertEqual(entry["tool"], "x")

    def test_idempotent(self):
        logger = setupLogging(logFile=self._logFile, console=False)
        n = len(logger.handlers)
        setupLogging(logFile=self._logFile, console=False)
        self.assertEqual(len(logger.handlers), n)

    def test_formatter_handles_exception(self):
        fmt = StructuredFormatter()
        import logging
        try:
            raise ValueError("boom")
        except ValueError:
            rec = logging.LogRecord(
                "ndlmpanel.t", logging.ERROR, __file__, 1, "err", None,
                __import__("sys").exc_info())
        out = json.loads(fmt.format(rec))
        self.assertIn("exception", out)
        self.assertIn("boom", out["exception"])


if __name__ == "__main__":
    unittest.main()
