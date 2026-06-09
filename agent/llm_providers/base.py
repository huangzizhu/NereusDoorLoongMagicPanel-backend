"""
LLM Provider 抽象基类。

所有 Provider 实现此接口，
AgentCore 只依赖此抽象，不绑定具体实现。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from agent.shared.types import LLMResponse


class LLMProvider(ABC):
    """LLM 调用抽象。"""

    @abstractmethod
    async def chat(self, messages: list[dict]) -> LLMResponse:
        """非流式对话。"""
        ...

    @abstractmethod
    async def chatStream(self, messages: list[dict]) -> AsyncIterator[LLMResponse]:
        """流式对话，每次 yield 一个增量 LLMResponse。"""
        ...
