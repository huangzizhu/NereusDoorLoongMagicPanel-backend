from __future__ import annotations

import asyncio
import json
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
from pojo.Agent import AgentSessionCreate


class AgentGatewayService(Singleton):
    @singletonInit
    def __init__(self):
        self.sessionDao = AgentSessionDaoOrm()
        self.profileService = AgentLlmProfileService()
        self.tokenUsageDao = AgentTokenUsageDaoOrm()
        self._runtimeSessions: dict[str, RuntimeAgentSession] = {}
        self._turnTasks: dict[str, asyncio.Task] = {}
        self._sendLocks: dict[str, asyncio.Lock] = {}

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
        await self._send(websocket, sendLock, self._serverEvent(
            "agent.ready", sessionId, None, {"sessionId": sessionId}
        ))
        if created:
            await self._send(websocket, sendLock, self._serverEvent(
                "session.created", sessionId, None, {"sessionId": sessionId}
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

                elif event.type == EventType.APPROVAL_REQUIRED:
                    self.sessionDao.updateStatus(sessionId, "waiting_approval")
                elif event.type == EventType.APPROVAL_RESOLVED:
                    self.sessionDao.updateStatus(sessionId, "running")
                elif event.type == EventType.ERROR:
                    self.sessionDao.updateStatus(
                        sessionId, "error", lastError=str(event.data.get("message", ""))
                    )
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
            raise
        except Exception as exc:
            self.sessionDao.updateStatus(sessionId, "error", lastError=str(exc))
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

    @staticmethod
    def _newSessionId() -> str:
        from agent.shared.id_gen import gen_session_id

        return gen_session_id()
