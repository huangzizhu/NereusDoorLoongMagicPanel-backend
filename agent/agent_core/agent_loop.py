"""
Agent 核心循环 — 纯 asyncio 状态机。

替代 LangGraph，实现 ReAct 模式：
  THINK → ACT → OBSERVE → THINK → ... → DONE
"""
from __future__ import annotations
import asyncio
import json
import logging
from enum import Enum
from agent.shared.types import EventType, LLMResponse
from agent.shared.id_gen import gen_tool_call_id
from agent.integration.event_stream import EventStream
from agent.safety.injection_detector import checkPromptInjection
from agent.safety.rule_engine import RuleEngine
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher
from ndlmpanel_agent.mcp.protocol.json_rpc import encodeRequest
from agent.agent_core.prompt_builder import PromptBuilder
from agent.llm_providers.base import LLMProvider
from agent.context_mgmt.compressor import compressHistory
from agent.trace_log.recorder import TraceRecorder

_logger = logging.getLogger("ndlmpanel.agent_core")

MAX_TOOL_OUTPUT_CHARS_FOR_MODEL = 1200
MAX_TOTAL_TOOL_OUTPUT_CHARS_PER_ROUND = 6000


class LoopState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    DONE = "done"


class AgentCore:
    """Agent 核心循环引擎。"""

    def __init__(
        self,
        llmProvider: LLMProvider,
        registry: ToolRegistry,
        dispatcher: McpDispatcher,
        safety: RuleEngine,
        promptBuilder: PromptBuilder,
        maxRounds: int = 0,
        approvalTimeout: float = 300.0,
        maxTokens: int = 60000,
        maxToolCallsPerRound: int = 0,
    ):
        self._llm = llmProvider
        self._registry = registry
        self._dispatcher = dispatcher
        self._safety = safety
        self._promptBuilder = promptBuilder
        self._maxRounds = maxRounds
        self._maxTokens = maxTokens
        self._maxToolCallsPerRound = maxToolCallsPerRound
        self._approvalTimeout = approvalTimeout
        self._pendingApprovals: dict[str, asyncio.Event] = {}
        self._approvalDecisions: dict[str, dict] = {}
        self._recorder: "TraceRecorder | None" = None

    def setRecorder(self, recorder: "TraceRecorder") -> None:
        """注入 TraceRecorder，在循环中自动记录关键事件。"""
        self._recorder = recorder

    def approve(self, actionId: str) -> bool:
        """批准某个待审批动作。由外部（AgentSession）调用。

        Returns:
            True = 找到并放行该动作；False = 无此 action_id（可能已超时/已处理）
        """
        return self._resolveApproval(actionId, approved=True, reason="")

    def reject(self, actionId: str, reason: str = "") -> bool:
        """拒绝某个待审批动作。由外部（AgentSession）调用。"""
        return self._resolveApproval(actionId, approved=False, reason=reason)

    def _resolveApproval(self, actionId: str, approved: bool,
                         reason: str) -> bool:
        ev = self._pendingApprovals.get(actionId)
        if ev is None:
            return False
        self._approvalDecisions[actionId] = {
            "approved": approved, "reason": reason,
        }
        ev.set()
        return True

    async def run(
        self,
        userMessage: str,
        stream: EventStream,
        conversationHistory: list[dict] | None = None,
    ) -> None:
        """运行 Agent 循环。

        本方法保证无论成功、异常还是被取消，都会向 stream 发出终止事件
        （DONE 或 ERROR），避免消费端 `async for` 永久挂起。
        """
        try:
            await self._runLoop(userMessage, stream, conversationHistory)
        except asyncio.CancelledError:
            stream.emit(EventType.ERROR, {"message": "会话已取消"})
            raise
        except Exception as exc:
            _logger.exception("AgentCore.run 异常: %s", exc)
            stream.emit(EventType.ERROR, {"message": f"内部错误: {exc}"})

    async def _runLoop(
        self,
        userMessage: str,
        stream: EventStream,
        conversationHistory: list[dict] | None,
    ) -> None:
        traceId = stream.traceId
        sessionId = stream._sessionId

        # 注入检测 → trace
        if checkPromptInjection(userMessage):
            self._trace(traceId, sessionId, "injection.detected",
                        {"input": userMessage[:200]})
            stream.emit(EventType.ERROR, {"message": "检测到 Prompt Injection"})
            stream.emit(EventType.DONE)
            return
        self._trace(traceId, sessionId, "input.received",
                    {"input": userMessage[:200]})

        msgs = self._promptBuilder.build(
            userMessage, conversationHistory=conversationHistory,
        )
        state = LoopState.THINKING
        roundCount = 0
        response: LLMResponse | None = None

        while state != LoopState.DONE and self._withinRoundLimit(roundCount):
            roundCount += 1

            if state == LoopState.THINKING:
                # 上下文压缩（token 预算保护）
                msgs = compressHistory(msgs, maxTokens=self._maxTokens)

                stream.emit(EventType.THINKING_START, {"round": roundCount})
                self._trace(traceId, sessionId, "llm.request",
                            {"round": roundCount, "msgs_count": len(msgs)})

                # ── 真流式：逐 token 推送 TEXT_DELTA ──
                contentParts: list[str] = []
                toolCalls: list[dict] = []
                finishReason = ""
                usage: dict = {}

                async for chunk in self._llm.chatStream(msgs):
                    if chunk.content:
                        contentParts.append(chunk.content)
                        # 立即推送文本 delta（真正的流式输出）
                        for line in self._splitLines(chunk.content):
                            stream.emit(EventType.TEXT_DELTA, {"content": line})
                            await asyncio.sleep(0)
                    if chunk.tool_calls:
                        toolCalls.extend(chunk.tool_calls)
                    if chunk.usage:
                        usage = chunk.usage
                    if chunk.finish_reason:
                        finishReason = chunk.finish_reason

                # 重建完整响应
                response = LLMResponse(
                    content="".join(contentParts) if contentParts else None,
                    tool_calls=toolCalls,
                    finish_reason=finishReason or "stop",
                    usage=usage,
                )

                self._trace(traceId, sessionId, "llm.response", {
                    "round": roundCount,
                    "finish_reason": response.finish_reason,
                    "usage": response.usage,
                    "tc_count": len(response.tool_calls),
                })

                if response.content and not response.tool_calls:
                    stream.emit(EventType.TEXT_DONE, {
                        "usage": response.usage,
                    })
                    state = LoopState.DONE

                elif response.tool_calls:
                    toolCallsBlock = []
                    for tc in response.tool_calls:
                        toolCallsBlock.append({
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": json.dumps(
                                    tc.get("arguments", {}),
                                    ensure_ascii=False,
                                ),
                            }
                        })
                    # 发出 TOOL_CALLING 事件，让消费者可以持久化
                    stream.emit(EventType.TOOL_CALLING, {
                        "tool_calls": toolCallsBlock,
                        "usage": response.usage,
                    })
                    msgs.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": toolCallsBlock,
                    })
                    state = LoopState.EXECUTING

                else:
                    stream.emit(EventType.TEXT_DELTA,
                                {"content": "(AgentCore: 空响应)"})
                    stream.emit(EventType.DONE)
                    state = LoopState.DONE

            elif state == LoopState.EXECUTING:
                totalToolOutputChars = 0
                for index, tc in enumerate(response.tool_calls if response else []):
                    name = tc.get("name", "")
                    args = tc.get("arguments", {})
                    callId = tc.get("id", "") or gen_tool_call_id()

                    if self._maxToolCallsPerRound > 0 and index >= self._maxToolCallsPerRound:
                        toolOutput = (
                            "[跳过] 本轮工具调用数量超过上限 "
                            f"{self._maxToolCallsPerRound}，请分批继续测试。"
                        )
                        self._trace(traceId, sessionId, "tool.skipped", {
                            "tool": name, "call_id": callId,
                            "reason": "too_many_tool_calls",
                        })
                        stream.emit(EventType.TOOL_RESULT, {
                            "call_id": callId, "tool_name": name,
                            "success": False, "output": toolOutput,
                        })
                        msgs.append({
                            "role": "tool",
                            "tool_call_id": callId,
                            "content": toolOutput,
                        })
                        continue

                    risk = self._registry.getRiskLevel(name)
                    verdict, reason = self._safety.checkToolCallWithReason(
                        name, risk, args)

                    self._trace(traceId, sessionId, "safety.check", {
                        "tool": name, "risk": risk.value,
                        "verdict": verdict.value, "reason": reason,
                    })
                    stream.emit(EventType.SAFETY_CHECKED, {
                        "tool": name, "risk": risk.value,
                        "verdict": verdict.value, "reason": reason,
                    })

                    if verdict.value == "block":
                        toolOutput = "[阻塞] " + reason
                        stream.emit(EventType.ERROR,
                                    {"message": toolOutput})
                    elif verdict.value == "require_confirm":
                        self._trace(traceId, sessionId, "approval.requested", {
                            "tool": name, "args": {k: str(v)[:100] for k, v in args.items()},
                        })
                        toolOutput = await self._handleApproval(
                            stream, name, args, reason)
                    else:
                        toolOutput = await self._executeTool(name, args)

                    self._trace(traceId, sessionId, "tool.result", {
                        "tool": name, "call_id": callId,
                        "output_len": len(toolOutput),
                    })
                    stream.emit(EventType.TOOL_RESULT, {
                        "call_id": callId, "tool_name": name,
                        "success": True, "output": toolOutput[:2000],
                    })

                    modelToolOutput = self._fitToolOutputForModel(
                        toolOutput,
                        MAX_TOOL_OUTPUT_CHARS_FOR_MODEL,
                        MAX_TOTAL_TOOL_OUTPUT_CHARS_PER_ROUND - totalToolOutputChars,
                    )
                    totalToolOutputChars += len(modelToolOutput)
                    msgs.append({
                        "role": "tool",
                        "tool_call_id": callId,
                        "content": modelToolOutput,
                    })

                state = LoopState.THINKING

        if self._maxRounds > 0 and roundCount >= self._maxRounds:
            stream.emit(EventType.TEXT_DELTA,
                        {"content": "\n[达到最大轮次 " + str(self._maxRounds) + "]"})
        self._trace(traceId, sessionId, "session.done",
                    {"rounds": roundCount})
        stream.emit(EventType.DONE)

    def _withinRoundLimit(self, roundCount: int) -> bool:
        if self._maxRounds == 0:
            return True
        return roundCount < self._maxRounds

    async def _handleApproval(self, stream: EventStream, name: str,
                              args: dict, reason: str) -> str:
        """高危操作人工审批闭环。

        发出 APPROVAL_REQUIRED 事件后，挂起等待外部 approve()/reject()，
        或在 approvalTimeout 后视为拒绝。只有获得批准才真正执行工具。
        """
        actionId = gen_tool_call_id()
        ev = asyncio.Event()
        self._pendingApprovals[actionId] = ev

        stream.emit(EventType.APPROVAL_REQUIRED, {
            "tool_name": name, "arguments": args,
            "action_id": actionId, "reason": reason,
        })

        try:
            await asyncio.wait_for(ev.wait(), timeout=self._approvalTimeout)
        except asyncio.TimeoutError:
            self._pendingApprovals.pop(actionId, None)
            self._approvalDecisions.pop(actionId, None)
            stream.emit(EventType.APPROVAL_RESOLVED, {
                "action_id": actionId, "approved": False,
                "reason": "审批超时",
            })
            return f"[审批超时] 工具 {name} 未在规定时间内获得批准，已跳过执行"

        decision = self._approvalDecisions.pop(actionId, {"approved": False})
        self._pendingApprovals.pop(actionId, None)

        stream.emit(EventType.APPROVAL_RESOLVED, {
            "action_id": actionId,
            "approved": decision["approved"],
            "reason": decision.get("reason", ""),
        })

        if decision["approved"]:
            return await self._executeTool(name, args)
        rejectReason = decision.get("reason", "") or "用户拒绝执行"
        return f"[用户拒绝] 工具 {name} 未执行。原因: {rejectReason}"

    def _trace(self, traceId: str, sessionId: str,
               eventType: str, data: dict) -> None:
        """记录审计事件（若已注入 TraceRecorder）。"""
        if self._recorder is not None:
            self._recorder.record(traceId, sessionId, eventType, data)

    async def _executeTool(self, name: str, args: dict) -> str:
        loop = asyncio.get_running_loop()
        reqId = gen_tool_call_id()
        mcpReq = encodeRequest("tools/call",
                               {"name": name, "arguments": args},
                               reqId)
        raw = await loop.run_in_executor(None, self._dispatcher.handle, mcpReq)
        data = json.loads(raw)
        result = data.get("result", {})
        content = result.get("content", [{}])
        return content[0].get("text", str(result))

    @staticmethod
    def _fitToolOutputForModel(
        text: str,
        perToolLimit: int,
        remainingRoundBudget: int,
    ) -> str:
        if remainingRoundBudget <= 0:
            return "[工具输出省略] 本轮工具结果总量已达到回传模型上限。"
        limit = max(0, min(perToolLimit, remainingRoundBudget))
        if len(text) <= limit:
            return text
        if limit <= 80:
            return "[工具输出截断] 输出过长。"
        return (
            text[: limit - 60]
            + f"\n...[工具输出截断，原始长度 {len(text)} 字符]"
        )

    @staticmethod
    def _splitLines(text: str, maxLen: int = 40) -> list[str]:
        if not text:
            return []
        parts = []
        lines = text.split("\n")
        for i, line in enumerate(lines):
            isLast = (i == len(lines) - 1)
            if len(line) <= maxLen:
                parts.append(line + ("" if isLast else "\n"))
            else:
                for j in range(0, len(line), maxLen):
                    parts.append(line[j:j+maxLen])
        return parts
