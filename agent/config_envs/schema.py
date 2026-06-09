"""配置校验规则。"""
from agent.shared.types import AgentConfig

def validateConfig(config: AgentConfig) -> list[str]:
    issues: list[str] = []
    if not config.llm_endpoint:
        issues.append("llm_endpoint 不能为空")
    elif not (config.llm_endpoint.startswith("http://")
              or config.llm_endpoint.startswith("https://")):
        issues.append("llm_endpoint 必须以 http:// 或 https:// 开头")
    if config.max_tool_rounds != 0 and not 1 <= config.max_tool_rounds <= 100:
        issues.append("max_tool_rounds 必须为 0（不限制）或 1-100 之间")
    if config.max_tool_calls_per_round != 0 and not 1 <= config.max_tool_calls_per_round <= 100:
        issues.append("max_tool_calls_per_round 必须为 0（不限制）或 1-100 之间")
    if not 1 <= config.tool_timeout_seconds <= 600:
        issues.append("tool_timeout_seconds 必须在 1-600 之间")
    if not 256 <= config.llm_max_tokens <= 262144:
        issues.append("llm_max_tokens 必须在 256-262144 之间")
    if not config.execution_user:
        issues.append("execution_user 不能为空")
    if not 0.0 <= config.llm_temperature <= 2.0:
        issues.append("llm_temperature 必须在 0-2 之间")
    if not 0 <= config.llm_retry_count <= 10:
        issues.append("llm_retry_count 必须在 0-10 之间")
    if config.llm_retry_delay < 0:
        issues.append("llm_retry_delay 不能为负")
    return issues
