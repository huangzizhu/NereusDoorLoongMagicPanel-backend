"""
LLM 配置与端点工具函数。

统一处理 LLM 配置的获取（DB Profile → 文件配置兜底）、
端点 URL 规整化等共享逻辑，供 audit_service、AgentGatewayService 等模块复用。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("ndlmpanel.utils")


def get_llm_config(session=None) -> dict[str, str]:
    """获取 LLM 配置（endpoint, api_key, model）。

    优先从数据库默认 profile（credential.baseUrl / credential.apiKey / profile.model）获取，
    兜底走 loadConfig() 文件配置。

    如果 session 有 profileId，优先使用该 profile；否则用默认 profile。

    Returns:
        {"endpoint": str, "api_key": str, "model": str}
        全部为空字符串表示未找到有效配置。
    """
    try:
        from gateway.service.AgentLlmProfileService import AgentLlmProfileService

        svc = AgentLlmProfileService()

        # 优先从 session 指定的 profile
        if session and getattr(session, "profileId", None):
            profile = svc.dao.getProfileById(session.profileId)
            if profile:
                cred = svc.dao.getCredentialById(profile.credentialId) if profile.credentialId else None
                if cred and cred.baseUrl and cred.apiKey:
                    return {
                        "endpoint": cred.baseUrl,
                        "api_key": cred.apiKey,
                        "model": profile.model or "deepseek-chat",
                    }

        # 走 buildAgentConfig（内置兜底链：默认 profile → loadConfig → Mock）
        ac = svc.buildAgentConfig()
        if ac and ac.llm_api_key and ac.llm_endpoint:
            return {
                "endpoint": ac.llm_endpoint,
                "api_key": ac.llm_api_key,
                "model": ac.llm_model or "deepseek-chat",
            }
    except Exception as exc:
        logger.warning("get_llm_config: DB profile 读取失败: %s，尝试文件兜底", exc)

    # 兜底: 文件配置
    try:
        from agent.config_envs.loader import loadConfig

        cfg = loadConfig()
        if cfg and cfg.llm_api_key and cfg.llm_endpoint:
            return {
                "endpoint": cfg.llm_endpoint,
                "api_key": cfg.llm_api_key,
                "model": cfg.llm_model or "deepseek-chat",
            }
    except Exception as exc:
        logger.warning("get_llm_config: 文件配置读取失败: %s", exc)

    return {"endpoint": "", "api_key": "", "model": "deepseek-chat"}


def normalize_endpoint(endpoint: str) -> str:
    """规整化 LLM 端点 URL（用于 raw HTTP 调用，如 audit_service）。

    OpenAIProvider / AnthropicProvider 内部会追加 /chat/completions 或 /messages，
    此函数用于不经过 Provider、直接调 urllib 的场景。

    规则：
    - `api.deepseek.com` + `/anthropic` → `https://api.deepseek.com/chat/completions`
    - `api.deepseek.com`（官方 OpenAI 端点）→ `https://api.deepseek.com/chat/completions`（无 /v1）
    - 其他 → 加 `/v1/chat/completions`
    - 末尾多余斜杠 → 去除

    Args:
        endpoint: 原始端点 URL

    Returns:
        规整化后的端点 URL，保证以 `/chat/completions` 结尾
    """
    endpoint = endpoint.rstrip("/")

    # DeepSeek Anthropic 兼容端点 → 转为 OpenAI-compatible 格式
    if endpoint.endswith("/anthropic"):
        endpoint = "https://api.deepseek.com/chat/completions"
    elif endpoint.endswith("/chat/completions"):
        pass  # 已是标准格式
    elif "api.deepseek.com" in endpoint:
        # DeepSeek 官方 OpenAI 端点：/chat/completions，不用 /v1
        endpoint = "https://api.deepseek.com/chat/completions"
    elif endpoint.endswith("/v1"):
        endpoint = endpoint + "/chat/completions"
    else:
        endpoint = endpoint + "/v1/chat/completions"

    return endpoint
