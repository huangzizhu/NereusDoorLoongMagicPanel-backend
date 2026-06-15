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
from agent.shared.types import EventType, LLMResponse, ToolRiskLevel
from agent.shared.id_gen import gen_tool_call_id
from agent.integration.event_stream import EventStream
from agent.safety.injection_detector import checkPromptInjection
from agent.safety.rule_engine import RuleEngine
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher
from ndlmpanel_agent.mcp.protocol.json_rpc import encodeRequest
from agent.agent_core.prompt_builder import PromptBuilder
from agent.llm_providers.base import LLMProvider
from agent.context_mgmt.compressor import closeOrphanToolCalls, compressHistory
from agent.trace_log.recorder import TraceRecorder
from agent.agent_router.router import AgentMode, getModePrompt
from agent.agent_router.plan_schema import planFromSubmitArgs, formatPlanForPrompt

_logger = logging.getLogger("ndlmpanel.agent_core")

MAX_TOOL_OUTPUT_CHARS_FOR_MODEL = 1200
MAX_TOTAL_TOOL_OUTPUT_CHARS_PER_ROUND = 6000

_LABEL_IDS = ["A", "B", "C", "D", "E", "F"]


def _normalize_choice_options(raw_options: list) -> list[dict]:
    """归一化 ask_choice 的 options 参数。

    LLM 可能输出不同格式，统一转为 [{"id": "A", "title": "...", "summary": ""}, ...]。

    支持的输入格式：
    - 字符串列表 ["Python", "Go"] → 自动赋予 A/B 编号
    - 对象列表 [{"id":"A","title":"Python"}] → 透传，补 summary
    - 混合格式 → 尽力归一化
    """
    if not raw_options:
        return []

    normalized: list[dict] = []
    for i, opt in enumerate(raw_options):
        if isinstance(opt, str):
            # 扁平字符串 → 自动编号
            label = _LABEL_IDS[i] if i < len(_LABEL_IDS) else str(i + 1)
            normalized.append({
                "id": label,
                "title": opt,
                "summary": "",
            })
        elif isinstance(opt, dict):
            # 对象格式 → 补默认值
            label = str(opt.get("id", _LABEL_IDS[i] if i < len(_LABEL_IDS) else str(i + 1)))
            normalized.append({
                "id": label,
                "title": str(opt.get("title", opt.get("id", f"选项{i+1}"))),
                "summary": str(opt.get("summary", "")),
            })
        else:
            # 兜底
            label = _LABEL_IDS[i] if i < len(_LABEL_IDS) else str(i + 1)
            normalized.append({
                "id": label,
                "title": str(opt),
                "summary": "",
            })
    return normalized


class LoopState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    PLAN_REVIEW = "plan_review"
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
        mode: AgentMode = AgentMode.AGENT,
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
        self._mode = mode
        self._pendingApprovals: dict[str, asyncio.Event] = {}
        self._approvalDecisions: dict[str, dict] = {}
        self._recorder: "TraceRecorder | None" = None
        # 两阶段 Plan 审批基础设施
        self._msgs: list[dict] = []
        self._pendingPlanApproval: tuple[str, asyncio.Event] | None = None
        self._planApprovalDecision: dict | None = None
        # 选择题（ask_choice）基础设施
        self._pendingChoice: tuple[str, asyncio.Event] | None = None
        self._choiceDecision: dict | None = None

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

    def _switchMode(self, mode: AgentMode) -> None:
        """切换运行模式（仅更新 mode 标记）。

        KV-Cache 优化：不再重新 setTools — tools 参数始终不变。
        模式门控通过 _injectModePrompt（前端文本约束）+ RuleEngine（后端硬规则）实现。
        """
        self._mode = mode

    def _injectModePrompt(self, messages: list[dict]) -> list[dict]:
        """在 LLM 调用前注入当前模式指令。

        插入位置：在最后一条 user 消息之前。
        所有模式统一注入（包括 AGENT），确保消息结构一致。

        注意：本方法不修改传入的 messages（self._msgs），
        仅构造注入后的副本发送给 LLM。self._msgs 保持与 DB history 一致。
        """
        result = list(messages)

        # 找到最后一条 role: user 消息的位置
        last_user_idx = -1
        for i in range(len(result) - 1, -1, -1):
            if result[i].get("role") == "user":
                last_user_idx = i
                break

        mode_msg = {"role": "system", "content": getModePrompt(self._mode)}

        if last_user_idx == -1:
            result.append(mode_msg)
        else:
            result.insert(last_user_idx, mode_msg)

        return result

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

    # ── 两阶段 Plan 审批 ──

    def approvePlan(self) -> bool:
        """批准当前待审批的计划。由外部（AgentSession）调用。

        Returns:
            True = 找到并放行；False = 无待审批计划
        """
        if self._pendingPlanApproval is None:
            return False
        plan_id, ev = self._pendingPlanApproval
        self._planApprovalDecision = {"approved": True, "reason": ""}
        ev.set()
        return True

    def rejectPlan(self, reason: str = "") -> bool:
        """拒绝当前待审批的计划。由外部（AgentSession）调用。

        Args:
            reason: 拒绝原因/修改建议

        Returns:
            True = 找到并拒绝；False = 无待审批计划
        """
        if self._pendingPlanApproval is None:
            return False
        plan_id, ev = self._pendingPlanApproval
        self._planApprovalDecision = {"approved": False, "reason": reason}
        ev.set()
        return True

    # ── 选择题（ask_choice）──

    def resolveChoice(self, selectionId: str, customInput: str = "") -> bool:
        """响应当前待回复的选择题。由外部（AgentSession）调用。

        Args:
            selectionId: 用户选择的选项 id（如 "A"），或 "__custom__"
            customInput: 当 selectionId 为 "__custom__" 时的自定义输入

        Returns:
            True = 找到并放行；False = 无待回复的选择题
        """
        if self._pendingChoice is None:
            return False
        choiceId, ev = self._pendingChoice
        self._choiceDecision = {
            "selection_id": selectionId,
            "custom_input": customInput,
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

        self._msgs = self._promptBuilder.build(
            userMessage, conversationHistory=conversationHistory,
        )

        # ── ToolCall 完整性校验 ──
        # 移除历史中残留的孤立 tool_calls，防止 LLM API 400
        # （发生场景：WS 断开导致审批残留）
        self._msgs = closeOrphanToolCalls(self._msgs)

        state = LoopState.THINKING
        roundCount = 0
        response: LLMResponse | None = None

        while state != LoopState.DONE and self._withinRoundLimit(roundCount):
            roundCount += 1

            if state == LoopState.THINKING:
                # 上下文压缩（token 预算保护）
                self._msgs = compressHistory(self._msgs, maxTokens=self._maxTokens)

                stream.emit(EventType.THINKING_START, {"round": roundCount})
                self._trace(traceId, sessionId, "llm.request",
                            {"round": roundCount, "msgs_count": len(self._msgs)})

                # ── 注入模式指令（所有模式统一注入，保持消息结构一致）──
                msgs_with_mode = self._injectModePrompt(self._msgs)

                # ── 真流式：逐 token 推送 TEXT_DELTA ──
                contentParts: list[str] = []
                toolCalls: list[dict] = []
                finishReason = ""
                usage: dict = {}

                async for chunk in self._llm.chatStream(msgs_with_mode):
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
                    # LLM 回复了纯文本（无 tool_calls）→ 本轮结束
                    # 在 ReAct 模式中，LLM 会在同一轮输出分析文本 + 调工具，
                    # 不会在纯文本之后的下轮再调工具。
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
                    # 拼装 LLM 输出文本（用于 tool 调用时填充 ai_reason 兜底）
                    preamble = "".join(contentParts).strip() if contentParts else ""
                    stream.emit(EventType.TOOL_CALLING, {
                        "tool_calls": toolCallsBlock,
                        "usage": response.usage,
                    })
                    self._msgs.append({
                        "role": "assistant",
                        "content": preamble or None,
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
                hasPendingPlan = False
                for index, tc in enumerate(response.tool_calls if response else []):
                    name = tc.get("name", "")
                    args = tc.get("arguments", {})
                    callId = tc.get("id", "") or gen_tool_call_id()

                    # ── 拦截 ask_choice（选择题交互）──
                    if name == "ask_choice":
                        question = str(args.get("question", ""))
                        raw_options = args.get("options", [])
                        allow_custom = True  # 强制允许自定义，让用户总有自由输入权

                        # 归一化：扁平字符串数组 → 对象数组
                        # LLM 有时输出 ["A", "B"] 而非 [{"id":"A","title":"A"}]
                        options = _normalize_choice_options(raw_options)

                        choiceResult = await self._waitForChoice(
                            stream, question, options, allow_custom,
                        )
                        # 构造 tool result 返回给 LLM
                        toolOutput = json.dumps(
                            choiceResult, ensure_ascii=False,
                        )
                        stream.emit(EventType.TOOL_RESULT, {
                            "call_id": callId, "tool_name": name,
                            "success": True, "output": toolOutput,
                        })
                        modelToolOutput = self._fitToolOutputForModel(
                            toolOutput,
                            MAX_TOOL_OUTPUT_CHARS_FOR_MODEL,
                            MAX_TOTAL_TOOL_OUTPUT_CHARS_PER_ROUND - totalToolOutputChars,
                        )
                        totalToolOutputChars += len(modelToolOutput)
                        self._msgs.append({
                            "role": "tool",
                            "tool_call_id": callId,
                            "content": modelToolOutput,
                        })
                        continue

                    # ── 拦截 submitPlan（两阶段 Plan 模式）──
                    if name == "submitPlan":
                        try:
                            plan = planFromSubmitArgs(args)
                        except ValueError as exc:
                            toolOutput = f"[计划格式错误] {exc}"
                            self._trace(traceId, sessionId, "plan.invalid", {
                                "error": str(exc),
                            })
                            stream.emit(EventType.TOOL_RESULT, {
                                "call_id": callId, "tool_name": name,
                                "success": False, "output": toolOutput,
                            })
                            self._msgs.append({
                                "role": "tool",
                                "tool_call_id": callId,
                                "content": toolOutput,
                            })
                            continue

                        # 发出 PLAN_PROPOSED 事件
                        from agent.agent_router.plan_schema import planToDict
                        self._trace(traceId, sessionId, "plan.proposed", {
                            "summary": plan.summary,
                            "step_count": len(plan.steps),
                        })
                        stream.emit(EventType.PLAN_PROPOSED, {
                            "plan": planToDict(plan),
                        })
                        # 向对话历史添加 tool response，保持 assistant(tool_calls)→tool 配对
                        # 避免后续 LLM 调用因 tool_calls 无响应而报 400
                        toolOutput = "[计划已提交，等待审批]"
                        stream.emit(EventType.TOOL_RESULT, {
                            "call_id": callId, "tool_name": name,
                            "success": True, "output": toolOutput,
                        })
                        self._msgs.append({
                            "role": "tool",
                            "tool_call_id": callId,
                            "content": toolOutput,
                        })

                        # 进入 PLAN_REVIEW 等待审批
                        hasPendingPlan = True
                        self._pendingPlanProps = (plan, callId)
                        break

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
                        self._msgs.append({
                            "role": "tool",
                            "tool_call_id": callId,
                            "content": toolOutput,
                        })
                        continue

                    risk = self._registry.getRiskLevel(name)
                    # 提取并剥离 AI 调用理由（仅 write/dangerous 工具有此参数）
                    ai_reason = args.pop("reason", "") if risk != ToolRiskLevel.READ_ONLY else ""

                    # ── 打回：write/dangerous 工具必须带 reason ──
                    if risk != ToolRiskLevel.READ_ONLY and not ai_reason:
                        toolOutput = (
                            f"[缺少 reason 参数] 调用 {name} 时必须填写 reason 参数说明调用原因和目的，"
                            f"请补充 reason 后重新调用。"
                        )
                        stream.emit(EventType.TOOL_RESULT, {
                            "call_id": callId, "tool_name": name,
                            "success": False, "output": toolOutput,
                        })
                        modelToolOutput = self._fitToolOutputForModel(
                            toolOutput,
                            MAX_TOOL_OUTPUT_CHARS_FOR_MODEL,
                            MAX_TOTAL_TOOL_OUTPUT_CHARS_PER_ROUND - totalToolOutputChars,
                        )
                        totalToolOutputChars += len(modelToolOutput)
                        self._msgs.append({
                            "role": "tool",
                            "tool_call_id": callId,
                            "content": modelToolOutput,
                        })
                        continue

                    verdict, reason = self._safety.checkToolCallWithReason(
                        name, risk, args, self._mode)

                    self._trace(traceId, sessionId, "safety.check", {
                        "tool": name, "risk": risk.value,
                        "verdict": verdict.value, "reason": reason,
                        "ai_reason": ai_reason,
                    })
                    stream.emit(EventType.SAFETY_CHECKED, {
                        "tool": name, "risk": risk.value,
                        "verdict": verdict.value, "reason": reason,
                        "ai_reason": ai_reason,
                    })

                    if verdict.value == "block":
                        toolOutput = "[阻塞] " + reason
                        # 先发 TOOL_RESULT 再发 ERROR
                        # ERROR 会导致 EventStream.__aiter__ 提前 break
                        # 不先发 TOOL_RESULT 会使数据库缺失 tool response
                        stream.emit(EventType.TOOL_RESULT, {
                            "call_id": callId, "tool_name": name,
                            "success": False, "output": toolOutput,
                        })
                        stream.emit(EventType.ERROR,
                                    {"message": toolOutput})
                        # 跳过公共的 TOOL_RESULT emit（下面的代码还会再发一次）
                        # 直接跳到 tool response 加入对话历史
                        self._trace(traceId, sessionId, "tool.result", {
                            "tool": name, "call_id": callId,
                            "output_len": len(toolOutput),
                        })
                        modelToolOutput = self._fitToolOutputForModel(
                            toolOutput,
                            MAX_TOOL_OUTPUT_CHARS_FOR_MODEL,
                            MAX_TOTAL_TOOL_OUTPUT_CHARS_PER_ROUND - totalToolOutputChars,
                        )
                        totalToolOutputChars += len(modelToolOutput)
                        self._msgs.append({
                            "role": "tool",
                            "tool_call_id": callId,
                            "content": modelToolOutput,
                        })
                        continue
                    elif verdict.value == "require_confirm":
                        self._trace(traceId, sessionId, "approval.requested", {
                            "tool": name, "args": {k: str(v)[:100] for k, v in args.items()},
                            "ai_reason": ai_reason,
                        })
                        toolOutput = await self._handleApproval(
                            stream, name, args, reason, ai_reason=ai_reason,
                            call_id=callId)
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
                    self._msgs.append({
                        "role": "tool",
                        "tool_call_id": callId,
                        "content": modelToolOutput,
                    })

                if hasPendingPlan:
                    state = LoopState.PLAN_REVIEW
                else:
                    state = LoopState.THINKING

            elif state == LoopState.PLAN_REVIEW:
                # 等待计划审批
                plan, callId = self._pendingPlanProps
                await self._waitForPlanApproval(stream, plan, callId)
                # 审批完成后无论批准/拒绝都回到 THINKING
                # （_waitForPlanApproval 内部已切换 mode 或注入反馈）
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
                              args: dict, reason: str,
                              ai_reason: str = "",
                              call_id: str = "") -> str:
        """高危操作人工审批闭环。

        发出 APPROVAL_REQUIRED 事件后，挂起等待外部 approve()/reject()，
        或在 approvalTimeout 后视为拒绝。只有获得批准才真正执行工具。

        Args:
            call_id: LLM 发起的 tool_call 原始 id（用于 WS 重连时匹配）
        """
        actionId = gen_tool_call_id()
        ev = asyncio.Event()
        self._pendingApprovals[actionId] = ev

        stream.emit(EventType.APPROVAL_REQUIRED, {
            "tool_name": name, "arguments": args,
            "action_id": actionId, "reason": reason,
            "ai_reason": ai_reason, "call_id": call_id,
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

    def _updateToolResponse(self, callId: str, newContent: str) -> None:
        """更新对话历史中指定 tool_call_id 的 tool 响应内容。
        
        用于 plan 审批后更新 "[计划已提交，等待审批]" 为实际结果。
        """
        for msg in self._msgs:
            if (msg.get("role") == "tool"
                    and msg.get("tool_call_id") == callId):
                msg["content"] = newContent
                break

    async def _waitForPlanApproval(self, stream: EventStream,
                                    plan, callId: str) -> None:
        """等待计划审批结果。

        发出 PLAN_PROPOSED 后挂起，等待外部 approvePlan()/rejectPlan()。
        批准后切换到 AGENT 模式并注入计划；
        拒绝后更新 tool 响应并注入反馈让 LLM 重新出计划。
        """
        planId = gen_tool_call_id()
        ev = asyncio.Event()
        self._pendingPlanApproval = (planId, ev)
        traceId = stream.traceId
        sessionId = stream._sessionId

        try:
            await asyncio.wait_for(ev.wait(), timeout=self._approvalTimeout)
        except asyncio.TimeoutError:
            self._pendingPlanApproval = None
            self._planApprovalDecision = None
            self._pendingPlanProps = None
            stream.emit(EventType.PLAN_REJECTED, {
                "reason": "审批超时",
                "call_id": callId,
            })
            self._trace(traceId, sessionId, "plan.rejected", {
                "reason": "审批超时",
            })
            # 更新 tool 响应
            self._updateToolResponse(callId, "[计划审批超时，已跳过]")
            # 超时后回退到 AGENT 模式，不阻断用户
            self._switchMode(AgentMode.AGENT)
            self._trace(traceId, sessionId, "mode.switch", {
                "from": AgentMode.PLAN.value,
                "to": AgentMode.AGENT.value,
                "reason": "plan_timeout",
            })
            self._msgs.append({
                "role": "system",
                "content": "计划审批超时，已切换到标准模式。请直接告诉用户你需要做什么。",
            })
            return

        decision = self._planApprovalDecision
        self._pendingPlanApproval = None
        self._planApprovalDecision = None
        self._pendingPlanProps = None

        if decision["approved"]:
            # 批准：切换到 AGENT 模式
            self._switchMode(AgentMode.AGENT)
            self._trace(traceId, sessionId, "mode.switch", {
                "from": AgentMode.PLAN.value,
                "to": AgentMode.AGENT.value,
                "reason": "plan_approved",
            })
            self._trace(traceId, sessionId, "plan.approved", {
                "summary": plan.summary,
                "step_count": len(plan.steps),
            })
            # 更新 tool 响应（让 LLM 看到审批结果）
            self._updateToolResponse(callId, "[计划已批准，开始执行]")
            plan_text = formatPlanForPrompt(plan)
            # 注入已批准的计划作为上下文
            self._msgs.append({
                "role": "system",
                "content": f"## 已批准的执行计划\n\n{plan_text}",
            })
            # 自动注入用户消息触发 LLM 开始执行
            self._msgs.append({
                "role": "user",
                "content": "开始实施",
            })
            from agent.agent_router.plan_schema import planToDict
            stream.emit(EventType.PLAN_APPROVED, {
                "plan": planToDict(plan),
                "call_id": callId,
                "tool_response": "[计划已批准，开始执行]",
            })
        else:
            # 拒绝：更新 tool 响应 + 注入反馈
            feedback = decision.get("reason", "") or "请调整计划"
            self._trace(traceId, sessionId, "plan.rejected", {
                "reason": feedback,
            })
            self._updateToolResponse(callId, f"[计划被拒绝] {feedback}")
            self._msgs.append({
                "role": "user",
                "content": f"计划需要修改：{feedback}\n\n请根据反馈重新生成计划。",
            })
            stream.emit(EventType.PLAN_REJECTED, {
                "reason": feedback,
                "call_id": callId,
            })

    async def _waitForChoice(
        self, stream: EventStream,
        question: str, options: list, allow_custom: bool,
    ) -> dict:
        """等待用户回答选择题（ask_choice）。

        发出 CHOICE_REQUIRED 事件后挂起，等待外部 resolveChoice()，
        或在 approvalTimeout 后视为超时。超时返回默认选择。

        Returns:
            dict: {"selection_id": str, "custom_input": str}
        """
        choiceId = gen_tool_call_id()
        ev = asyncio.Event()
        self._pendingChoice = (choiceId, ev)
        traceId = stream.traceId
        sessionId = stream._sessionId

        stream.emit(EventType.CHOICE_REQUIRED, {
            "question": question,
            "options": options,
            "allow_custom": allow_custom,
            "action_id": choiceId,
        })

        try:
            await asyncio.wait_for(ev.wait(), timeout=self._approvalTimeout)
        except asyncio.TimeoutError:
            self._pendingChoice = None
            self._choiceDecision = None
            self._trace(traceId, sessionId, "choice.timeout", {
                "question": question[:100],
            })
            stream.emit(EventType.CHOICE_RESOLVED, {
                "action_id": choiceId,
                "selection_id": "__timeout__",
                "custom_input": "",
            })
            return {"selection_id": "__timeout__", "custom_input": ""}

        decision = self._choiceDecision or {"selection_id": "__timeout__", "custom_input": ""}
        self._pendingChoice = None
        self._choiceDecision = None

        self._trace(traceId, sessionId, "choice.resolved", {
            "selection_id": decision["selection_id"],
            "has_custom": bool(decision.get("custom_input", "")),
        })
        stream.emit(EventType.CHOICE_RESOLVED, {
            "action_id": choiceId,
            "selection_id": decision["selection_id"],
            "custom_input": decision.get("custom_input", ""),
        })
        return {
            "selection_id": decision["selection_id"],
            "custom_input": decision.get("custom_input", ""),
        }

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
