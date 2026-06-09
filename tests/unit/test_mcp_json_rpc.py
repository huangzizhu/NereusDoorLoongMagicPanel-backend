import json, unittest
from ndlmpanel_agent.mcp.protocol.json_rpc import (encodeRequest, decodeRequest,
    encodeResult, encodeError, METHOD_NOT_FOUND)

class TestJsonRpc(unittest.TestCase):
    def test_encode(self):
        d = json.loads(encodeRequest("ping", {}, 1))
        self.assertEqual(d["method"], "ping")
    def test_decode(self):
        r = decodeRequest(json.dumps({"jsonrpc": "2.0", "id": 5, "method": "tools/list", "params": {}}))
        self.assertEqual(r.method, "tools/list")
    def test_result(self):
        d = json.loads(encodeResult(1, {"ok": True}))
        self.assertEqual(d["result"]["ok"], True)
    def test_error(self):
        d = json.loads(encodeError(1, METHOD_NOT_FOUND, "bad"))
        self.assertEqual(d["error"]["code"], METHOD_NOT_FOUND)
