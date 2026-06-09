"""
LLM Provider 工厂。

根据 AgentConfig.llm_provider / llm_endpoint 自动选择 Provider：
  - endpoint 包含 "/anthropic" → AnthropicProvider（DeepSeek Anthropic 端点）
  - 通用 OpenAI-compatible 端点 → OpenAIProvider（Qwen/vLLM/Ollama 等）
  - "mock" 或缺 api_key → MockProvider（离线测试）

供应商默认值（仅当 config 未显式指定 endpoint/model 时生效）：
  deepseek      → https://api.deepseek.com/anthropic  / deepseek-chat
  qwen          → https://dashscope.aliyuncs.com/compatible-mode/v1 / qwen-plus
  openai_compat → 必须显式配置 endpoint 与 model（通用兜底）
  mock          → MockProvider（离线测试，无需网络）
"""
from __future__ import annotations

from agent.llm_providers.anthropic_compat import AnthropicProvider
from agent.llm_providers.base import LLMProvider
from agent.llm_providers.mock import MockProvider
from agent.llm_providers.openai_compat import OpenAIProvider
from agent.shared.types import AgentConfig

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "deepseek": {
        "endpoint": "https://api.deepseek.com/anthropic",
        "model": "deepseek-v4-pro",
    },
    "qwen": {
        "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "openai_compat": {
        "endpoint": "",
        "model": "deepseek-chat",
    },
}


def createProvider(config: AgentConfig) -> LLMProvider:
    """根据配置创建 Provider 实例。

    自动检测：若 llm_endpoint 包含 "/anthropic"，使用 AnthropicProvider；
    否则使用 OpenAIProvider。
    """
    providerType = (config.llm_provider or "openai_compat").lower()

    if providerType == "mock" or not config.llm_api_key:
        return MockProvider([
            {"content": "[MockProvider] 未配置 LLM API Key，当前为离线模式。"}
        ])

    defaults = PROVIDER_DEFAULTS.get(providerType,
                                     PROVIDER_DEFAULTS["openai_compat"])
    endpoint = config.llm_endpoint or defaults["endpoint"]
    model = config.llm_model or defaults["model"]

    if not endpoint:
        raise ValueError(
            f"provider '{providerType}' 需要显式配置 llm_endpoint")

    # 自动检测：Anthropic 格式端点
    if "/anthropic" in endpoint:
        return AnthropicProvider(
            endpoint=endpoint, apiKey=config.llm_api_key, model=model,
            maxTokens=config.llm_max_tokens, temperature=config.llm_temperature,
            retryCount=config.llm_retry_count, retryDelay=config.llm_retry_delay,
        )

    return OpenAIProvider(
        endpoint=endpoint, apiKey=config.llm_api_key, model=model,
        maxTokens=config.llm_max_tokens, temperature=config.llm_temperature,
        retryCount=config.llm_retry_count, retryDelay=config.llm_retry_delay,
    )
