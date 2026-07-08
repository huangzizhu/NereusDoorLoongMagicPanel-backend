"""后台 Agent 执行器 — 解耦 WebSocket 生命周期。

核心职责：
- 管理 Agent 任务的后台执行（独立于任何 WS 连接）
- 拥有 RuntimeSession 的生命周期
- 将 Agent 事件写入 EventBuffer（供 WS handler 消费）
- 处理消息排队（agent 运行时新消息进入队列）
- 统一持久化（消息、token 用量、会话状态）
"""
from __future__ import annotations
import asyncio
import json
import logging
from typing import Any

from agent.agent_router.router import AgentMode
from agent.integration.session import AgentSession as RuntimeAgentSession
from agent.shared.types import AgentEvent, EventType
from gateway.service.AgentEventBuffer import AgentEventBuffer

_logger = logging.getLogger("ndlmpanel.gateway")


class BackgroundRunner:
    """管理后台 Agent 任务的独立运行器。

    解耦 WS 生命周期：即使所有 WS 连接断开，agent 仍然运行。
    所有事件写入 EventBuffer，WS handler 从中拉取推送给前端。
    """

    def __init__(self, dao, profileService, tokenUsageDao):
        self._dao = dao
        self._profileService = profileService
        self._tokenUsageDao = tokenUsageDao

        # sessionId → {buffer, queue, task, runtime, running, userId}
        self._sessions: dict[str, dict] = {}
        self._lock = asyncio.Lock()

        # ── 后台超时配置 ──
        self._backgroundApprovalTimeout = 600.0   # 10 分钟
        self._maxBackgroundTime = 1800.0           # 30 分钟
        self._maxBackgroundRounds = 100            # 最大轮次（兜底）

    # ── 公共 API ──

    async def submit(
        self, userId: int, sessionId: str, message: str,
    ) -> AgentEventBuffer:
        """提交用户消息，返回事件缓冲区。

        如果已有 agent 在运行，消息进入排队队列，
        当前任务完成后自动消费。
        """
        async with self._lock:
            if sessionId not in self._sessions:
                buffer = AgentEventBuffer(maxSize=1000)
                queue: asyncio.Queue[str] = asyncio.Queue()
                self._sessions[sessionId] = {
                    "buffer": buffer,
                    "queue": queue,
                    "task": None,
                    "runtime": None,
                    "running": False,
                    "userId": userId,
                }

            sessionState = self._sessions[sessionId]

            if sessionState["running"]:
                await sessionState["queue"].put(message)
                _logger.info(
                    "Agent 消息排队: session=%s queue_size=%d",
                    sessionId, sessionState["queue"].qsize(),
                )
                return sessionState["buffer"]

            # 直接启动
            sessionState["running"] = True
            # ── 重置 buffer 的 done 状态（上一轮 markDone 后 _done=True）──
            await sessionState["buffer"].resetForNewRound()
            task = asyncio.create_task(
                self._runAgentLoop(sessionId, message)
            )
            sessionState["task"] = task
            return sessionState["buffer"]

    async def cancel(self, sessionId: str) -> bool:
        """取消指定会话的后台 agent。"""
        async with self._lock:
            state = self._sessions.get(sessionId)
            if state is None:
                return False
            task = state.get("task")
            if task and not task.done():
                task.cancel()
            # 清空排队队列
            while not state["queue"].empty():
                try:
                    state["queue"].get_nowait()
                except asyncio.QueueEmpty:
                    break
            state["running"] = False
            return True

    def getBuffer(self, sessionId: str) -> AgentEventBuffer | None:
        """获取会话的事件缓冲区（供 WS handler 使用）。"""
        state = self._sessions.get(sessionId)
        return state["buffer"] if state else None

    async def clearBuffer(self, sessionId: str) -> None:
        """清空会话的事件缓冲区（regenerate 时使用）。"""
        async with self._lock:
            state = self._sessions.get(sessionId)
            if state is None:
                return
            buffer = state["buffer"]
            # 重建 buffer 以完全清空积压事件
            newBuffer = AgentEventBuffer(maxSize=1000)
            state["buffer"] = newBuffer

    def isRunning(self, sessionId: str) -> bool:
        """检查是否有后台 agent 在运行。"""
        state = self._sessions.get(sessionId)
        return state["running"] if state else False

    def getRuntime(self, sessionId: str) -> RuntimeAgentSession | None:
        """获取会话的 RuntimeSession（供审批/计划/选择题操作使用）。"""
        state = self._sessions.get(sessionId)
        return state["runtime"] if state else None

    def cleanSession(self, sessionId: str) -> None:
        """清理会话的所有后台资源。"""

        async def _clean():
            async with self._lock:
                state = self._sessions.pop(sessionId, None)
                if state is None:
                    return
                task = state.get("task")
                if task and not task.done():
                    task.cancel()
                runtime = state.get("runtime")
                if runtime:
                    try:
                        runtime.close()
                    except Exception:
                        pass

        asyncio.create_task(_clean())

    # ── 审批 / 计划 / 选择题委托 ──

    def approve(self, sessionId: str, actionId: str) -> bool:
        """批准一个待审批的高危动作。"""
        runtime = self.getRuntime(sessionId)
        if runtime is None:
            return False
        return runtime.approve(actionId)

    def reject(self, sessionId: str, actionId: str, reason: str = "") -> bool:
        """拒绝一个待审批的高危动作。"""
        runtime = self.getRuntime(sessionId)
        if runtime is None:
            return False
        return runtime.reject(actionId, reason)

    def approvePlan(self, sessionId: str) -> bool:
        """批准当前待审批的计划。"""
        runtime = self.getRuntime(sessionId)
        if runtime is None:
            return False
        return runtime.approvePlan()

    def rejectPlan(self, sessionId: str, reason: str = "") -> bool:
        """拒绝当前待审批的计划。"""
        runtime = self.getRuntime(sessionId)
        if runtime is None:
            return False
        return runtime.rejectPlan(reason)

    def resolveChoice(self, sessionId: str, actionId: str,
                      selectionId: str, customInput: str = "") -> bool:
        """响应当前待回复的选择题。"""
        runtime = self.getRuntime(sessionId)
        if runtime is None:
            return False
        return runtime.resolveChoice(actionId, selectionId, customInput)

    def switchMode(self, sessionId: str, mode: AgentMode) -> bool:
        """切换 Agent 运行模式。"""
        runtime = self.getRuntime(sessionId)
        if runtime is None:
            return False
        runtime.switchMode(mode)
        return True

    # ── 内部实现 ──

    async def _runAgentLoop(self, sessionId: str, firstMessage: str) -> None:
        """后台 agent 主循环 — 独立于任何 WS 连接。

        负责：
        1. 获取/创建 RuntimeSession
        2. 持久化 user 消息
        3. 运行 agent 循环，将事件写入 EventBuffer
        4. 持久化 assistant/tool 消息 + token 用量
        5. 完成后检查排队队列，自动消费下一条消息
        """
        sessionState = self._sessions.get(sessionId)
        if sessionState is None:
            return

        buffer: AgentEventBuffer = sessionState["buffer"]
        queue: asyncio.Queue[str] = sessionState["queue"]
        userId = sessionState["userId"]
        currentMessage = firstMessage

        try:
            while currentMessage is not None:
                # ── 获取或创建 runtime ──
                runtime = await self._ensureRuntime(sessionId, userId)
                if runtime is None:
                    await buffer.push({
                        "type": "error",
                        "data": {"message": "无法创建 Agent 运行时"},
                    })
                    break

                sessionState["runtime"] = runtime

                # ── 持久化 user 消息 ──
                roundIndex = self._dao.getNextRoundIndex(sessionId)
                userMessageId = self._dao.addMessage(
                    sessionId, "user", currentMessage, roundIndex=roundIndex,
                )

                # ── 获取对话历史 ──
                history = self._dao.getRecentConversationHistory(sessionId)

                # ── 本轮持久化状态 ──
                traceId: str | None = None
                assistantParts: list[str] = []
                usageThisRound: dict = {}
                userTraceUpdated = False

                try:
                    async for event in runtime.submit(
                        currentMessage, conversationHistory=history,
                    ):
                        traceId = traceId or event.trace_id
                        if traceId and not userTraceUpdated:
                            self._dao.updateMessageTrace(userMessageId, traceId)
                            userTraceUpdated = True

                        # ── 格式化并写入 buffer ──
                        formatted = self._formatAgentEvent(event)
                        await buffer.push(formatted)

                        eventType = event.type

                        # ── 持久化关键事件 ──
                        if eventType == EventType.TEXT_DELTA:
                            assistantParts.append(
                                str(event.data.get("content", ""))
                            )

                        elif eventType == EventType.TOOL_CALLING:
                            toolCalls = event.data.get("tool_calls", [])
                            usageThisRound = event.data.get("usage", {})
                            if toolCalls:
                                self._dao.addMessage(
                                    sessionId, "assistant", content=None,
                                    traceId=traceId, roundIndex=roundIndex,
                                    metadata={"tool_calls": toolCalls},
                                )

                        elif eventType == EventType.TOOL_RESULT:
                            self._dao.addMessage(
                                sessionId, "tool",
                                content=str(event.data.get("output", "")),
                                traceId=traceId, roundIndex=roundIndex,
                                toolCallId=event.data.get("call_id", ""),
                                metadata={
                                    "tool_name": event.data.get("tool_name", ""),
                                },
                            )
                            # ── 提权码同步：submitElevation 必须在后台注册 ──
                            # （不能只靠 _streamEvents，因为 WS 可能断开）
                            tool_name = event.data.get("tool_name", "")
                            if (tool_name == "submitElevation"
                                    and event.data.get("success")):
                                self._syncElevation(sessionId, event.data)

                        elif eventType == EventType.APPROVAL_REQUIRED:
                            self._dao.updateStatus(sessionId, "waiting_approval")
                            self._dao.updatePendingApproval(sessionId, {
                                "action_id": event.data.get("action_id", ""),
                                "tool_name": event.data.get("tool_name", ""),
                                "arguments": event.data.get("arguments", {}),
                                "reason": event.data.get("reason", ""),
                                "ai_reason": event.data.get("ai_reason", ""),
                                "call_id": event.data.get("call_id", ""),
                            })

                        elif eventType == EventType.APPROVAL_RESOLVED:
                            self._dao.updateStatus(sessionId, "running")
                            self._dao.clearPendingApproval(sessionId)

                        elif eventType == EventType.ERROR:
                            self._dao.updateStatus(
                                sessionId, "error",
                                lastError=str(event.data.get("message", "")),
                            )
                            self._dao.clearPendingApproval(sessionId)

                        elif eventType == EventType.CHOICE_REQUIRED:
                            self._dao.updateStatus(sessionId, "waiting_choice")
                            # ── 持久化选择题数据（WS 断连恢复用）──
                            choice_data = {
                                "action_id": event.data.get("action_id", ""),
                                "question": event.data.get("question", ""),
                                "options": event.data.get("options", []),
                                "allow_custom": event.data.get("allow_custom", True),
                                "call_id": event.data.get("call_id", ""),
                            }
                            self._dao.updatePendingChoice(sessionId, choice_data)

                        elif eventType == EventType.CHOICE_RESOLVED:
                            self._dao.updateStatus(sessionId, "running")
                            self._dao.clearPendingChoice(sessionId)

                        elif eventType == EventType.PLAN_PROPOSED:
                            self._dao.updateStatus(sessionId, "waiting_plan")

                        elif eventType == EventType.PLAN_APPROVED:
                            self._dao.updateMode(sessionId, "agent")
                            self._dao.updateStatus(sessionId, "running")
                            call_id = str(event.data.get("call_id", ""))
                            tool_response = str(
                                event.data.get("tool_response", "")
                            )
                            if call_id:
                                self._dao.updateToolResponse(
                                    sessionId, call_id, tool_response,
                                )

                        elif eventType == EventType.PLAN_REJECTED:
                            self._dao.updateStatus(sessionId, "running")
                            reason = str(event.data.get("reason", ""))
                            call_id = str(event.data.get("call_id", ""))
                            if call_id:
                                new_content = (
                                    f"[计划被拒绝] {reason}"
                                    if reason
                                    else "[计划被拒绝]"
                                )
                                self._dao.updateToolResponse(
                                    sessionId, call_id, new_content,
                                )
                            if "超时" in reason:
                                self._dao.updateMode(sessionId, "agent")

                        elif eventType == EventType.TEXT_DONE:
                            if not usageThisRound:
                                usageThisRound = event.data.get("usage", {})

                        elif eventType == EventType.DONE:
                            self._dao.clearPendingApproval(sessionId)

                    # ── 持久化 final assistant 文本 ──
                    finalText = "".join(assistantParts).strip()
                    if finalText:
                        self._dao.addMessage(
                            sessionId, "assistant", finalText,
                            traceId=traceId, roundIndex=roundIndex,
                        )

                    # ── 记录 token 用量 ──
                    await self._recordTokenUsage(
                        sessionId, traceId, userId, usageThisRound,
                    )

                    # ── 首轮自动生成标题 ──
                    if roundIndex == 1:
                        session = self._dao.getSession(sessionId, userId)
                        if session and session.title in (
                            "新 Agent 会话", "新会话", "",
                        ):
                            asyncio.create_task(
                                self._autoGenerateTitle(
                                    sessionId, currentMessage, finalText,
                                )
                            )

                except asyncio.CancelledError:
                    await buffer.push({
                        "type": "error",
                        "data": {"message": "Agent 任务被取消"},
                    })
                    self._dao.updateStatus(sessionId, "idle")
                    break

                except Exception as exc:
                    _logger.exception(
                        "Agent 后台执行异常: session=%s", sessionId,
                    )
                    await buffer.push({
                        "type": "error",
                        "data": {"message": str(exc)},
                    })
                    self._dao.updateStatus(
                        sessionId, "error", lastError=str(exc),
                    )
                    break

                # ── 本轮结束：检查排队队列 ──
                try:
                    currentMessage = queue.get_nowait()
                    _logger.info(
                        "Agent 消费排队消息: session=%s remaining=%d",
                        sessionId, queue.qsize(),
                    )
                except asyncio.QueueEmpty:
                    currentMessage = None

            # ── agent 循环正常结束 ──
            self._dao.updateStatus(sessionId, "idle")
            await buffer.markDone("idle")

        finally:
            async with self._lock:
                sessionState["running"] = False
                sessionState["runtime"] = None
                # 检查是否还有排队消息 → 自动启动下一轮
                if (
                    sessionState in self._sessions.values()
                    and not sessionState["queue"].empty()
                ):
                    nextMsg = sessionState["queue"].get_nowait()
                    sessionState["running"] = True
                    # ── 重置 buffer done 状态（必须在新 loop 前完成）──
                    await sessionState["buffer"].resetForNewRound()
                    asyncio.create_task(
                        self._runAgentLoop(sessionId, nextMsg)
                    )

    async def _ensureRuntime(
        self, sessionId: str, userId: int,
    ) -> RuntimeAgentSession | None:
        """获取或创建 RuntimeSession。"""
        sessionState = self._sessions.get(sessionId)
        if sessionState is None:
            return None

        if sessionState.get("runtime") is not None:
            return sessionState["runtime"]

        session = self._dao.getSession(sessionId, userId)
        if session is None:
            return None

        config = self._profileService.buildAgentConfig(
            session.profileId,
            safetyPolicy=session.safetyPolicy,
        )

        try:
            mode = AgentMode(session.mode)
        except ValueError:
            mode = AgentMode.AGENT

        runtime = RuntimeAgentSession(
            config=config,
            userId=str(userId),
            sessionId=sessionId,
            mode=mode,
            toolSource=session.toolSource,
            mcpServers=session.mcpServers,
        )
        return runtime

    async def _recordTokenUsage(
        self, sessionId: str, traceId: str | None,
        userId: int, usage: dict,
    ) -> None:
        """记录本轮 LLM 调用的 token 用量。"""
        if not usage:
            return
        inputTokens = (
            usage.get("prompt_tokens")
            or usage.get("input_tokens")
            or 0
        )
        outputTokens = (
            usage.get("completion_tokens")
            or usage.get("output_tokens")
            or 0
        )
        if not inputTokens and not outputTokens:
            return
        cachedInputTokens = (
            usage.get("prompt_cache_hit_tokens")
            or usage.get("prompt_tokens_details", {}).get("cached_tokens")
            or 0
        )
        model = "unknown"
        try:
            session = self._dao.getSession(sessionId, userId)
            if session and session.profileId:
                profile = self._profileService.dao.getProfileById(
                    session.profileId
                )
                if profile:
                    model = profile.model
        except Exception:
            pass
        self._tokenUsageDao.recordUsage(
            sessionId=sessionId,
            model=model,
            inputTokens=int(inputTokens),
            outputTokens=int(outputTokens),
            cachedInputTokens=int(cachedInputTokens),
            traceId=traceId,
        )

    async def _autoGenerateTitle(
        self, sessionId: str, userMsg: str, response: str,
    ) -> None:
        """首轮对话后异步生成标题。"""
        try:
            session = self._dao.getSession(sessionId)
            if session is None:
                return

            from gateway.utils.llm_utils import get_llm_config
            from agent.llm_providers.factory import createProvider
            from agent.shared.types import AgentConfig

            llm_cfg = get_llm_config(session)
            endpoint = llm_cfg.get("endpoint", "")
            api_key = llm_cfg.get("api_key", "")
            model = llm_cfg.get("model", "deepseek-chat")

            if not endpoint or not api_key:
                self._titleFallback(sessionId, userMsg)
                return

            raw_endpoint = endpoint
            if "/anthropic" in endpoint:
                pass
            elif "api.deepseek.com" in endpoint:
                endpoint = "https://api.deepseek.com"
            else:
                endpoint = endpoint.rstrip("/")
                if endpoint.endswith("/chat/completions"):
                    endpoint = endpoint[: -len("/chat/completions")]
                if not endpoint.endswith("/v1"):
                    endpoint = endpoint + "/v1"

            titleConfig = AgentConfig(
                llm_endpoint=endpoint,
                llm_model=model,
                llm_max_tokens=1000,
                llm_temperature=0.0,
                llm_retry_count=1,
                llm_retry_delay=1.0,
            )
            titleConfig.llm_api_key = api_key

            provider = createProvider(titleConfig)
            resp = await provider.chat([
                {
                    "role": "system",
                    "content": (
                        "根据对话内容生成一个简洁的对话标题"
                        "（10字~20字以内），只返回标题本身，不要加引号"
                    ),
                },
                {"role": "user", "content": f"用户：{userMsg[:200]}"},
            ])
            title = (resp.content or "").strip().strip('"').strip("'")
            if title and len(title) <= 100:
                self._dao.updateSessionTitle(sessionId, title)
                _logger.info(
                    "自动标题生成成功: session=%s title=%s",
                    sessionId, title,
                )
                # ── 推送标题事件到 buffer（WS 在线时前端直接展示）──
                await self._pushTitleToBuffer(sessionId, title)
            else:
                self._titleFallback(sessionId, userMsg)

        except Exception as e:
            _logger.warning(
                "自动标题生成失败: %s, 使用 fallback。session=%s",
                e, sessionId,
            )
            self._titleFallback(sessionId, userMsg)

    async def _pushTitleToBuffer(self, sessionId: str, title: str) -> None:
        """推送标题更新事件到 EventBuffer。"""
        state = self._sessions.get(sessionId)
        if state is None:
            return
        buffer = state.get("buffer")
        if buffer is None:
            return
        await buffer.push({
            "type": "title.updated",
            "data": {"title": title},
        })

    def _titleFallback(self, sessionId: str, userMsg: str) -> None:
        """标题生成 fallback：用用户消息前 20 字作为标题。"""
        fallbackTitle = userMsg[:20].strip()
        if fallbackTitle:
            try:
                self._dao.updateSessionTitle(sessionId, fallbackTitle)
                # ── 推送标题事件到 buffer ──
                asyncio.create_task(
                    self._pushTitleToBuffer(sessionId, fallbackTitle)
                )
            except Exception as e:
                _logger.warning(
                    "标题 fallback 写入失败: session=%s error=%s",
                    sessionId, e,
                )

    @staticmethod
    def _syncElevation(sessionId: str, tcData: dict) -> None:
        """同步提权码到 ElevationService（后台执行，不依赖 WS）。

        必须在 BackgroundRunner 中调用，因为 agent 可能在无 WS 连接时运行。
        """
        import json
        from pathlib import Path

        tool_output = tcData.get("output", "")
        try:
            result_data = (
                json.loads(tool_output)
                if isinstance(tool_output, str) else {}
            )
        except (json.JSONDecodeError, TypeError):
            _logger.warning("_syncElevation: 无法解析 tool output")
            return

        code = result_data.get("code")
        commands = result_data.get("commands", [])
        reason = result_data.get("reason", "")
        if not code or not commands:
            return

        from gateway.service.elevation_service import ElevationService
        elevation = ElevationService()
        entry = elevation.get_code(code)
        if entry is not None:
            return  # 已存在

        inline_cmd = result_data.get("inline_cmd", "")
        script_path = result_data.get("script_path", "")

        from privileged_agent.crypto import hash_payload as _hash_payload
        inline_cmd_hash = (
            _hash_payload({"cmd": inline_cmd}) if inline_cmd else None
        )
        script_hash = None
        if script_path:
            try:
                _script_content = Path(script_path).read_text(
                    encoding="utf-8", errors="ignore",
                )
                script_hash = _hash_payload({"content": _script_content})
            except (OSError, FileNotFoundError):
                _logger.warning(
                    "_syncElevation: 无法读取脚本 %s", script_path,
                )

        elevation.generate_code(
            session_id=sessionId,
            commands=commands,
            reason=reason,
            ttl_seconds=int(result_data.get("ttl_seconds", 3600)),
            max_ops=int(result_data.get("max_ops", 10)),
            code=code,
            inline_cmd=inline_cmd or None,
            inline_cmd_hash=inline_cmd_hash,
            script_path=script_path or None,
            script_hash=script_hash,
        )
        _logger.info(
            "_syncElevation: code=%s session=%s registered",
            code, sessionId,
        )

    @staticmethod
    def _formatAgentEvent(event: AgentEvent) -> dict[str, Any]:
        """格式化 AgentEvent 为前端 JSON 兼容格式。"""
        eventType = (
            event.type.value
            if hasattr(event.type, "value")
            else str(event.type)
        )
        return {
            "type": eventType,
            "sessionId": event.session_id,
            "traceId": event.trace_id,
            "timestamp": event.timestamp,
            "data": event.data,
        }
