"""
SSE (Server-Sent Events) 流式解析器。

不依赖外部库，逐行解析 data: 行。
"""
from __future__ import annotations
import json


def parseSseStream(lines: list[str]) -> list[dict]:
    """解析完整的 SSE 响应体为 dict 列表。

    每行格式：
      data: {"id":"...","choices":[{"delta":{"content":"..."}}]}
      data: [DONE]

    Returns:
        [{"delta": {"content": "..."}, "finish_reason": "stop"}, ...]
    """
    events: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line.startswith("data: "):
            continue
        payload = line[6:]  # 去掉 "data: "
        if payload == "[DONE]":
            break
        try:
            obj = json.loads(payload)
            choice = obj.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            finish = choice.get("finish_reason") or ""
            events.append({
                "delta": delta,
                "finish_reason": finish,
                "usage": obj.get("usage"),
            })
        except json.JSONDecodeError:
            continue
    return events


def mergeSseDeltas(events: list[dict]) -> dict:
    """合并 SSE 增量事件为完整 LLMResponse。

    Returns:
        可传给 LLMResponse(**result) 的 dict
    """
    contentParts: list[str] = []
    toolCalls: dict[int, dict] = {}
    finishReason = "stop"
    usage = {}

    for ev in events:
        delta = ev.get("delta", {})
        if "content" in delta and delta["content"]:
            contentParts.append(delta["content"])

        # tool_calls 增量
        for tc in delta.get("tool_calls", []):
            idx = tc.get("index", 0)
            if idx not in toolCalls:
                toolCalls[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
            if "id" in tc and tc["id"]:
                toolCalls[idx]["id"] = tc["id"]
            if "function" in tc:
                if "name" in tc["function"] and tc["function"]["name"]:
                    toolCalls[idx]["function"]["name"] = tc["function"]["name"]
                if "arguments" in tc["function"]:
                    toolCalls[idx]["function"]["arguments"] += tc["function"]["arguments"]

        if ev.get("finish_reason"):
            finishReason = ev["finish_reason"]
        if ev.get("usage"):
            usage = ev["usage"]

    content = "".join(contentParts) or None
    tcList = []
    for idx in sorted(toolCalls.keys()):
        tc = toolCalls[idx]
        if tc["id"] and tc["function"]["name"]:
            args = {}
            argStr = tc["function"]["arguments"]
            if argStr:
                try:
                    args = json.loads(argStr)
                except json.JSONDecodeError:
                    args = {"_raw": argStr}
            tcList.append({"id": tc["id"], "name": tc["function"]["name"], "arguments": args})

    return {"content": content, "tool_calls": tcList,
            "finish_reason": finishReason, "usage": usage}
