from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from agent.agent_router.router import AgentMode
from agent.integration.session import AgentSession as RuntimeAgentSession
from agent.shared.types import AgentEvent, EventType
from agent.config_envs.loader import loadConfig
from agent.llm_providers.factory import createProvider
from agent.shared.types import AgentConfig
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.AgentSessionDaoOrm import AgentSessionDaoOrm
from gateway.dao.AgentTokenUsageDaoOrm import AgentTokenUsageDaoOrm
from gateway.service.AgentLlmProfileService import AgentLlmProfileService
from gateway.service.elevation_service import ElevationService
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
        """首轮对话后异步生成标题（静默失败）。"""
        try:
            # 获取当前 model 配置
            profile = None
            try:
                profile = self.profileService.dao.getProfileById(session.profileId) if session.profileId else None
            except Exception:
                pass
            if profile is None:
                profile = self.profileService.dao.getDefaultProfile()

            import os as _os
            endpoint = ""
            apiKey = ""
            model = "deepseek-chat"
            if profile:
                cred = self.profileService.dao.getCredentialById(profile.credentialId) if profile.credentialId else None
                if cred and cred.baseUrl:
                    endpoint = cred.baseUrl
                    apiKey = cred.apiKey
                    model = profile.model

            if not endpoint:
                # fallback: 从配置文件获取
                try:
                    cfg = loadConfig()
                    endpoint = cfg.llm_endpoint
                    model = cfg.llm_model
                    apiKey = cfg.llm_api_key
                except Exception:
                    return

            titleConfig = AgentConfig(
                llm_endpoint=endpoint,
                llm_model=model,
                llm_max_tokens=20,
                llm_temperature=0.0,
                llm_retry_count=0,
                llm_retry_delay=0.0,
            )
            titleConfig.llm_api_key = apiKey

            provider = createProvider(titleConfig)
            resp = await provider.chat([
                {"role": "system",
                 "content": "根据对话内容生成一个简洁的对话标题（10字以内），只返回标题本身，不要加引号"},
                {"role": "user", "content": f"用户：{userMsg[:200]}"},
            ])
            title = (resp.content or "").strip().strip('"').strip("'")
            if title and len(title) <= 100:
                self.sessionDao.updateSessionTitle(sessionId, title)
        except Exception:
            import logging
            logging.getLogger("ndlmpanel.gateway").debug(
                "自动标题生成失败（静默忽略）", exc_info=True)

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
            elevation.generate_code(
                session_id=sessionId,
                commands=commands,
                reason=reason,
                ttl_seconds=int(result_data.get("ttl_seconds", 3600)),
                max_ops=int(result_data.get("max_ops", 10)),
                code=code,  # 使用 MCP 子进程生成的 code，不重新随机生成
            )
            _logger.info("elevation: code=%s 已同步到 Gateway ElevationService", code)

        # 推送 WS 事件到前端
        await self._send(websocket, sendLock, self._serverEvent(
            "elevation.requested", sessionId, tcData.get("trace_id"), {
                "code": code,
                "commands": commands,
                "reason": reason,
                "ttl_seconds": result_data.get("ttl_seconds", 3600),
                "max_ops": result_data.get("max_ops", 10),
                "message": f"Agent 请求特权操作，请在 SSH 执行: sudo nereus approve {code}",
            }
        ))

    @staticmethod
    def _newSessionId() -> str:
        from agent.shared.id_gen import gen_session_id

        return gen_session_id()
