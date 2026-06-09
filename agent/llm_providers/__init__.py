"""LLM Provider 适配层 — OpenAI-compatible + Mock。"""
from agent.llm_providers.base import LLMProvider
from agent.llm_providers.openai_compat import OpenAIProvider
from agent.llm_providers.mock import MockProvider
__all__ = ["LLMProvider", "OpenAIProvider", "MockProvider"]
