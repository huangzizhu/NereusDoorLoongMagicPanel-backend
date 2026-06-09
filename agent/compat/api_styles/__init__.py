"""API 风格适配器 — OpenAI / Claude / Native。"""
from agent.compat.api_styles.openai_adapter import OpenAIAdapter
from agent.compat.api_styles.claude_adapter import ClaudeAdapter
__all__ = ["OpenAIAdapter", "ClaudeAdapter"]
