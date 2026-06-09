"""
OpenAI 风格适配器。

将 Agent 内部事件转为 OpenAI Streaming SSE 格式，
供后端 FastAPI 直接流式输出。
"""
from __future__ import annotations
import json
from agent.shared.types import AgentEvent, EventType


class OpenAIAdapter:
    """OpenAI Chat Completions 风格 SSE 格式化。"""

    @staticmethod
    def formatSse(event: AgentEvent) -> str:
        """将 AgentEvent 转为 OpenAI 风格 SSE data: 行。

        Returns:
            "data: {...}\n\n" 或 "data: [DONE]\n\n"
        """
        if event.type == EventType.DONE:
            return "data: [DONE]\n\n"

        payload = {
            "id": event.trace_id,
            "object": "agent.event",
            "created": int(event.timestamp),
            "type": event.type,
        }

        if event.type == EventType.THINKING_DELTA:
            payload["delta"] = {"content": event.data.get("content", "")}
        elif event.type == EventType.TEXT_DELTA:
            payload["delta"] = {"content": event.data.get("content", "")}
        elif event.type == EventType.TOOL_CALLING:
            payload["tool_call"] = {
                "id": event.data.get("id", ""),
                "name": event.data.get("name", ""),
                "arguments": event.data.get("arguments", {}),
            }
        elif event.type == EventType.TOOL_RESULT:
            payload["tool_result"] = event.data
        elif event.type == EventType.APPROVAL_REQUIRED:
            payload["approval"] = event.data
        elif event.type == EventType.ERROR:
            payload["error"] = event.data

        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
