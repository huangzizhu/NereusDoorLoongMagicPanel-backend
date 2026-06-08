"""统一错误码与异常类。"""

from enum import Enum


class ErrorCode(str, Enum):
    INTERNAL_ERROR = "E0001"
    INVALID_ARGUMENT = "E0002"
    TIMEOUT = "E0003"
    CONFIG_LOAD_FAILED = "E1001"
    CONFIG_INVALID = "E1002"
    LLM_CONNECTION_FAILED = "E2001"
    LLM_RESPONSE_MALFORMED = "E2002"
    LLM_RATE_LIMITED = "E2003"
    SAFETY_BLOCKED = "E3001"
    SAFETY_APPROVAL_REQUIRED = "E3002"
    INJECTION_DETECTED = "E3003"
    TOOL_NOT_FOUND = "E4001"
    TOOL_EXECUTION_FAILED = "E4002"
    TOOL_TIMEOUT = "E4003"
    EXEC_PERMISSION_DENIED = "E5001"
    EXEC_OUTPUT_TOO_LARGE = "E5002"


class AgentError(Exception):
    """Agent 异常基类。"""
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        detail: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail or {}
        super().__init__(f"[{code.value}] {message}")
