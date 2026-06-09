"""
Shared 模块 — 公共类型、错误码、序列化工具、ID 生成。

零外部依赖，全部基于 Python 3.10+ stdlib。
"""

from agent.shared.types import (
    AgentConfig, AgentEvent, EventType, LLMResponse,
    SafetyVerdict, ToolCall, ToolDefinition, ToolResult,
    ToolRiskLevel, TraceEntry,
)
from agent.shared.errors import AgentError, ErrorCode
from agent.shared.serialization import canonical_json, safe_truncate
from agent.shared.id_gen import gen_session_id, gen_tool_call_id, gen_trace_id

__all__ = [
    "EventType", "ToolRiskLevel", "SafetyVerdict",
    "AgentEvent", "ToolDefinition", "ToolCall", "ToolResult",
    "TraceEntry", "LLMResponse", "AgentConfig",
    "ErrorCode", "AgentError",
    "canonical_json", "safe_truncate",
    "gen_session_id", "gen_trace_id", "gen_tool_call_id",
]
