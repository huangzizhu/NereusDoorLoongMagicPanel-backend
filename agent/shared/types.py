"""
核心 dataclass 类型定义。

替代原 pydantic models，全部基于 Python 3.10+ dataclasses。
枚举类使用 (str, Enum) 继承，保证 JSON 序列化时输出字符串值。
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum


# ── 枚举 ──

class EventType(str, Enum):
    """Agent 事件流类型。"""
    SESSION_CREATED = "session.created"
    THINKING_START = "thinking.start"
    THINKING_DELTA = "thinking.delta"
    THINKING_END = "thinking.end"
    TOOL_CALLING = "tool.calling"
    TOOL_RESULT = "tool.result"
    SAFETY_CHECKED = "safety.checked"
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_RESOLVED = "approval.resolved"
    PLAN_PROPOSED = "plan.proposed"
    PLAN_APPROVED = "plan.approved"
    PLAN_REJECTED = "plan.rejected"
    TEXT_DELTA = "text.delta"
    TEXT_DONE = "text.done"
    ERROR = "error"
    DONE = "done"


class ToolRiskLevel(str, Enum):
    """工具风险等级。"""
    READ_ONLY = "read_only"
    WRITE = "write"
    DANGEROUS = "dangerous"


class SafetyVerdict(str, Enum):
    """安全校验结果。"""
    ALLOW = "allow"
    REQUIRE_CONFIRM = "require_confirm"
    BLOCK = "block"


# ── 核心 dataclass ──

@dataclass
class AgentEvent:
    """事件流基本单元。"""
    type: str
    session_id: str
    trace_id: str
    timestamp: float = field(default_factory=time.time)
    data: dict = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """工具元信息。parameters 为 JSON Schema 格式。"""
    name: str
    description: str
    parameters: dict
    risk_level: ToolRiskLevel = ToolRiskLevel.WRITE
    requires_privilege: bool = False


@dataclass
class ToolCall:
    """LLM 发起的工具调用请求。"""
    id: str
    name: str
    arguments: dict


@dataclass
class ToolResult:
    """工具执行结果。"""
    call_id: str
    tool_name: str
    success: bool
    output: str
    truncated: bool = False
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class TraceEntry:
    """审计日志条目。哈希链节点。"""
    trace_id: str
    event_type: str
    session_id: str
    timestamp: float
    data: dict
    prev_hash: str | None = None
    entry_hash: str | None = None


@dataclass
class LLMResponse:
    """LLM 调用结果。兼容 OpenAI Chat Completions 格式。"""
    content: str | None = None
    tool_calls: list = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Agent 运行时配置。由 config_envs/loader 加载并校验。

    安全约定：
    - llm_api_key 标记 repr=False，绝不出现在 repr()/日志中；
      它不应写入配置文件，只在运行时从环境变量（或 .env）注入。
    - dataclass_to_dict() 会序列化所有字段（含 api_key），因此持久化
      配置前必须经 trace_log.sanitizer 脱敏，或显式排除该字段。
    """
    llm_provider: str = "openai_compat"
    llm_endpoint: str = ""
    llm_model: str = "deepseek-chat"
    llm_max_tokens: int = 4096
    safety_policy: str = "default"
    execution_user: str = "nobody"
    trace_db_path: str = "runtime/sqlite/traces.db"
    max_tool_rounds: int = 0
    tool_timeout_seconds: int = 30
    # LLM 调用调优
    llm_temperature: float = 0.7
    llm_retry_count: int = 2          # 失败后重试次数（不含首次）
    llm_retry_delay: float = 1.0      # 重试基准间隔秒（指数退避基数）
    max_tool_calls_per_round: int = 0
    # 敏感字段：不进 repr、不应写配置文件
    llm_api_key: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        if not self.llm_endpoint:
            raise ValueError("llm_endpoint 不能为空")
        if self.max_tool_rounds < 0:
            raise ValueError("max_tool_rounds 必须 >= 0")
        if self.tool_timeout_seconds < 1:
            raise ValueError("tool_timeout_seconds 必须 >= 1")
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError("llm_temperature 必须在 0-2 之间")
        if self.llm_retry_count < 0:
            raise ValueError("llm_retry_count 不能为负")
        if self.llm_retry_delay < 0:
            raise ValueError("llm_retry_delay 不能为负")
        if self.max_tool_calls_per_round < 0:
            raise ValueError("max_tool_calls_per_round 必须 >= 0")


def dataclass_to_dict(obj) -> dict:
    """递归转换 dataclass 为 dict。"""
    return asdict(obj)


def dict_to_dataclass(d: dict, cls):
    """从 dict 构造 dataclass（浅层，支持 Enum 字段）。"""
    import dataclasses as _dc
    field_types = {f.name: f.type for f in _dc.fields(cls)}
    kwargs: dict = {}
    for k, v in d.items():
        if k in field_types:
            kwargs[k] = v
    return cls(**kwargs)
