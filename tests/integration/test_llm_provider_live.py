"""LLM Provider 测试。

- TestProviderFactory / TestSSEParser / TestStreamChunkParsing / TestRetryError:
  纯离线，无需网络
- TestLLMProviderLive: 真机 API 测试，缺 NDLM_LLM_API_KEY 时自动 skip
"""
import asyncio
import io
import os
import unittest
import urllib.error

from agent.llm_providers.factory import createProvider, PROVIDER_DEFAULTS
from agent.llm_providers.mock import MockProvider
from agent.llm_providers.openai_compat import OpenAIProvider
from agent.llm_providers.sse_parser import parseSseStream, mergeSseDeltas
from agent.shared.types import AgentConfig
from agent.shared.errors import AgentError, ErrorCode


def _cfg(**kw) -> AgentConfig:
    base = dict(llm_endpoint="https://api.test.com/v1")
    base.update(kw)
    apiKey = base.pop("apiKey", None)
    c = AgentConfig(**base)
    if apiKey is not None:
        c.llm_api_key = apiKey
    return c


class TestProviderFactory(unittest.TestCase):
    def test_no_apikey_returns_mock(self):
        self.assertIsInstance(createProvider(_cfg()), MockProvider)

    def test_explicit_mock(self):
        self.assertIsInstance(
            createProvider(_cfg(llm_provider="mock", apiKey="sk-x")),
            MockProvider)

    def test_deepseek_builds_openai_provider(self):
        p = createProvider(_cfg(llm_provider="deepseek", apiKey="sk-x"))
        self.assertIsInstance(p, OpenAIProvider)

    def test_deepseek_default_endpoint(self):
        self.assertTrue(
            PROVIDER_DEFAULTS["deepseek"]["endpoint"].startswith(
                "https://api.deepseek.com"))

    def test_qwen_default_endpoint(self):
        self.assertIn("dashscope", PROVIDER_DEFAULTS["qwen"]["endpoint"])

    def test_explicit_endpoint_overrides_default(self):
        p = createProvider(_cfg(llm_provider="deepseek", apiKey="sk-x",
                                llm_endpoint="https://custom.local/v1"))
        self.assertEqual(p._endpoint, "https://custom.local/v1")

    def test_retry_params_passed(self):
        p = createProvider(_cfg(llm_provider="deepseek", apiKey="sk-x",
                                llm_retry_count=5, llm_retry_delay=2.0))
        self.assertEqual(p._retryCount, 5)
        self.assertEqual(p._retryDelay, 2.0)


class TestSSEParser(unittest.TestCase):
    def test_parse_simple_stream(self):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}',
            'data: {"choices":[{"delta":{"content":" World"},"index":0}]}',
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"total_tokens":10}}',
            'data: [DONE]',
        ]
        events = parseSseStream(lines)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["delta"]["content"], "Hello")
        self.assertEqual(events[2]["finish_reason"], "stop")

    def test_merge_content(self):
        events = [
            {"delta": {"content": "ab"}, "finish_reason": ""},
            {"delta": {"content": "cd"}, "finish_reason": "stop"},
        ]
        merged = mergeSseDeltas(events)
        self.assertEqual(merged["content"], "abcd")
        self.assertEqual(merged["finish_reason"], "stop")

    def test_merge_tool_calls(self):
        events = [
            {"delta": {"tool_calls": [
                {"index": 0, "id": "tc1",
                 "function": {"name": "getCpuInfo", "arguments": ""}}]},
             "finish_reason": ""},
            {"delta": {"tool_calls": [
                {"index": 0, "function": {"arguments": ""}}]},
             "finish_reason": "tool_calls"},
        ]
        merged = mergeSseDeltas(events)
        self.assertEqual(len(merged["tool_calls"]), 1)
        self.assertEqual(merged["tool_calls"][0]["name"], "getCpuInfo")
        self.assertEqual(merged["tool_calls"][0]["arguments"], {})


class TestStreamChunkParsing(unittest.TestCase):
    def setUp(self):
        self.p = OpenAIProvider("https://api.test.com/v1", apiKey="sk-x")

    def test_content_chunk(self):
        r = self.p._parseStreamChunk(
            '{"choices":[{"delta":{"content":"hi"}}]}')
        self.assertEqual(r.content, "hi")

    def test_finish_chunk(self):
        r = self.p._parseStreamChunk(
            '{"choices":[{"delta":{},"finish_reason":"stop"}]}')
        self.assertIsNone(r.content)
        self.assertEqual(r.finish_reason, "stop")

    def test_empty_delta_returns_none(self):
        self.assertIsNone(
            self.p._parseStreamChunk('{"choices":[{"delta":{}}]}'))

    def test_bad_json_returns_none(self):
        self.assertIsNone(self.p._parseStreamChunk("not json"))


class TestRetryError(unittest.TestCase):
    def test_malformed_response_raises(self):
        p = OpenAIProvider("https://api.test.com/v1", apiKey="sk-x")
        with self.assertRaises(AgentError) as ctx:
            p._parseResponse("not valid json")
        self.assertEqual(ctx.exception.code, ErrorCode.LLM_RESPONSE_MALFORMED)

    def test_wrap_http_401(self):
        p = OpenAIProvider("https://api.test.com/v1", apiKey="sk-x")
        err = urllib.error.HTTPError(
            "url", 401, "Unauthorized", {}, io.BytesIO(b""))
        wrapped = p._wrapHttpError(err)
        self.assertEqual(wrapped.code, ErrorCode.LLM_CONNECTION_FAILED)

    def test_wrap_http_429(self):
        p = OpenAIProvider("https://api.test.com/v1", apiKey="sk-x")
        err = urllib.error.HTTPError("url", 429, "Too Many", {}, io.BytesIO(b""))
        wrapped = p._wrapHttpError(err)
        self.assertEqual(wrapped.code, ErrorCode.LLM_RATE_LIMITED)

    def test_4xx_not_retried(self):
        """401 应立即抛出，不触发重试（通过计数 _httpPost 调用验证）。"""
        p = OpenAIProvider("https://api.test.com/v1", apiKey="sk-x",
                           retryCount=3, retryDelay=0.0)
        calls = {"n": 0}

        def _boom(body):
            calls["n"] += 1
            raise urllib.error.HTTPError(
                "url", 401, "Unauthorized", {}, io.BytesIO(b""))

        p._httpPost = _boom
        with self.assertRaises(AgentError):
            asyncio.run(p._postWithRetry(b"{}"))
        self.assertEqual(calls["n"], 1)

    def test_429_retried(self):
        """429 应重试 retryCount+1 次后抛出。"""
        p = OpenAIProvider("https://api.test.com/v1", apiKey="sk-x",
                           retryCount=2, retryDelay=0.0)
        calls = {"n": 0}

        def _boom(body):
            calls["n"] += 1
            raise urllib.error.HTTPError(
                "url", 429, "Too Many", {}, io.BytesIO(b""))

        p._httpPost = _boom
        with self.assertRaises(AgentError):
            asyncio.run(p._postWithRetry(b"{}"))
        self.assertEqual(calls["n"], 3)  # 1 + 2 retries

    def test_retry_then_success(self):
        p = OpenAIProvider("https://api.test.com/v1", apiKey="sk-x",
                           retryCount=2, retryDelay=0.0)
        calls = {"n": 0}

        def _flaky(body):
            calls["n"] += 1
            if calls["n"] < 2:
                raise urllib.error.URLError("temporary")
            return '{"choices":[{"message":{"content":"ok"}}]}'

        p._httpPost = _flaky
        raw = asyncio.run(p._postWithRetry(b"{}"))
        self.assertIn("ok", raw)
        self.assertEqual(calls["n"], 2)


def _liveApiKey() -> str:
    return os.environ.get("NDLM_LLM_API_KEY", "")


@unittest.skipUnless(_liveApiKey(), "需要 NDLM_LLM_API_KEY 才能运行真机 API 测试")
class TestLLMProviderLive(unittest.TestCase):
    def setUp(self):
        self.config = AgentConfig(
            llm_provider=os.environ.get("NDLM_LLM_PROVIDER", "deepseek"),
            llm_endpoint=os.environ.get(
                "NDLM_LLM_ENDPOINT", "https://api.deepseek.com/v1"),
            llm_model=os.environ.get("NDLM_LLM_MODEL", "deepseek-chat"),
            llm_max_tokens=256, llm_temperature=0.1,
        )
        self.config.llm_api_key = _liveApiKey()
        self.provider = createProvider(self.config)

    def test_nonstream_returns_content(self):
        resp = asyncio.run(self.provider.chat(
            [{"role": "user", "content": "只回复：OK"}]))
        self.assertTrue(resp.content and len(resp.content) > 0)
        self.assertIn("prompt_tokens", resp.usage)

    def test_stream_yields_chunks(self):
        chunks = []
        async def collect():
            async for r in self.provider.chatStream(
                    [{"role": "user", "content": "数到三"}]):
                if r.content:
                    chunks.append(r.content)
        asyncio.run(collect())
        self.assertGreater(len(chunks), 0)

    def test_invalid_key_raises(self):
        badCfg = AgentConfig(
            llm_provider=self.config.llm_provider,
            llm_endpoint=self.config.llm_endpoint,
            llm_model=self.config.llm_model, llm_retry_count=0)
        badCfg.llm_api_key = "sk-invalid-test-key"
        bad = createProvider(badCfg)
        with self.assertRaises(AgentError):
            asyncio.run(bad.chat([{"role": "user", "content": "hi"}]))


if __name__ == "__main__":
    unittest.main()
