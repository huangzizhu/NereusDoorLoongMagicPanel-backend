from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import WebSocket

from agent.agent_router.router import AgentMode
from agent.integration.session import AgentSession as RuntimeAgentSession
from agent.shared.types import AgentEvent, EventType
from agent.llm_providers.factory import createProvider
from agent.shared.types import AgentConfig
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.AgentSessionDaoOrm import AgentSessionDaoOrm
from gateway.dao.AgentTokenUsageDaoOrm import AgentTokenUsageDaoOrm
from gateway.service.AgentLlmProfileService import AgentLlmProfileService
from gateway.service.elevation_service import ElevationService
from gateway.utils.llm_utils import get_llm_config
from pojo.Agent import AgentSessionCreate

_logger = logging.getLogger("ndlmpanel.gateway")


class AgentGatewayService(Singleton):
    @singletonInit
    def __init__(self):
        self.sessionDao = AgentSessionDaoOrm()
        self.profileService = AgentLlmProfileService()
        self.tokenUsageDao = AgentTokenUsageDaoOrm()
        self._runtimeSessions: dict[str, RuntimeAgentSession] = {}
        self._turnTasks: dict[str, asyncio.Task] = {}
        self._sendLocks: dict[str, asyncio.Lock] = {}
        self._activeConns: dict[str, tuple[WebSocket, asyncio.Lock]] = {}

    def invalidateRuntime(self, sessionId: str) -> None:
        """使缓存的 RuntimeSession 失效，下次 _getRuntimeSession 将重建。"""
        runtime = self._runtimeSessions.pop(sessionId, None)
        if runtime is not None:
            runtime.close()
        task = self._turnTasks.pop(sessionId, None)
        if task is not None and not task.done():
            task.cancel()
        self._sendLocks.pop(sessionId, None)

    def switchToolSource(self, sessionId: str, toolSource: str,
                         mcpServers: list[dict] | None = None) -> None:
        """切换工具来源并重建 runtime。"""
        self.invalidateRuntime(sessionId)
        # 数据库中的 toolSource / mcpServers 由调用者更新

    async def handleWebSocket(self, websocket: WebSocket, userId: int,
                              sessionId: str | None = None) -> None:
        created = False
        if sessionId:
            session = self.sessionDao.getSession(sessionId, userId)
            if session is None:
                await websocket.send_json(self._serverEvent("error", sessionId, None, {
                    "message": f"不存在 sessionId 为 {sessionId} 的 Agent 会话",
                }))
                return
        else:
            defaultProfile = self.profileService.getDefaultProfile()
            request = AgentSessionCreate(
                title="新 Agent 会话",
                profileId=defaultProfile.profileId if defaultProfile else None,
            )
            session = self.sessionDao.createSession(
                sessionId=self._newSessionId(),
                userId=userId,
                request=request,
            )
            sessionId = session.sessionId
            created = True

        assert sessionId is not None
        sendLock = self._sendLocks.setdefault(sessionId, asyncio.Lock())
        self._activeConns[sessionId] = (websocket, sendLock)
        await self._send(websocket, sendLock, self._serverEvent(
            "agent.ready", sessionId, None, {"sessionId": sessionId}
        ))
        if created:
            await self._send(websocket, sendLock, self._serverEvent(
                "session.created", sessionId, None, {"sessionId": sessionId}
            ))

        # ── WS 重连恢复：检测待审批事件 ──
        # 如果上次 WS 断开时有残留的 APPROVAL_REQUIRED，
        # 重新推送给前端让审批弹窗恢复
        pending_approval = self.sessionDao.getPendingApproval(sessionId)
        if pending_approval:
            _logger.info(
                "WS 重连检测到待审批事件: session=%s tool=%s",
                sessionId, pending_approval.get("tool_name", "?"),
            )
            await self._send(websocket, sendLock, self._serverEvent(
                "approval.resume", sessionId, None, {
                    "message": "检测到上次断连时有待审批操作，请确认是否继续",
                    "approval": pending_approval,
                }
            ))

        try:
            while True:
                payload = await websocket.receive_json()
                msgType = payload.get("type")

                if msgType == "ping":
                    await self._send(websocket, sendLock, self._serverEvent(
                        "pong", sessionId, None, {}
                    ))
                elif msgType == "user_message":
                    message = str(payload.get("message") or "")
                    if not message.strip():
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None, {"message": "message 不能为空"}
                        ))
                        continue
                    if self._isRunning(sessionId):
                        await self._send(websocket, sendLock, self._serverEvent(
                            "agent.busy", sessionId, None, {"message": "当前会话已有运行中的任务"}
                        ))
                        continue
                    task = asyncio.create_task(
                        self._runTurn(websocket, sendLock, userId, sessionId, message)
                    )
                    self._turnTasks[sessionId] = task
                elif msgType == "approval":
                    actionId = str(payload.get("actionId") or "")
                    approved = bool(payload.get("approved"))
                    reason = str(payload.get("reason") or "")
                    runtime = self._runtimeSessions.get(sessionId)
                    ok = False
                    if runtime is not None and actionId:
                        ok = runtime.approve(actionId) if approved else runtime.reject(actionId, reason)
                    # ── WS 重连后审批恢复路径 ──
                    # runtime 已销毁（WS 断连导致），但 DB 中还有 pendingApproval
                    if not ok and actionId:
                        pending = self.sessionDao.getPendingApproval(sessionId)
                        if pending and pending.get("action_id") == actionId:
                            tool_name = pending.get("tool_name", "")
                            tool_args = pending.get("arguments", {})
                            _logger.info(
                                "WS 重连审批恢复: session=%s action=%s tool=%s approved=%s",
                                sessionId, actionId, tool_name, approved,
                            )

                            # 重建 runtime 并实际执行工具
                            execution_ok = False
                            execution_output = ""
                            if approved:
                                try:
                                    session_obj = self.sessionDao.getSession(
                                        sessionId, userId
                                    )
                                    if session_obj is not None:
                                        exec_runtime = self._getRuntimeSession(
                                            session_obj
                                        )
                                        execution_output = (
                                            await exec_runtime._core._executeTool(
                                                tool_name, tool_args
                                            )
                                        )
                                        execution_ok = True
                                except Exception as exc:
                                    execution_output = str(exc)
                                    execution_ok = False
                            else:
                                execution_output = f"[用户拒绝] 工具 {tool_name} 未执行。原因: {reason}"

                            # 写入 tool 结果到 DB
                            self.sessionDao.addMessage(
                                sessionId, "tool",
                                content=str(execution_output)[:2000],
                                roundIndex=self.sessionDao.getNextRoundIndex(sessionId),
                                toolCallId=pending.get("call_id", actionId),
                                metadata={"tool_name": tool_name},
                            )

                            # 清除 pending
                            self.sessionDao.clearPendingApproval(sessionId)
                            self.sessionDao.updateStatus(sessionId, "idle")
                            # 清理 runtime（下次 submit 时重建）
                            self.invalidateRuntime(sessionId)

                            # 发送 approval 和 tool result 事件
                            await self._send(websocket, sendLock, self._serverEvent(
                                "approval.resolved", sessionId, None, {
                                    "action_id": actionId,
                                    "approved": approved,
                                    "reason": reason,
                                }
                            ))
                            await self._send(websocket, sendLock, self._serverEvent(
                                "tool.result", sessionId, None, {
                                    "call_id": pending.get("call_id", actionId),
                                    "tool_name": tool_name,
                                    "success": execution_ok,
                                    "output": str(execution_output)[:2000],
                                }
                            ))

                            # ── 继续 AgentCore 循环 ──
                            # tool result 已写入 DB，历史完整
                            # _runTurn 会: 新建干净 runner → 从 DB 拉上下文
                            # → LLM 看到完整的 tool 链 → 自然继续
                            if approved and execution_ok:
                                # invalidateRuntime 已清理旧 runtime
                                cont_task = asyncio.create_task(
                                    self._runTurn(
                                        websocket, sendLock,
                                        userId, sessionId, "",
                                    )
                                )
                                self._turnTasks[sessionId] = cont_task
                            else:
                                await self._send(websocket, sendLock, self._serverEvent(
                                    "done", sessionId, None, {}
                                ))
                            ok = True
                    if not ok:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None, {"message": "审批动作不存在或已处理"}
                        ))
                elif msgType == "plan":
                    approved = bool(payload.get("approved"))
                    reason = str(payload.get("reason") or "")
                    runtime = self._runtimeSessions.get(sessionId)
                    ok = False
                    if runtime is not None:
                        ok = runtime.approvePlan() if approved else runtime.rejectPlan(reason)
                    if not ok:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None, {"message": "无待审批的计划或计划已处理"}
                        ))
                elif msgType == "choice":
                    actionId = str(payload.get("actionId") or "")
                    selectionId = str(payload.get("selectionId") or "")
                    customInput = str(payload.get("customInput") or "")
                    runtime = self._runtimeSessions.get(sessionId)
                    ok = False
                    if runtime is not None:
                        ok = runtime.resolveChoice(actionId, selectionId, customInput)
                    if not ok:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None, {"message": "无待回复的选择题或已处理"}
                        ))
                elif msgType == "switch_mode":
                    mode_str = str(payload.get("mode") or "")
                    try:
                        target_mode = AgentMode(mode_str)
                    except ValueError:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None,
                            {"message": f"不支持的模式: {mode_str}"}
                        ))
                        continue

                    # 1. 持久化到 DB（不管 runtime 是否存在都要写）
                    self.sessionDao.updateMode(sessionId, target_mode.value)

                    # 2. 如果运行时 session 存在 → 即时生效
                    runtime = self._runtimeSessions.get(sessionId)
                    if runtime is not None:
                        runtime.switchMode(target_mode)
                        await self._send(websocket, sendLock, self._serverEvent(
                            "mode_changed", sessionId, None,
                            {"mode": target_mode.value}
                        ))
                    else:
                        # 运行时不存在 → 告知用户下次会话生效
                        await self._send(websocket, sendLock, self._serverEvent(
                            "mode_changed", sessionId, None,
                            {"mode": target_mode.value,
                             "effective": "next_turn"}
                        ))
                elif msgType == "cancel":
                    await self._cancelTurn(sessionId)
                    self.sessionDao.updateStatus(sessionId, "idle")
                    self.sessionDao.clearPendingApproval(sessionId)
                    await self._send(websocket, sendLock, self._serverEvent(
                        "done", sessionId, None, {"reason": "cancelled"}
                    ))
                else:
                    await self._send(websocket, sendLock, self._serverEvent(
                        "error", sessionId, None, {"message": f"不支持的 Agent 消息类型: {msgType}"}
                    ))
        finally:
            await self._cancelTurn(sessionId)

    async def _runTurn(self, websocket: WebSocket, sendLock: asyncio.Lock,
                       userId: int, sessionId: str, message: str) -> None:
        runtime: RuntimeAgentSession | None = None
        traceId: str | None = None
        doneSent = False
        assistantParts: list[str] = []
        roundIndex = self.sessionDao.getNextRoundIndex(sessionId)
        userMessageId = self.sessionDao.addMessage(
            sessionId, "user", message, roundIndex=roundIndex
        )
        userTraceUpdated = False
        # 跟踪本轮 tool_calls 和 tool 结果以持久化
        currentTcBlock: list[dict] | None = None  # 当前轮次的 tool_calls 块
        toolResultsThisRound: list[dict] = []     # 当前轮次的 tool 结果
        usageThisRound: dict = {}

        try:
            session = self.sessionDao.getSession(sessionId, userId)
            if session is None:
                raise RuntimeError(f"session {sessionId} 不存在")
            self.sessionDao.updateStatus(sessionId, "running")
            runtime = self._getRuntimeSession(session)
            history = self.sessionDao.getRecentConversationHistory(sessionId)
            if history and history[-1]["role"] == "user" and history[-1]["content"] == message:
                history = history[:-1]

            async for event in runtime.submit(message, conversationHistory=history):
                traceId = traceId or event.trace_id
                if traceId and not userTraceUpdated:
                    self.sessionDao.updateMessageTrace(userMessageId, traceId)
                    userTraceUpdated = True

                eventType = event.type.value if hasattr(event.type, "value") else str(event.type)

                if event.type == EventType.TEXT_DELTA:
                    assistantParts.append(str(event.data.get("content", "")))

                elif event.type == EventType.TOOL_CALLING:
                    # 持久化：assistant 带 tool_calls 的消息
                    currentTcBlock = event.data.get("tool_calls", [])
                    usageThisRound = event.data.get("usage", {})
                    if currentTcBlock:
                        self.sessionDao.addMessage(
                            sessionId, "assistant", content=None,
                            traceId=traceId, roundIndex=roundIndex,
                            metadata={"tool_calls": currentTcBlock},
                        )

                elif event.type == EventType.TOOL_RESULT:
                    # 持久化：tool 消息
                    tcData = event.data
                    toolResultsThisRound.append({
                        "call_id": tcData.get("call_id", ""),
                        "tool_name": tcData.get("tool_name", ""),
                        "output": tcData.get("output", ""),
                        "success": tcData.get("success", False),
                    })
                    self.sessionDao.addMessage(
                        sessionId, "tool",
                        content=str(tcData.get("output", "")),
                        traceId=traceId, roundIndex=roundIndex,
                        toolCallId=tcData.get("call_id", ""),
                        metadata={"tool_name": tcData.get("tool_name", "")},
                    )

                    # ── 特权提权事件检测 ──
                    tool_name = tcData.get("tool_name", "")
                    if tool_name == "submitElevation" and tcData.get("success"):
                        await self._handleElevationResult(sessionId, websocket, sendLock, tcData)
                    elif tool_name == "runPrivileged":
                        await self._send(websocket, sendLock, self._serverEvent(
                            "elevation.resolved", sessionId, tcData.get("trace_id"), {
                                "status": "approved" if tcData.get("success") else "failed",
                                "message": "特权命令已执行" if tcData.get("success") else "特权执行失败",
                            }
                        ))

                elif event.type == EventType.APPROVAL_REQUIRED:
                    self.sessionDao.updateStatus(sessionId, "waiting_approval")
                    # 持久化审批事件数据（WS 重连时恢复用）
                    self.sessionDao.updatePendingApproval(sessionId, {
                        "action_id": event.data.get("action_id", ""),
                        "tool_name": event.data.get("tool_name", ""),
                        "arguments": event.data.get("arguments", {}),
                        "reason": event.data.get("reason", ""),
                        "ai_reason": event.data.get("ai_reason", ""),
                        "call_id": event.data.get("call_id", ""),
                    })
                elif event.type == EventType.APPROVAL_RESOLVED:
                    self.sessionDao.updateStatus(sessionId, "running")
                    self.sessionDao.clearPendingApproval(sessionId)
                elif event.type == EventType.ERROR:
                    self.sessionDao.updateStatus(
                        sessionId, "error", lastError=str(event.data.get("message", ""))
                    )
                    self.sessionDao.clearPendingApproval(sessionId)
                elif event.type == EventType.CHOICE_REQUIRED:
                    self.sessionDao.updateStatus(sessionId, "waiting_choice")
                elif event.type == EventType.CHOICE_RESOLVED:
                    self.sessionDao.updateStatus(sessionId, "running")
                elif event.type == EventType.PLAN_PROPOSED:
                    self.sessionDao.updateStatus(sessionId, "waiting_plan")
                elif event.type == EventType.PLAN_APPROVED:
                    # 计划批准 → 模式已切换为 AGENT
                    self.sessionDao.updateMode(sessionId, "agent")
                    self.sessionDao.updateStatus(sessionId, "running")
                    # 更新 DB 中 tool 消息的内容
                    call_id = str(event.data.get("call_id", ""))
                    tool_response = str(event.data.get("tool_response", ""))
                    if call_id:
                        self.sessionDao.updateToolResponse(
                            sessionId, call_id, tool_response,
                        )
                    await self._send(websocket, sendLock, self._serverEvent(
                        "mode_changed", sessionId, traceId,
                        {"mode": "agent"}
                    ))
                elif event.type == EventType.PLAN_REJECTED:
                    self.sessionDao.updateStatus(sessionId, "running")
                    reason = str(event.data.get("reason", ""))
                    call_id = str(event.data.get("call_id", ""))
                    # 更新 DB 中 tool 消息的内容
                    if call_id:
                        new_content = f"[计划被拒绝] {reason}" if reason else "[计划被拒绝]"
                        self.sessionDao.updateToolResponse(
                            sessionId, call_id, new_content,
                        )
                    # 超时拒绝 → 模式已回退到 AGENT
                    if "超时" in reason:
                        self.sessionDao.updateMode(sessionId, "agent")
                        await self._send(websocket, sendLock, self._serverEvent(
                            "mode_changed", sessionId, traceId,
                            {"mode": "agent", "reason": reason}
                        ))
                elif event.type == EventType.TEXT_DONE:
                    # 纯文本回复完成时捕获 usage（有 tool_calls 时在 TOOL_CALLING 中已捕获）
                    if not usageThisRound:
                        usageThisRound = event.data.get("usage", {})
                elif event.type == EventType.DONE:
                    doneSent = True
                    self.sessionDao.clearPendingApproval(sessionId)

                await self._send(websocket, sendLock, self._formatAgentEvent(event))

            # ── 持久化 final assistant 文本 ──
            finalText = "".join(assistantParts).strip()
            if finalText:
                self.sessionDao.addMessage(
                    sessionId, "assistant", finalText,
                    traceId=traceId, roundIndex=roundIndex,
                )

            # ── 记录 token 用量 ──
            await self._recordTokenUsage(sessionId, traceId, session, usageThisRound)

            # ── 首轮自动生成标题（更新会话标题） ──
            if roundIndex == 1 and session and session.title in ("新 Agent 会话", "新会话", ""):
                asyncio.create_task(
                    self._autoGenerateTitle(sessionId, message, finalText, session)
                )

            self.sessionDao.updateStatus(sessionId, "idle")
            if not doneSent:
                await self._send(websocket, sendLock, self._serverEvent(
                    "done", sessionId, traceId, {}
                ))
        except asyncio.CancelledError:
            self.sessionDao.updateStatus(sessionId, "idle")
            # 注意：不断连时不清除 pendingApproval
            # WS 断连后 pendingApproval 仍然保留，重连时通过 approval.resume 恢复
            raise
        except Exception as exc:
            self.sessionDao.updateStatus(sessionId, "error", lastError=str(exc))
            self.sessionDao.clearPendingApproval(sessionId)
            await self._send(websocket, sendLock, self._serverEvent(
                "error", sessionId, traceId, {"message": str(exc)}
            ))
        finally:
            storedRuntime = self._runtimeSessions.get(sessionId)
            if runtime is not None and storedRuntime is runtime:
                self._runtimeSessions.pop(sessionId, None)
                runtime.close()
            current = self._turnTasks.get(sessionId)
            if current is asyncio.current_task():
                self._turnTasks.pop(sessionId, None)

    async def _recordTokenUsage(self, sessionId: str, traceId: str | None,
                                 session, usage: dict) -> None:
        """记录本轮 LLM 调用的 token 用量（含缓存命中统计）。"""
        if not usage:
            return
        inputTokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        outputTokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        if not inputTokens and not outputTokens:
            return
        # 提取缓存命中 tokens（DeepSeek / OpenAI 兼容格式）
        cachedInputTokens = (
            usage.get("prompt_cache_hit_tokens")
            or usage.get("prompt_tokens_details", {}).get("cached_tokens")
            or 0
        )
        # 获取模型名
        model = "unknown"
        try:
            profile = self.profileService.dao.getProfileById(session.profileId) if session.profileId else None
            if profile:
                model = profile.model
        except Exception:
            pass
        self.tokenUsageDao.recordUsage(
            sessionId=sessionId,
            model=model,
            inputTokens=int(inputTokens),
            outputTokens=int(outputTokens),
            cachedInputTokens=int(cachedInputTokens),
            traceId=traceId,
        )

    async def _autoGenerateTitle(self, sessionId: str, userMsg: str,
                                  response: str, session) -> None:
        """首轮对话后异步生成标题。

        重要：不调 normalize_endpoint() — createProvider 靠检测 endpoint
        中是否含 "/anthropic" 来自动选择 AnthropicProvider / OpenAIProvider。
        归一化会移除该标记导致 Provider 选错 + 路径重复（404）。
        """
        try:
            # ── 1. 获取 LLM 配置 ──
            llm_cfg = get_llm_config(session)
            endpoint = llm_cfg.get("endpoint", "")
            api_key = llm_cfg.get("api_key", "")
            model = llm_cfg.get("model", "deepseek-chat")

            if not endpoint or not api_key:
                _logger.warning(
                    "自动标题生成: LLM 配置不完整, 使用 fallback。"
                    "endpoint=%s api_key=%s", bool(endpoint), bool(api_key),
                )
                self._titleFallback(sessionId, userMsg)
                return

            # ── 2. 规整化端点（Provider 兼容）──
            # 规整规则：
            #   Anthropic 端点 (.../anthropic) → 不动，createProvider 自动检测
            #   DeepSeek 官方 (api.deepseek.com) → 裸域名，不用 /v1
            #   其他 → 加 /v1（OpenAI 标准路径前缀）
            # OpenAIProvider 内部会追加 /chat/completions，这里只给 BASE URL
            raw_endpoint = endpoint
            if "/anthropic" in endpoint:
                pass  # 让 createProvider 检测 /anthropic → AnthropicProvider
            elif "api.deepseek.com" in endpoint:
                # DeepSeek 官方地址: https://api.deepseek.com/chat/completions
                endpoint = "https://api.deepseek.com"
            else:
                endpoint = endpoint.rstrip("/")
                # 去掉已存在的 /chat/completions（provider 会再加）
                if endpoint.endswith("/chat/completions"):
                    endpoint = endpoint[: -len("/chat/completions")]
                # 确保有 /v1 前缀（其他厂商的 OpenAI 标准路径）
                if not endpoint.endswith("/v1"):
                    endpoint = endpoint + "/v1"

            _logger.info(
                "自动标题生成: raw_endpoint=%s -> normalized=%s model=%s is_anthropic=%s",
                raw_endpoint[:80], endpoint[:80], model, "/anthropic" in raw_endpoint,
            )

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
            _logger.info(
                "自动标题生成: provider=%s final_endpoint=%s",
                type(provider).__name__,
                getattr(provider, '_endpoint', '?'),
            )

            resp = await provider.chat([
                {"role": "system",
                 "content": "根据对话内容生成一个简洁的对话标题（10字~20字以内），只返回标题本身，不要加引号"},
                {"role": "user", "content": f"用户：{userMsg[:200]}"},
            ])
            title = (resp.content or "").strip().strip('"').strip("'")
            if title and len(title) <= 100:
                self.sessionDao.updateSessionTitle(sessionId, title)
                _logger.info(
                    "自动标题生成成功: session=%s title=%s", sessionId, title,
                )
                # ── 推送标题更新事件到前端 ──
                await self._pushTitleEvent(sessionId, title)
            else:
                self._titleFallback(sessionId, userMsg)
                _logger.info(
                    "自动标题生成: LLM 返回空标题, 使用 fallback。session=%s",
                    sessionId,
                )

        except Exception as e:
            _logger.warning(
                "自动标题生成失败: %s, 使用 fallback。session=%s", e, sessionId,
            )
            self._titleFallback(sessionId, userMsg)

    async def _titleFallback(self, sessionId: str, userMsg: str) -> None:
        """标题生成 fallback：用用户消息前 20 字作为标题。"""
        fallbackTitle = userMsg[:20].strip()
        if fallbackTitle:
            try:
                self.sessionDao.updateSessionTitle(sessionId, fallbackTitle)
                _logger.info(
                    "标题 fallback 成功: session=%s title=%s",
                    sessionId, fallbackTitle,
                )
                await self._pushTitleEvent(sessionId, fallbackTitle)
            except Exception as e:
                _logger.warning(
                    "标题 fallback 写入失败: session=%s error=%s",
                    sessionId, e,
                )

    async def _pushTitleEvent(self, sessionId: str, title: str) -> None:
        """向前端推送标题更新事件。"""
        pair = self._activeConns.get(sessionId)
        if pair is None:
            _logger.debug("_pushTitleEvent: session=%s 无活跃 WS 连接", sessionId)
            return
        websocket, sendLock = pair
        try:
            await self._send(websocket, sendLock, self._serverEvent(
                "title.updated", sessionId, None, {"title": title},
            ))
        except Exception as e:
            _logger.warning("_pushTitleEvent: session=%s 推送失败: %s", sessionId, e)

    def _getRuntimeSession(self, session) -> RuntimeAgentSession:
        runtime = self._runtimeSessions.get(session.sessionId)
        if runtime is not None:
            return runtime
        config = self.profileService.buildAgentConfig(
            session.profileId,
            safetyPolicy=session.safetyPolicy,
        )
        try:
            mode = AgentMode(session.mode)
        except ValueError:
            mode = AgentMode.AGENT
        runtime = RuntimeAgentSession(
            config=config,
            userId=str(session.userId),
            sessionId=session.sessionId,
            mode=mode,
            toolSource=session.toolSource,
            mcpServers=session.mcpServers,
        )
        self._runtimeSessions[session.sessionId] = runtime
        return runtime

    async def _cancelTurn(self, sessionId: str) -> None:
        runtime = self._runtimeSessions.pop(sessionId, None)
        if runtime is not None:
            runtime.close()
        task = self._turnTasks.pop(sessionId, None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

    def _isRunning(self, sessionId: str) -> bool:
        task = self._turnTasks.get(sessionId)
        if task is None:
            return False
        if task.done():
            self._turnTasks.pop(sessionId, None)
            return False
        return True

    @staticmethod
    async def _send(websocket: WebSocket, lock: asyncio.Lock,
                    payload: dict[str, Any]) -> None:
        async with lock:
            await websocket.send_json(payload)

    @staticmethod
    def _formatAgentEvent(event: AgentEvent) -> dict[str, Any]:
        eventType = event.type.value if hasattr(event.type, "value") else str(event.type)
        return {
            "type": eventType,
            "sessionId": event.session_id,
            "traceId": event.trace_id,
            "timestamp": event.timestamp,
            "data": event.data,
        }

    @staticmethod
    def _serverEvent(eventType: str, sessionId: str,
                     traceId: str | None, data: dict[str, Any]) -> dict[str, Any]:
        import time

        return {
            "type": eventType,
            "sessionId": sessionId,
            "traceId": traceId,
            "timestamp": time.time(),
            "data": data,
        }

    async def pushElevationEvent(self, sessionId: str, eventType: str, data: dict) -> bool:
        """向指定 session 推送特权提权事件。"""
        pair = self._activeConns.get(sessionId)
        if pair is None:
            _logger.warning("pushElevationEvent: session=%s 无活跃连接", sessionId)
            return False
        websocket, sendLock = pair
        try:
            await self._send(websocket, sendLock, self._serverEvent(
                eventType, sessionId, None, data,
            ))
            return True
        except Exception:
            _logger.exception("pushElevationEvent: session=%s 推送失败", sessionId)
            self._activeConns.pop(sessionId, None)
            return False

    async def _handleElevationResult(
        self, sessionId: str, websocket: WebSocket,
        sendLock: asyncio.Lock, tcData: dict,
    ) -> None:
        """处理 submitElevation 工具结果：推送 WS 事件 + 同步到本地 ElevationService。"""
        import json

        tool_output = tcData.get("output", "")
        try:
            result_data = json.loads(tool_output) if isinstance(tool_output, str) else {}
        except (json.JSONDecodeError, TypeError):
            _logger.warning("_handleElevationResult: 无法解析 tool output")
            return

        code = result_data.get("code")
        commands = result_data.get("commands", [])
        reason = result_data.get("reason", "")
        if not code or not commands:
            _logger.warning("_handleElevationResult: 缺少 code 或 commands")
            return

        # 同步到本地 ElevationService（CLI approve 时查找用）
        elevation = ElevationService()
        entry = elevation.get_code(code)
        if entry is None:
            # 提取双通道字段
            inline_cmd = result_data.get("inline_cmd", "")
            script_path = result_data.get("script_path", "")

            # 双通道 hash 计算（runPrivileged / 特权代理校验时使用）
            from privileged_agent.crypto import hash_payload as _hash_payload
            inline_cmd_hash = (
                _hash_payload({"cmd": inline_cmd}) if inline_cmd else None
            )
            script_hash = None
            if script_path:
                try:
                    _script_content = Path(script_path).read_text(
                        encoding="utf-8", errors="ignore"
                    )
                    script_hash = _hash_payload({"content": _script_content})
                except (OSError, FileNotFoundError):
                    _logger.warning(
                        "script_hash: 无法读取脚本文件 %s，script_hash 将为空",
                        script_path,
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
                "elevation: code=%s 已同步到 Gateway ElevationService (inline=%s script=%s)",
                code, bool(inline_cmd), bool(script_path),
            )

        # 推送 WS 事件到前端
        ws_data = {
            "code": code,
            "commands": commands,
            "reason": reason,
            "ttl_seconds": result_data.get("ttl_seconds", 3600),
            "max_ops": result_data.get("max_ops", 10),
            "message": f"Agent 请求特权操作，请在 SSH 执行: sudo nereus approve {code}",
        }
        if inline_cmd:
            ws_data["inline_cmd"] = inline_cmd
        if script_path:
            ws_data["script_path"] = script_path
        await self._send(websocket, sendLock, self._serverEvent(
            "elevation.requested", sessionId, tcData.get("trace_id"), ws_data,
        ))

    @staticmethod
    def _newSessionId() -> str:
        from agent.shared.id_gen import gen_session_id

        return gen_session_id()
