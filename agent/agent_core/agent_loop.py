"""
Agent 核心循环 — 纯 asyncio 状态机。

替代 LangGraph，实现 ReAct 模式：
  THINK → ACT → OBSERVE → THINK → ... → DONE
"""
from __future__ import annotations
import asyncio
import json
import logging
import re
from collections.abc import Callable
from enum import Enum
from agent.shared.types import EventType, LLMResponse, ToolRiskLevel
from agent.shared.id_gen import gen_tool_call_id
from agent.integration.event_stream import EventStream
from agent.safety.injection_detector import checkPromptInjection
from agent.safety.canary import CanaryManager
from agent.safety.llm_classifier import InjectionClassifier
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
        contextWindow: int = 1048576,
        maxToolCallsPerRound: int = 0,
        mode: AgentMode = AgentMode.AGENT,
        autoApproveScheduled: bool = False,
        nonInteractiveApprovals: bool = False,
        scheduledApprovalPolicy: dict | None = None,
        autoRunTaskId: int | None = None,
        autoRunSource: str = "",
        autoRunGuidance: str = "",
        injectionClassifier: InjectionClassifier | None = None,
        canary: CanaryManager | None = None,
        alertSink: Callable[[int, str], None] | None = None,
    ):
        self._llm = llmProvider
        self._registry = registry
        self._dispatcher = dispatcher
        self._safety = safety
        self._promptBuilder = promptBuilder
        self._injectionClassifier = injectionClassifier
        self._canary = canary
        # 告警回调：level(0 Info/1 Warning/2 Error), message → 写入 alert_events
        self._alertSink = alertSink
        self._maxRounds = maxRounds
        self._maxTokens = maxTokens
        self._contextWindow = contextWindow
        self._maxToolCallsPerRound = maxToolCallsPerRound
        self._approvalTimeout = approvalTimeout
        self._mode = mode
        self._autoApproveScheduled = autoApproveScheduled
        self._nonInteractiveApprovals = nonInteractiveApprovals
        self._scheduledApprovalPolicy = scheduledApprovalPolicy or {}
        # ── 无人值守运行上下文（定时任务/巡检）──
        self._autoRunTaskId = autoRunTaskId
        self._autoRunSource = autoRunSource
        self._autoRunGuidance = autoRunGuidance
        # ── 后台超时控制（S6：WS 解耦后 Agent 在后台独立运行）──
        self._maxBackgroundTime: float = 1800.0   # 30 分钟最大后台运行时间
        self._startTime: float | None = None
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

        mode_content = getModePrompt(self._mode)
        if self._autoRunGuidance:
            mode_content = mode_content + "\n\n" + self._autoRunGuidance
        mode_msg = {"role": "system", "content": mode_content}

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
                        {"source": "regex", "input": userMessage[:200]})
            self._emitAlert(
                1, "检测到用户输入包含提示词注入特征（正则快筛），已拒绝")
            stream.emit(EventType.ERROR, {"message": "检测到 Prompt Injection"})
            stream.emit(EventType.DONE)
            return

        # ── 组合拳第二层：第三方 LLM 分类器（抽检/全检测）──
        if (self._injectionClassifier is not None
                and self._injectionClassifier.shouldCheck()):
            verdict = await self._injectionClassifier.classify(userMessage)
            if verdict.checked and verdict.injection:
                self._trace(traceId, sessionId, "injection.detected", {
                    "source": "classifier",
                    "confidence": verdict.confidence,
                    "reason": verdict.reason,
                    "input": userMessage[:200],
                })
                self._emitAlert(
                    2,
                    f"检测到用户输入提示词注入（LLM 分类器，置信度 "
                    f"{verdict.confidence:.2f}）",
                )
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

        # ── 后台超时计时起点 ──
        import time as _time
        self._startTime = _time.time()

        while state != LoopState.DONE and self._withinRoundLimit(roundCount):
            roundCount += 1

            # ── 后台超时检查（最大时间 + 最大轮次）──
            elapsed = _time.time() - (self._startTime or _time.time())
            if self._maxBackgroundTime > 0 and elapsed > self._maxBackgroundTime:
                stream.emit(EventType.TEXT_DELTA, {
                    "content": (
                        "\n[Agent 运行时间已达上限（"
                        + str(int(elapsed // 60))
                        + " 分钟），会话暂停。你可以发送消息继续。]"
                    ),
                })
                self._trace(traceId, sessionId, "background.timeout", {
                    "elapsed_seconds": elapsed,
                    "rounds": roundCount,
                })
                break

            if state == LoopState.THINKING:
                # 上下文压缩（token 预算保护）
                self._msgs = compressHistory(self._msgs, maxTokens=self._contextWindow)

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

                # ── 金丝雀输出侧检测：模型回复（文本+工具参数）泄露令牌 → 拦截并轮换 ──
                if self._canary is not None and self._canary.enabled:
                    out_text = response.content or ""
                    for tc in toolCalls:
                        out_text += json.dumps(
                            tc.get("arguments", {}), ensure_ascii=False)
                    if self._canary.leakedIn(out_text):
                        self._trace(traceId, sessionId, "canary.leaked", {
                            "round": roundCount,
                            "content_len": len(response.content or ""),
                            "tool_calls": len(toolCalls),
                        })
                        self._canary.rotate()
                        self._emitAlert(
                            2,
                            "检测到系统提示词泄露（金丝雀令牌泄露），"
                            "已拦截本轮并轮换安全令牌",
                        )
                        stream.emit(EventType.ERROR, {
                            "message": "检测到系统提示词泄露（金丝雀令牌泄露），"
                                       "已中止本轮并轮换安全令牌。",
                        })
                        self._msgs.append({
                            "role": "system",
                            "content": "检测到提示词注入（金丝雀令牌泄露），已中止执行。",
                        })
                        state = LoopState.DONE
                        break

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
                        await self._appendToolMessage(
                            callId, modelToolOutput, traceId, sessionId)
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
                            await self._appendToolMessage(
                                callId, toolOutput, traceId, sessionId)
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
                        await self._appendToolMessage(
                            callId, toolOutput, traceId, sessionId)

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
                        await self._appendToolMessage(
                            callId, toolOutput, traceId, sessionId)
                        continue

                    risk = self._registry.getRiskLevel(name)
                    # 提取并剥离 AI 调用理由（仅 write/dangerous 工具有此参数）
                    # 注意：submitElevation 等工具原生就有 reason 参数，不能剥离
                    _native_reason_tools = {"submitElevation", "runPrivileged", "writePrivilegedFile", "nginxWriteStaticFile"}
                    if risk != ToolRiskLevel.READ_ONLY and name not in _native_reason_tools:
                        ai_reason = args.pop("reason", "")
                    else:
                        ai_reason = args.get("reason", "")

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
                        await self._appendToolMessage(
                            callId, modelToolOutput, traceId, sessionId)
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
                        await self._appendToolMessage(
                            callId, modelToolOutput, traceId, sessionId)
                        continue
                    elif verdict.value == "require_confirm":
                        if self._nonInteractiveApprovals or self._autoApproveScheduled:
                            allowed, policyReason = self._isPreAuthorizedToolCall(name, args, sessionId)
                            if allowed:
                                autoReason = (
                                    "scheduled policy pre-authorized REQUIRE_CONFIRM; "
                                    f"policy_reason={reason}; match={policyReason}"
                                )
                                self._trace(traceId, sessionId, "approval.pre_authorized", {
                                    "tool": name,
                                    "args": {k: str(v)[:100] for k, v in args.items()},
                                    "ai_reason": ai_reason,
                                    "reason": autoReason,
                                })
                                stream.emit(EventType.APPROVAL_RESOLVED, {
                                    "action_id": callId,
                                    "approved": True,
                                    "reason": autoReason,
                                })
                                toolOutput = await self._executeTool(name, args)
                            else:
                                # 预授权未覆盖 → 提交工具授权请求（CLI 审批），
                                # 本次跳过该步骤，任务继续执行其余步骤
                                requestCode = self._submitAuthorizationRequest(
                                    name, args, reason, policyReason,
                                    risk, traceId, sessionId,
                                )
                                toolOutput = (
                                    f"[授权请求已提交] 工具 {name} 不在预授权范围内，"
                                    f"本次跳过未执行；管理员批准后后续运行将自动放行。\n"
                                    f"审批命令: sudo nereus approve {requestCode}\n"
                                    f"安全原因: {reason}; 匹配结果: {policyReason}"
                                )
                                self._trace(traceId, sessionId, "approval.authorization_requested", {
                                    "tool": name,
                                    "args": {k: str(v)[:100] for k, v in args.items()},
                                    "ai_reason": ai_reason,
                                    "reason": reason,
                                    "policy_reason": policyReason,
                                    "approval_code": requestCode,
                                })
                                stream.emit(EventType.AUTHORIZATION_REQUESTED, {
                                    "action_id": callId,
                                    "tool": name,
                                    "approval_code": requestCode,
                                    "args": {k: str(v)[:200] for k, v in args.items()},
                                    "ai_reason": ai_reason,
                                    "reason": reason,
                                    "policy_reason": policyReason,
                                })
                                stream.emit(EventType.TOOL_RESULT, {
                                    "call_id": callId, "tool_name": name,
                                    "success": False, "output": toolOutput,
                                })
                                # 注意：不发 ERROR —— 后台任务应继续执行其余步骤，
                                # ERROR 会导致 EventStream.__aiter__ 提前 break
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
                                await self._appendToolMessage(
                                    callId, modelToolOutput, traceId, sessionId)
                                continue
                        else:
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
                    await self._appendToolMessage(
                        callId, modelToolOutput, traceId, sessionId)

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
                    {"rounds": roundCount,
                     "elapsed_seconds": int(_time.time() - (self._startTime or 0)),
                     "background_timeout": getattr(self, '_maxBackgroundTime', 1800)})
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

    def _isPreAuthorizedToolCall(
        self, name: str, args: dict, sessionId: str | None = None
    ) -> tuple[bool, str]:
        """预授权判定：静态策略快照 + 同 session 已批准的授权请求（运行时动态白名单）。

        任务运行中管理员审批通过后，当前会话立即生效（不再需要等下次运行）：
        - 静态策略（启动时快照）匹配 → 放行
        - 静态失败且失败原因是"覆盖不足"（工具/路径/命令未授权）→
          查同 session 已 approved 的授权请求，工具 + 路径/命令匹配 → 放行
        - deniedPaths 类失败始终拒绝（管理员配置的拒绝边界优先）
        """
        ok, reason = self._checkStaticPreauthorization(name, args)
        if ok:
            return True, reason
        if "deniedPaths" in reason:
            return False, reason

        if sessionId or self._autoRunTaskId or self._autoRunSource:
            try:
                from gateway.service.ToolAuthorizationService import (
                    ToolAuthorizationService,
                )

                svc = ToolAuthorizationService()
                grants: list[dict] = []
                # 1) 同 session 内已批准（本次运行中审批立即生效）
                if sessionId:
                    grants += svc.listApprovedGrants(sessionId=sessionId)
                # 2) 所属定时任务的历史已批准授权（跨运行持久，不受前端
                #    保存任务覆盖 approvalPolicy 影响）
                if self._autoRunTaskId is not None:
                    grants += svc.listApprovedGrants(
                        taskId=self._autoRunTaskId,
                        sourceType="scheduled",
                    )
                # 3) 巡检全局已批准授权（跨运行持久）
                if self._autoRunSource == "inspection":
                    grants += svc.listApprovedGrants(sourceType="inspection")
                if self._matchApprovedGrant(grants, name, args):
                    return True, (
                        f"命中已批准的授权请求"
                        f"（静态: {reason}）"
                    )
            except Exception:
                _logger.exception(
                    "查询已批准授权失败: session=%s task=%s source=%s",
                    sessionId, self._autoRunTaskId, self._autoRunSource,
                )
        return False, reason

    def _matchApprovedGrant(
        self, grants: list[dict], name: str, args: dict
    ) -> bool:
        """同 session 已批准授权片段是否覆盖本次调用（工具 + 路径前缀 + 命令前缀）。"""
        if not grants:
            return False
        values = [str(v) for v in self._flattenArgumentValues(args)]
        paths = self._extractPathLikeValues(values)
        cmd = (
            self._extractCommandLine(args)
            if name in ("runCommand", "runShellCommand") else ""
        )
        for grant in grants:
            if str(grant.get("toolName") or "") != name:
                continue
            granted_paths = [
                str(p) for p in (grant.get("paths") or []) if str(p)
            ]
            if granted_paths and paths:
                if not any(
                    self._pathWithin(p, base)
                    for p in paths for base in granted_paths
                ):
                    continue
            granted_cmd = str(grant.get("commandLine") or "")
            if granted_cmd and cmd:
                if not (cmd == granted_cmd or cmd.startswith(granted_cmd + " ")):
                    continue
            return True
        return False

    def _checkStaticPreauthorization(self, name: str, args: dict) -> tuple[bool, str]:
        policy = self._scheduledApprovalPolicy or {}
        allowed_tools = set(str(x) for x in policy.get("allowedTools") or [])
        if name not in allowed_tools:
            return False, f"工具 {name} 不在 allowedTools 中"

        allowed_privileged = set(
            str(x) for x in policy.get("allowedPrivilegedCommands") or []
        )
        if allowed_privileged and name == "submitElevation":
            requested = self._extractPrivilegedCommands(args)
            if not requested:
                return False, "无法识别 submitElevation 请求的特权命令"
            denied = [cmd for cmd in requested if cmd not in allowed_privileged]
            if denied:
                return False, f"特权命令未授权: {', '.join(denied)}"

        # 命令执行类工具：策略显式配置了 allowedCommands 时必须命中命令白名单。
        # 注意：空列表 = 拒绝一切命令；未配置该 key 时维持原有行为（仅工具名+路径匹配）。
        if "allowedCommands" in policy and name in ("runCommand", "runShellCommand"):
            cmd = self._extractCommandLine(args)
            if not cmd:
                return False, "无法识别命令执行工具的命令内容"
            allowed_commands = [str(x) for x in policy.get("allowedCommands") or []]
            matched = any(
                cmd == ac or cmd.startswith(ac + " ") for ac in allowed_commands
            )
            if not matched:
                return False, (
                    f"命令未命中 allowedCommands 白名单: {cmd[:120]}"
                )
            # runShellCommand 走 bash -lc，白名单前缀后可拼接任意 shell 语法
            # （如 `df -h ; curl x | bash`），必须拒绝链式/替换类控制字符。
            # `>` `>>` 重定向允许（配合路径白名单兜底），管道/分号/与/命令替换拒绝。
            if name == "runShellCommand" and re.search(
                r"[;&|`$()\n]", cmd
            ):
                return False, (
                    f"命令包含 shell 控制字符，不满足预授权放行: {cmd[:120]}"
                )

        values = [str(v) for v in self._flattenArgumentValues(args)]
        paths = self._extractPathLikeValues(values)
        denied_paths = [str(p) for p in policy.get("deniedPaths") or [] if str(p)]
        for path in paths:
            for denied in denied_paths:
                if self._pathWithin(path, denied):
                    return False, f"路径 {path} 命中 deniedPaths: {denied}"

        allowed_paths = [str(p) for p in policy.get("allowedPaths") or [] if str(p)]
        if allowed_paths and paths:
            for path in paths:
                if not any(self._pathWithin(path, allowed) for allowed in allowed_paths):
                    return False, f"路径 {path} 不在 allowedPaths 中"

        return True, "工具和路径匹配 approvalPolicy"

    @staticmethod
    def _flattenArgumentValues(value) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, (int, float, bool)):
            return [str(value)]
        if isinstance(value, dict):
            out: list[str] = []
            for item in value.values():
                out.extend(AgentCore._flattenArgumentValues(item))
            return out
        if isinstance(value, (list, tuple, set)):
            out: list[str] = []
            for item in value:
                out.extend(AgentCore._flattenArgumentValues(item))
            return out
        return []

    @staticmethod
    def _extractPathLikeValues(values: list[str]) -> list[str]:
        paths: list[str] = []
        for value in values:
            for match in re.findall(r"(?:~|/)[^\s'\"`,;|&<>]*", value):
                cleaned = match.rstrip(".,)")
                if cleaned and cleaned not in paths:
                    paths.append(cleaned)
        return paths

    @staticmethod
    def _pathWithin(path: str, base: str) -> bool:
        if not base:
            return False
        normalized_path = path.rstrip("/")
        normalized_base = base.rstrip("/")
        return (
            normalized_path == normalized_base
            or normalized_path.startswith(normalized_base + "/")
        )

    @staticmethod
    def _extractPrivilegedCommands(args: dict) -> list[str]:
        if args.get("inline_cmd"):
            return ["exec_arbitrary_cmd"]
        if args.get("script_path"):
            return ["exec_arbitrary_script"]
        commands = args.get("commands") or []
        result: list[str] = []
        if isinstance(commands, list):
            for item in commands:
                if isinstance(item, dict):
                    cmd = item.get("command")
                    if isinstance(cmd, list):
                        cmd = " ".join(str(part) for part in cmd)
                    if cmd:
                        result.append(str(cmd))
        return result

    @staticmethod
    def _extractCommandLine(args: dict) -> str:
        """提取命令执行类工具的实际命令文本（用于 allowedCommands 白名单匹配）。

        - runCommand: command 为 argv 列表 → 空格连接
        - runShellCommand: command 为 shell 字符串
        """
        command = args.get("command")
        if isinstance(command, list):
            parts = [str(part) for part in command if str(part)]
            return " ".join(parts) if parts else ""
        if isinstance(command, str):
            return command.strip()
        return ""

    def _submitAuthorizationRequest(
        self,
        name: str,
        args: dict,
        reason: str,
        policyReason: str,
        risk,
        traceId: str,
        sessionId: str,
    ) -> str:
        """预授权未覆盖时提交工具授权请求（CLI 审批），返回审批码。

        在 Gateway 进程内懒加载 ToolAuthorizationService（与 runPrivileged
        特殊处理同模式）。失败时返回占位码，不影响 Agent 主流程。
        """
        try:
            from gateway.service.ToolAuthorizationService import (
                ToolAuthorizationService,
            )

            paths = self._extractPathLikeValues(
                [str(v) for v in self._flattenArgumentValues(args)]
            )
            commandLine = ""
            if name in ("runCommand", "runShellCommand"):
                commandLine = self._extractCommandLine(args)
            # 无人值守审批码有效期：继承任务/巡检策略的 ttlSeconds / maxRuns
            # （策略默认 7 小时，覆盖管理员隔天登录审批的场景）
            policy = self._scheduledApprovalPolicy or {}
            try:
                ttl = int(policy.get("ttlSeconds") or 25200)
                max_runs = int(policy.get("maxRuns") or 100)
            except (TypeError, ValueError):
                ttl, max_runs = 25200, 100
            code, _created = ToolAuthorizationService().submitRequest(
                sessionId=sessionId,
                toolName=name,
                args={k: str(v)[:500] for k, v in args.items()},
                paths=paths,
                ttlSeconds=ttl,
                maxRuns=max_runs,
                commandLine=commandLine or None,
                reason=reason,
                policyReason=policyReason,
                riskLevel=risk.value if isinstance(risk, ToolRiskLevel) else str(risk),
            )
            return code
        except Exception:
            _logger.exception(
                "提交工具授权请求失败: tool=%s session=%s", name, sessionId
            )
            return "N/A"

    def _updateToolResponse(self, callId: str, newContent: str) -> None:
        """更新对话历史中指定 tool_call_id 的 tool 响应内容。
        
        用于 plan 审批后更新 "[计划已提交，等待审批]" 为实际结果。
        """
        for msg in self._msgs:
            if (msg.get("role") == "tool"
                    and msg.get("tool_call_id") == callId):
                msg["content"] = newContent
                break

    async def _appendToolMessage(self, callId: str, content: str,
                                 traceId: str, sessionId: str) -> str:
        """将工具输出追加到对话历史，并对输出做注入过滤（间接注入防线）。

        工具输出属于不可信外部数据（文件内容、网页、MCP 返回值等），
        在进入模型上下文前依次经过：
          1. 正则快筛（checkPromptInjection）— 命中直接替换为警示文本；
          2. 第三方 LLM 分类器抽检（injection_llm_mode）— 判定注入则替换。

        无论是否过滤，原始输出都会写入审计 trace（tool_output.injection），
        便于事后核对与降低误报影响。

        Args:
            callId: 对应 tool_call_id
            content: 工具输出原始文本
            traceId / sessionId: 审计 trace 标识

        Returns:
            实际写入对话历史的文本（可能已被替换为警示）。
        """
        sanitized = content
        # 1) 正则快筛
        if checkPromptInjection(content):
            self._trace(traceId, sessionId, "tool_output.injection", {
                "source": "regex",
                "output_len": len(content),
                "sample": content[:200],
            })
            self._emitAlert(
                1, "工具输出被过滤：检测到提示词注入特征（正则快筛）")
            sanitized = (
                "[工具输出已过滤] 检测到输出包含提示词注入特征，未回传模型。"
            )
        # 2) 分类器抽检
        elif (self._injectionClassifier is not None
              and self._injectionClassifier.shouldCheck()):
            verdict = await self._injectionClassifier.classify(content)
            if verdict.checked and verdict.injection:
                self._trace(traceId, sessionId, "tool_output.injection", {
                    "source": "classifier",
                    "confidence": verdict.confidence,
                    "reason": verdict.reason,
                    "output_len": len(content),
                    "sample": content[:200],
                })
                self._emitAlert(
                    1,
                    f"工具输出被过滤：LLM 分类器判定包含注入意图"
                    f"（置信度 {verdict.confidence:.2f}）",
                )
                sanitized = (
                    "[工具输出已过滤] 安全检测判定输出包含提示词注入意图"
                    f"（置信度 {verdict.confidence:.2f}），未回传模型。"
                )
        self._msgs.append({
            "role": "tool",
            "tool_call_id": callId,
            "content": sanitized,
        })
        return sanitized

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

    def _emitAlert(self, level: int, message: str) -> None:
        """写入告警（alert_events 表）。告警写入失败不阻断 Agent 主流程。

        Args:
            level: 0 Info / 1 Warning / 2 Error
            message: 告警内容（超出 500 字符截断，匹配表列宽）
        """
        if self._alertSink is None:
            return
        try:
            self._alertSink(int(level), str(message)[:500])
        except Exception:
            # 不记录 message 原文（可能含敏感内容），仅记级别
            _logger.warning("告警写入失败（level=%s），不影响 Agent 主流程", level)

    def _debug_write(self, msg: str):
        """写调试日志到文件（避免 print 污染 MCP stdout）。"""
        import os as _os
        _dbg_path = _os.environ.get("NDLM_DEBUG_LOG", "/tmp/elevation_debug.log")
        try:
            with open(_dbg_path, "a") as _f:
                _f.write(msg + "\n")
        except Exception:
            pass

    async def _executeTool(self, name: str, args: dict) -> str:
        # ── runPrivileged 特殊处理：在 Gateway 进程内直接执行 ──
        # 原因：ElevationService（token 存储）在 Gateway 进程中，
        # 如果通过 stdio 发给 MCP 子进程，子进程的 ElevationService 实例没有 token。
        # 直接在 Gateway 进程内调用 runPrivileged 确保 token 可见。
        if name == "runPrivileged":
            from ndlmpanel_agent.mcp.server.tool_adapter import runPrivileged as _run_privileged
            from ndlmpanel_agent.mcp.server.tool_adapter import McpToolExecutionError
            try:
                result = _run_privileged(**args)
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)
            except McpToolExecutionError as exc:
                return json.dumps(exc.payload, ensure_ascii=False, indent=2, default=str)
            except Exception as exc:
                _logger.exception("_executeTool: runPrivileged 异常")
                return json.dumps({
                    "success": False,
                    "errorCode": exc.__class__.__name__,
                    "errorMessage": str(exc),
                }, ensure_ascii=False)

        # ── submitElevation 无人值守 TTL 注入 ──
        # 在线（交互）会话：维持原装（agent 传什么用什么，默认 1 小时）。
        # 无人值守会话（定时任务/巡检，带 scheduledApprovalPolicy）：
        # agent 未显式指定 ttl_seconds 时，注入策略 TTL（默认 7 小时），
        # 覆盖管理员隔天登录审批的场景。
        if (
            name == "submitElevation"
            and self._scheduledApprovalPolicy
            and not args.get("ttl_seconds")
        ):
            try:
                ttl = int(self._scheduledApprovalPolicy.get("ttlSeconds") or 25200)
            except (TypeError, ValueError):
                ttl = 25200
            args = {**args, "ttl_seconds": ttl}

        loop = asyncio.get_running_loop()
        reqId = gen_tool_call_id()
        mcpReq = encodeRequest("tools/call",
                               {"name": name, "arguments": args},
                               reqId)
        raw = await loop.run_in_executor(None, self._dispatcher.handle, mcpReq)
        self._debug_write(f"[DEBUG _executeTool] name={name} args_keys={list(args.keys())}")
        self._debug_write(f"[DEBUG _executeTool] mcpReq={mcpReq}")
        self._debug_write(f"[DEBUG _executeTool] raw={repr(raw)}")
        self._debug_write(f"[DEBUG _executeTool] raw type={type(raw).__name__}")
        if raw is None or raw.strip() == "":
            return f"<error: MCP 返回了空结果, raw={repr(raw)}>"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            self._debug_write(f"[DEBUG _executeTool] JSONDecodeError: {e}")
            self._debug_write(f"[DEBUG _executeTool] raw first 500 chars: {raw[:500]}")
            return f"<error: JSON 解析失败: {e}, raw={raw[:200]}>"
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
