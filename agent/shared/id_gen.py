"""ID 生成工具。"""

import secrets
import uuid


def gen_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:12]}"


def gen_trace_id() -> str:
    return f"trace_{uuid.uuid4().hex[:16]}"


def gen_tool_call_id() -> str:
    return f"tc_{secrets.token_hex(6)}"
