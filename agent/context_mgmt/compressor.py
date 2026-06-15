"""上下文压缩器 — 滑窗 + LLM 摘要。

当对话历史超过 token 预算时，
保留最近 N 轮完整对话，更早的消息压缩为摘要。
"""
from __future__ import annotations

import logging

_logger = logging.getLogger("ndlmpanel.context_mgmt")


def closeOrphanToolCalls(messages: list[dict]) -> list[dict]:
    """移除没有对应 tool 响应的孤立 assistant tool_calls 消息。

    场景：WS 断开导致审批残留，assistant 发了 tool_calls 但未被执行。
    如果不清理，LLM API 会报 400：
      "Invalid parameter: messages with role 'assistant' must have a response..."

    策略（两层防御）：
      第一层：遍历时跟踪 tool_call_id → 检查后续是否有匹配的 tool 响应
      第二层：如果遍历完还有 pending 的 tool_calls → 回滚删除

    Args:
        messages: OpenAI 格式消息列表

    Returns:
        清理后的消息列表（不修改输入）
    """
    if not messages:
        return messages

    result: list[dict] = []
    pending_tc = False
    tc_ids: set[str] = set()
    responded_ids: set[str] = set()
    orphan_insertion_index: int | None = None

    for msg in messages:
        role = msg.get("role", "")

        if role == "assistant" and msg.get("tool_calls"):
            pending_tc = True
            result.append(msg)
            orphan_insertion_index = len(result) - 1
            tc_ids = {tc.get("id", "") for tc in msg["tool_calls"] if tc.get("id")}
            responded_ids = set()
            continue

        if role == "tool" and pending_tc:
            call_id = msg.get("tool_call_id", "")
            if call_id:
                responded_ids.add(call_id)
            result.append(msg)
            if tc_ids and tc_ids == responded_ids:
                pending_tc = False
                orphan_insertion_index = None
            continue

        if pending_tc and role == "assistant":
            _logger.warning(
                "closeOrphanToolCalls: 发现孤立 tool_calls (tc=%s, responded=%s), 已移除",
                tc_ids, responded_ids,
            )
            if orphan_insertion_index is not None:
                result = result[:orphan_insertion_index]
                orphan_insertion_index = None
            pending_tc = False
            tc_ids = set()
            responded_ids = set()
            result.append(msg)
            continue

        if pending_tc:
            if orphan_insertion_index is not None:
                _logger.warning(
                    "closeOrphanToolCalls: 链中断于 role=%s, 移除孤立 tool_calls",
                    role,
                )
                result = result[:orphan_insertion_index]
                orphan_insertion_index = None
            pending_tc = False
            tc_ids = set()
            responded_ids = set()
            result.append(msg)
            continue

        result.append(msg)

    if pending_tc and orphan_insertion_index is not None:
        _logger.warning(
            "closeOrphanToolCalls: 末尾孤立 tool_calls (tc=%s, responded=%s), 已移除",
            tc_ids, responded_ids,
        )
        result = result[:orphan_insertion_index]

    return result


def compressHistory(
    messages: list[dict],
    maxRecent: int = 6,
    maxTokens: int = 40000,
    compressionThreshold: float = 0.8,
) -> list[dict]:
    """压缩对话历史。

    策略：
    1. 保留 system 消息（永远不压缩）
    2. 保留最近 maxRecent 条 user/assistant/tool 消息
    3. 更早的消息替换为一条摘要（如果需要）

    Args:
        messages: 完整消息列表
        maxRecent: 保留的最近消息数
        maxTokens: token 预算（粗略估算：1 token ≈ 2 chars）
        compressionThreshold: 达到预算百分比后开始压缩

    Returns:
        压缩后的消息列表
    """
    if not messages:
        return messages

    # 分离 system 消息
    systemMsgs = [m for m in messages if m.get("role") == "system"]
    otherMsgs = [m for m in messages if m.get("role") != "system"]
    units = _groupMessages(otherMsgs)

    # 估算总 token 数
    totalChars = sum(len(str(m.get("content", ""))) for m in otherMsgs)
    estimatedTokens = totalChars // 2

    compressionThreshold = min(max(compressionThreshold, 0.0), 1.0)
    thresholdTokens = int(maxTokens * compressionThreshold)
    if estimatedTokens <= thresholdTokens:
        return messages

    # 压缩：保留最近 N 组消息，避免拆散 assistant tool_calls 和后续 tool 消息
    recentUnits = units[-maxRecent:]
    olderUnits = units[:-maxRecent]
    recent = [msg for unit in recentUnits for msg in unit]
    older = [msg for unit in olderUnits for msg in unit]

    if older:
        # 生成摘要
        summary = _buildSummary(older)
        result = systemMsgs + [
            {"role": "system", "content": f"[对话历史摘要] {summary}"}
        ] + recent
    else:
        result = systemMsgs + recent

    return result


def _buildSummary(messages: list[dict]) -> str:
    """从旧消息生成简要摘要（纯规则，不调用 LLM）。"""
    topics = []
    toolNames = []
    for m in messages:
        role = m.get("role", "")
        content = str(m.get("content", ""))[:80]
        if role == "user" and content:
            topics.append(content[:50])
        elif role == "tool":
            tcId = m.get("tool_call_id", "")
            toolNames.append(tcId)

    topicStr = "; ".join(topics[:5]) if topics else "无"
    toolStr = f"使用了 {len(toolNames)} 个工具" if toolNames else ""
    return f"用户之前询问了: {topicStr}. {toolStr}.".strip()


def _groupMessages(messages: list[dict]) -> list[list[dict]]:
    """将消息按工具调用链分组，避免压缩时破坏协议顺序。"""
    grouped: list[list[dict]] = []
    index = 0

    while index < len(messages):
        current = messages[index]
        role = current.get("role")

        if role == "assistant" and current.get("tool_calls"):
            unit = [current]
            index += 1
            while index < len(messages) and messages[index].get("role") == "tool":
                unit.append(messages[index])
                index += 1
            grouped.append(unit)
            continue

        grouped.append([current])
        index += 1

    return grouped
