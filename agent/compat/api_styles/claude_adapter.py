"""
Claude/Anthropic 风格适配器。

将 Agent 内部事件转为 Claude Messages API 流式格式：
  event: content_block_start / content_block_delta / message_stop
"""
from __future__ import annotations
import json
from agent.shared.types import AgentEvent, EventType


def _jd(obj) -> str:
    """json.dumps with ensure_ascii=False."""
    return json.dumps(obj, ensure_ascii=False)


class ClaudeAdapter:
    """Anthropic Claude Messages 风格 SSE 格式化。"""

    _msgIdCounter: int = 0
    _blockIdx: int = 0

    @classmethod
    def formatSse(cls, event: AgentEvent) -> str:
        lines: list[str] = []

        if event.type == EventType.SESSION_CREATED:
            cls._msgIdCounter = 0
            cls._blockIdx = 0
            return ""

        if event.type == EventType.THINKING_DELTA:
            if cls._blockIdx == 0 or event.data.get("_block_start", False):
                cls._blockIdx += 1
                lines.append("event: content_block_start")
                lines.append(_jd({
                    "type": "content_block_start",
                    "index": cls._blockIdx,
                    "content_block": {"type": "thinking", "thinking": ""}
                }))
            lines.append("event: content_block_delta")
            lines.append(_jd({
                "type": "content_block_delta",
                "index": cls._blockIdx,
                "delta": {"type": "thinking_delta",
                          "thinking": event.data.get("content", "")}
            }))
            return cls._join(lines)

        if event.type == EventType.TEXT_DELTA:
            if cls._blockIdx == 0 or event.data.get("_block_start", False):
                cls._blockIdx += 1
                lines.append("event: content_block_start")
                lines.append(_jd({
                    "type": "content_block_start",
                    "index": cls._blockIdx,
                    "content_block": {"type": "text", "text": ""}
                }))
            lines.append("event: content_block_delta")
            lines.append(_jd({
                "type": "content_block_delta",
                "index": cls._blockIdx,
                "delta": {"type": "text_delta",
                          "text": event.data.get("content", "")}
            }))
            return cls._join(lines)

        if event.type == EventType.TOOL_CALLING:
            cls._blockIdx += 1
            lines.append("event: content_block_start")
            lines.append(_jd({
                "type": "content_block_start",
                "index": cls._blockIdx,
                "content_block": {
                    "type": "tool_use",
                    "id": event.data.get("id", ""),
                    "name": event.data.get("name", ""),
                    "input": event.data.get("arguments", {}),
                }
            }))
            return cls._join(lines)

        if event.type == EventType.TOOL_RESULT:
            cls._blockIdx += 1
            lines.append("event: content_block_start")
            lines.append(_jd({
                "type": "content_block_start",
                "index": cls._blockIdx,
                "content_block": {
                    "type": "tool_result",
                    "tool_use_id": event.data.get("call_id", ""),
                    "content": event.data.get("output", ""),
                    "is_error": not event.data.get("success", True),
                }
            }))
            return cls._join(lines)

        if event.type == EventType.DONE:
            lines.append("event: message_stop")
            lines.append(_jd({"type": "message_stop"}))
            cls._msgIdCounter += 1
            cls._blockIdx = 0
            return cls._join(lines)

        if event.type == EventType.ERROR:
            cls._blockIdx += 1
            lines.append("event: content_block_start")
            lines.append(_jd({
                "type": "content_block_start",
                "index": cls._blockIdx,
                "content_block": {
                    "type": "text",
                    "text": f"[Error] {event.data.get('message', 'unknown')}"
                }
            }))
            return cls._join(lines)

        return ""

    @staticmethod
    def _join(lines: list[str]) -> str:
        return "\n".join(lines) + "\n\n"
