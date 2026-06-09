"""上下文压缩器 — 滑窗 + LLM 摘要。

当对话历史超过 token 预算时，
保留最近 N 轮完整对话，更早的消息压缩为摘要。
"""
from __future__ import annotations


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
            # 提取工具名
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
