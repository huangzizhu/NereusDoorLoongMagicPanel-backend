"""
Mock Provider — 离线测试用。

可编程预设响应，不依赖外部 API。
"""
from __future__ import annotations
import json
from collections.abc import AsyncIterator
from agent.llm_providers.base import LLMProvider
from agent.shared.types import LLMResponse


class MockProvider(LLMProvider):
    """Mock LLM Provider — 可预设响应序列。"""

    def __init__(self, responses: list[dict] | None = None):
        """
        Args:
            responses: 预设响应列表，每个元素为 dict:
                {"content": "..."}  或  {"tool_calls": [{"id":..., "name":..., "arguments":{}}]}
        """
        self._responses = responses or []
        self._callCount = 0

    async def chat(self, messages: list[dict]) -> LLMResponse:
        resp = self._nextResponse()
        if "tool_calls" in resp:
            return LLMResponse(tool_calls=resp["tool_calls"],
                               finish_reason="tool_calls")
        return LLMResponse(content=resp.get("content", ""),
                           finish_reason="stop")

    async def chatStream(self, messages: list[dict]) -> AsyncIterator[LLMResponse]:
        resp = self._nextResponse()
        if "tool_calls" in resp:
            yield LLMResponse(content=None, tool_calls=resp["tool_calls"],
                              finish_reason="tool_calls")
            return
        content = resp.get("content", "")
        # 每5个字符 yield 一个增量
        for i in range(0, len(content), 5):
            yield LLMResponse(content=content[i:i+5], finish_reason="")
        yield LLMResponse(content=None, finish_reason="stop")

    def mockSetResponses(self, responses: list[dict]) -> None:
        """预设响应序列。"""
        self._responses = responses
        self._callCount = 0

    def _nextResponse(self) -> dict:
        if self._callCount < len(self._responses):
            r = self._responses[self._callCount]
            self._callCount += 1
            return r
        return {"content": "(MockProvider: 无更多预设响应)"}
