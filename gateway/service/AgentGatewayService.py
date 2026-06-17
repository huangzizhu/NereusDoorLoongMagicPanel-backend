"""Agent WebSocket Gateway — 事件消费者（S6：WS 解耦版）。

S6 架构变更：
- Agent 生命周期从 WS 解绑 → 由 BackgroundRunner 管理
- WS 只负责：提交消息、接收事件流推送、审批/计划/选择题交互
- WS 断开不再杀死 agent — agent 在后台继续运行
- 重连时从 EventBuffer 重放积压事件
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import WebSocket

from agent.agent_router.router import AgentMode
from agent.shared.types import AgentEvent
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.AgentSessionDaoOrm import AgentSessionDaoOrm
from gateway.dao.AgentTokenUsageDaoOrm import AgentTokenUsageDaoOrm
from gateway.service.AgentLlmProfileService import AgentLlmProfileService
from gateway.service.AgentBackgroundRunner import BackgroundRunner
from gateway.service.AgentEventBuffer import AgentEventBuffer
from gateway.service.elevation_service import ElevationService
from pojo.Agent import AgentSessionCreate

_logger = logging.getLogger("ndlmpanel.gateway")


class AgentGatewayService(Singleton):
    """Agent WebSocket 网关服务（WS 解耦版）。

    WS handler 是事件的消费者，不再持有 Agent 生命周期。
    Agent 在 BackgroundRunner 中独立运行。
    """

    @singletonInit
    def __init__(self):
        self.sessionDao = AgentSessionDaoOrm()
        self.profileService = AgentLlmProfileService()
        self.tokenUsageDao = AgentTokenUsageDaoOrm()

        # ── S6：后台执行器（替代旧的 _runtimeSessions / _turnTasks）──
        self._runner = BackgroundRunner(
            self.sessionDao, self.profileService, self.tokenUsageDao,
        )

        # WS 连接追踪
        self._sendLocks: dict[str, asyncio.Lock] = {}
        self._activeConns: dict[str, tuple[WebSocket, asyncio.Lock]] = {}
        # 事件流任务追踪（sessionId → asyncio.Task）
        self._streamTasks: dict[str, asyncio.Task] = {}
        # ── 每 session 已推送的最大 _seq，用于重连时跳过已看事件 ──
        self._lastPushedSeq: dict[str, int] = {}

    # ── 公开 API（供 AgentSessionService 等外部调用）──

    def invalidateRuntime(self, sessionId: str) -> None:
        """使缓存的 RuntimeSession 失效（如切换 toolSource/model 后调用）。

        S6：委托给 BackgroundRunner.cleanSession()。
        """
        self._runner.cleanSession(sessionId)

    def switchToolSource(self, sessionId: str, toolSource: str,
                         mcpServers: list[dict] | None = None) -> None:
        """切换工具来源并重建 runtime。"""
        self._runner.cleanSession(sessionId)

    def switchMode(self, sessionId: str, mode: AgentMode) -> bool:
        """切换 Agent 运行模式（即时生效）。"""
        return self._runner.switchMode(sessionId, mode)

    # ── WebSocket Handler ──

    async def handleWebSocket(self, websocket: WebSocket, userId: int,
                              sessionId: str | None = None) -> None:
        """处理 WebSocket 连接（S6：WS 解耦版）。

        WS 生命周期与 Agent 生命周期解耦：
        - 连接时：从 EventBuffer 重放积压事件
        - 消息循环：通过 BackgroundRunner 提交 / 审批 / 选择
        - 断开时：只清理 WS 资源，不杀 agent
        """
        created = False
        if sessionId:
            session = self.sessionDao.getSession(sessionId, userId)
            if session is None:
                await websocket.send_json(self._serverEvent(
                    "error", sessionId, None, {
                        "message": f"不存在 sessionId 为 {sessionId} 的 Agent 会话",
                    },
                ))
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

        # ── S6：检查 agent 运行状态 ──
        agentRunning = self._runner.isRunning(sessionId)
        agentStatus = self.sessionDao.getSessionStatus(sessionId) or "idle"

        # ── 发送就绪事件（含运行状态）──
        await self._send(websocket, sendLock, self._serverEvent(
            "agent.ready", sessionId, None, {
                "sessionId": sessionId,
                "agentRunning": agentRunning,
                "status": agentStatus,
            },
        ))
        if created:
            await self._send(websocket, sendLock, self._serverEvent(
                "session.created", sessionId, None, {"sessionId": sessionId},
            ))

        # ── S6：重连恢复 — 从 EventBuffer 重放积压事件 ──
        buffer = self._runner.getBuffer(sessionId)
        if buffer:
            state = await buffer.getState()
            # ── 游标：只重放 _seq > lastPushedSeq 的事件（跳过已看过的）──
            lastSeq = self._lastPushedSeq.get(sessionId, -1)
            backlog = await buffer.readSince(lastSeq)

            # ── 积压去重：多个 approval.required / choice.required 只保留最后一个 ──
            lastApprovalRequiredIdx: int = -1
            lastChoiceRequiredIdx: int = -1
            for i, event in enumerate(backlog):
                if event.get("type") == "approval.required":
                    lastApprovalRequiredIdx = i
                if event.get("type") == "choice.required":
                    lastChoiceRequiredIdx = i

            for i, event in enumerate(backlog):
                if (event.get("type") == "approval.required"
                        and i != lastApprovalRequiredIdx):
                    continue
                if (event.get("type") == "choice.required"
                        and i != lastChoiceRequiredIdx):
                    continue
                await self._send(websocket, sendLock, event)
                # ── 更新游标 ──
                seq = event.get("_seq", 0)
                if seq > self._lastPushedSeq.get(sessionId, -1):
                    self._lastPushedSeq[sessionId] = seq

            # 如果 agent 已跑完 → 告知前端当前状态
            if state["done"]:
                if state.get("finalStatus") == "idle":
                    await self._send(websocket, sendLock, self._serverEvent(
                        "agent.ready", sessionId, None,
                        {"sessionId": sessionId, "status": "idle"},
                    ))

        # ── 审批恢复：检测 DB 中残留的待审批事件 ──
        # （兼容旧架构残留 + agent 超时后的情况）
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
                },
            ))

        # ── 选择题恢复：检测 DB 中残留的待回复选择题 ──
        pending_choice = self.sessionDao.getPendingChoice(sessionId)
        if pending_choice:
            _logger.info(
                "WS 重连检测到待回复选择题: session=%s question=%s",
                sessionId, pending_choice.get("question", "")[:50],
            )
            await self._send(websocket, sendLock, self._serverEvent(
                "choice.resume", sessionId, None, {
                    "message": "检测到上次断连时有待回复选择题，请继续回答",
                    "choice": pending_choice,
                },
            ))

        # ── 消息处理循环 ──
        try:
            while True:
                payload = await websocket.receive_json()
                msgType = payload.get("type")

                if msgType == "ping":
                    # ── S6：pong 返回 agent 运行状态 ──
                    await self._send(websocket, sendLock, self._serverEvent(
                        "pong", sessionId, None, {
                            "agentRunning": self._runner.isRunning(sessionId),
                            "status": self.sessionDao.getSessionStatus(sessionId) or "idle",
                        },
                    ))

                elif msgType == "user_message":
                    message = str(payload.get("message") or "")
                    if not message.strip():
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None,
                            {"message": "message 不能为空"},
                        ))
                        continue

                    # ── S6：通过 BackgroundRunner 提交（不再直接 _runTurn）──
                    if self._runner.isRunning(sessionId):
                        # 已有 agent 在跑 → 消息排队
                        buffer = await self._runner.submit(
                            userId, sessionId, message,
                        )
                        await self._send(websocket, sendLock, self._serverEvent(
                            "agent.queued", sessionId, None, {
                                "message": "Agent 正在执行上一轮任务，"
                                           "新消息已排队，完成后自动处理",
                            },
                        ))
                    else:
                        buffer = await self._runner.submit(
                            userId, sessionId, message,
                        )
                        # 启动事件流任务：从 buffer 实时消费事件推送 WS
                        task = asyncio.create_task(
                            self._streamEvents(
                                websocket, sendLock, sessionId, buffer,
                            )
                        )
                        self._streamTasks[sessionId] = task

                elif msgType == "approval":
                    actionId = str(payload.get("actionId") or "")
                    approved = bool(payload.get("approved"))
                    reason = str(payload.get("reason") or "")

                    # ── S6：通过 BackgroundRunner 处理审批 ──
                    ok = False
                    if approved:
                        ok = self._runner.approve(sessionId, actionId)
                    else:
                        ok = self._runner.reject(sessionId, actionId, reason)

                    # ── 回退路径：runtime 不存在但 DB 有残留 ──
                    if not ok and actionId:
                        ok = await self._handleApprovalResume(
                            websocket, sendLock, userId, sessionId,
                            actionId, approved, reason,
                        )
                    if not ok:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None,
                            {"message": "审批动作不存在或已处理"},
                        ))

                    # ── 无论成功/失败，确保 _streamEvents 在消费 ──
                    # （agent 可能仍在跑，后续事件不能丢）
                    await self._ensureStreamEvents(
                        websocket, sendLock, sessionId,
                    )

                elif msgType == "plan":
                    approved = bool(payload.get("approved"))
                    reason = str(payload.get("reason") or "")
                    ok = False
                    if approved:
                        ok = self._runner.approvePlan(sessionId)
                    else:
                        ok = self._runner.rejectPlan(sessionId, reason)
                    if not ok:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None,
                            {"message": "无待审批的计划或计划已处理"},
                        ))
                    elif ok:
                        await self._ensureStreamEvents(
                            websocket, sendLock, sessionId,
                        )

                elif msgType == "choice":
                    actionId = str(payload.get("actionId") or "")
                    selectionId = str(payload.get("selectionId") or "")
                    customInput = str(payload.get("customInput") or "")
                    ok = self._runner.resolveChoice(
                        sessionId, actionId, selectionId, customInput,
                    )

                    # ── 回退路径：runtime 不存在但 DB 有残留 ──
                    if not ok and actionId:
                        ok = await self._handleChoiceResume(
                            websocket, sendLock, sessionId,
                            actionId, selectionId, customInput,
                        )

                    if not ok:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None,
                            {"message": "无待回复的选择题或已处理"},
                        ))
                    elif ok:
                        await self._ensureStreamEvents(
                            websocket, sendLock, sessionId,
                        )

                elif msgType == "switch_mode":
                    mode_str = str(payload.get("mode") or "")
                    try:
                        target_mode = AgentMode(mode_str)
                    except ValueError:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "error", sessionId, None,
                            {"message": f"不支持的模式: {mode_str}"},
                        ))
                        continue

                    self.sessionDao.updateMode(sessionId, target_mode.value)

                    if self._runner.switchMode(sessionId, target_mode):
                        await self._send(websocket, sendLock, self._serverEvent(
                            "mode_changed", sessionId, None,
                            {"mode": target_mode.value},
                        ))
                    else:
                        await self._send(websocket, sendLock, self._serverEvent(
                            "mode_changed", sessionId, None,
                            {"mode": target_mode.value,
                             "effective": "next_turn"},
                        ))

                elif msgType == "cancel":
                    await self._runner.cancel(sessionId)
                    self.sessionDao.updateStatus(sessionId, "idle")
                    self.sessionDao.clearPendingApproval(sessionId)
                    # 取消事件流任务
                    task = self._streamTasks.pop(sessionId, None)
                    if task and not task.done():
                        task.cancel()
                    await self._send(websocket, sendLock, self._serverEvent(
                        "done", sessionId, None, {"reason": "cancelled"},
                    ))

                else:
                    await self._send(websocket, sendLock, self._serverEvent(
                        "error", sessionId, None,
                        {"message": f"不支持的 Agent 消息类型: {msgType}"},
                    ))

        finally:
            # ── S6：WS 断开只清理 WS 资源，不杀 agent ──
            streamTask = self._streamTasks.pop(sessionId, None)
            if streamTask and not streamTask.done():
                streamTask.cancel()

            # 移除活跃连接记录
            self._activeConns.pop(sessionId, None)

            # 无人连接 + agent 不在运行 → 标记 completed_unread
            if (self._countWsConnections(sessionId) == 0
                    and not self._runner.isRunning(sessionId)):
                session_status = self.sessionDao.getSessionStatus(sessionId)
                if session_status == "idle":
                    self.sessionDao.updateStatus(
                        sessionId, "completed_unread",
                    )

    # ── 事件流推送 ──

    async def _streamEvents(
        self, websocket: WebSocket, sendLock: asyncio.Lock,
        sessionId: str, buffer: AgentEventBuffer,
    ) -> None:
        """从 EventBuffer 持续推送事件到 WS。

        每 100ms 轮询一次 buffer 的实时队列。
        直到 agent 完成（buffer.done）或 WS 断开。
        """
        try:
            while True:
                state = await buffer.getState()

                # 从实时队列消费事件
                queue = await buffer.getQueue()
                try:
                    while True:
                        event = queue.get_nowait()
                        # ── 去重：跳过 backlog 重放已发过的事件 ──
                        seq = event.get("_seq", 0)
                        lastKnown = self._lastPushedSeq.get(sessionId, -1)
                        if seq <= lastKnown:
                            queue.task_done()
                            continue
                        await self._send(websocket, sendLock, event)
                        queue.task_done()
                        # ── 更新游标 ──
                        if seq > lastKnown:
                            self._lastPushedSeq[sessionId] = seq

                        # ── 特权提权事件特殊处理 ──
                        eventType = event.get("type", "")
                        data = event.get("data", {})
                        if eventType == "tool.result":
                            tool_name = data.get("tool_name", "")
                            try:
                                if tool_name == "submitElevation" and data.get(
                                    "success"
                                ):
                                    await self._handleElevationResult(
                                        sessionId, websocket, sendLock, data,
                                    )
                                elif tool_name == "runPrivileged":
                                    await self._send(
                                        websocket, sendLock,
                                        self._serverEvent(
                                            "elevation.resolved", sessionId,
                                            data.get("trace_id"), {
                                                "status": (
                                                    "approved"
                                                    if data.get("success")
                                                    else "failed"
                                                ),
                                                "message": (
                                                    "特权命令已执行"
                                                    if data.get("success")
                                                    else "特权执行失败"
                                                ),
                                            },
                                        ),
                                    )
                            except Exception:
                                _logger.exception(
                                    "_streamEvents: 处理特权事件异常 "
                                    "session=%s tool=%s",
                                    sessionId, tool_name,
                                )

                except asyncio.QueueEmpty:
                    pass

                if state["done"]:
                    await self._send(websocket, sendLock, self._serverEvent(
                        "done", sessionId, None, {},
                    ))
                    break

                await asyncio.sleep(0.1)  # 100ms 轮询间隔

        except asyncio.CancelledError:
            pass  # WS 断开，正常退出

    # ── 审批恢复路径（兼容旧架构残留）──

    async def _handleApprovalResume(
        self, websocket: WebSocket, sendLock: asyncio.Lock,
        userId: int, sessionId: str, actionId: str,
        approved: bool, reason: str,
    ) -> bool:
        """处理 WS 重连后的审批恢复（runtime 不存在但 DB 有残留 pending）。

        S6 中此路径仅在 agent 已超时/崩溃时触发。
        """
        pending = self.sessionDao.getPendingApproval(sessionId)
        if not pending or pending.get("action_id") != actionId:
            return False

        tool_name = pending.get("tool_name", "")
        tool_args = pending.get("arguments", {})
        _logger.info(
            "WS 重连审批恢复: session=%s action=%s tool=%s approved=%s",
            sessionId, actionId, tool_name, approved,
        )

        execution_ok = False
        execution_output = ""
        if approved:
            try:
                session_obj = self.sessionDao.getSession(sessionId, userId)
                if session_obj is not None:
                    # 临时创建 runtime 执行工具
                    from agent.agent_router.router import AgentMode
                    from agent.integration.session import (
                        AgentSession as RuntimeAgentSession,
                    )
                    config = self.profileService.buildAgentConfig(
                        session_obj.profileId,
                        safetyPolicy=session_obj.safetyPolicy,
                    )
                    try:
                        mode = AgentMode(session_obj.mode)
                    except ValueError:
                        mode = AgentMode.AGENT
                    exec_runtime = RuntimeAgentSession(
                        config=config,
                        userId=str(userId),
                        sessionId=sessionId,
                        mode=mode,
                        toolSource=session_obj.toolSource,
                        mcpServers=session_obj.mcpServers,
                    )
                    execution_output = await exec_runtime._core._executeTool(
                        tool_name, tool_args,
                    )
                    execution_ok = True
                    exec_runtime.close()
            except Exception as exc:
                execution_output = str(exc)
                execution_ok = False
        else:
            execution_output = (
                f"[用户拒绝] 工具 {tool_name} 未执行。原因: {reason}"
            )

        # 写入 tool 结果到 DB
        self.sessionDao.addMessage(
            sessionId, "tool",
            content=str(execution_output)[:2000],
            roundIndex=self.sessionDao.getNextRoundIndex(sessionId),
            toolCallId=pending.get("call_id", actionId),
            metadata={"tool_name": tool_name},
        )
        self.sessionDao.clearPendingApproval(sessionId)
        self.sessionDao.updateStatus(sessionId, "idle")

        # ── 发送事件 ──
        await self._send(websocket, sendLock, self._serverEvent(
            "approval.resolved", sessionId, None, {
                "action_id": actionId,
                "approved": approved,
                "reason": reason,
            },
        ))
        await self._send(websocket, sendLock, self._serverEvent(
            "tool.result", sessionId, None, {
                "call_id": pending.get("call_id", actionId),
                "tool_name": tool_name,
                "success": execution_ok,
                "output": str(execution_output)[:2000],
            },
        ))

        # ── 批准且执行成功 → 推送 done（此路径无后台 agent 运行）──
        if approved and execution_ok:
            # 注意：不调 submit("")，避免空消息触发 agent 异常行为
            # 用户可手动发下一条消息继续对话
            await self._send(websocket, sendLock, self._serverEvent(
                "agent.ready", sessionId, None, {
                    "sessionId": sessionId,
                    "agentRunning": False,
                    "status": "idle",
                },
            ))
        await self._send(websocket, sendLock, self._serverEvent(
            "done", sessionId, None, {},
        ))

        return True

    # ── 选择题恢复路径（兼容 runtime 不存在但 DB 有残留）──

    async def _handleChoiceResume(
        self, websocket: WebSocket, sendLock: asyncio.Lock,
        sessionId: str, actionId: str,
        selectionId: str, customInput: str,
    ) -> bool:
        """处理 WS 重连后的选择题恢复（runtime 不存在但 DB 有残留 pending）。

        S6 中此路径仅在 agent 已超时/崩溃时触发。
        """
        pending = self.sessionDao.getPendingChoice(sessionId)
        if not pending or pending.get("action_id") != actionId:
            return False

        _logger.info(
            "WS 重连选择题恢复: session=%s action=%s selection=%s",
            sessionId, actionId, selectionId,
        )

        # 写入选择题结果到 DB
        result = json.dumps({
            "selection_id": selectionId,
            "custom_input": customInput,
        }, ensure_ascii=False)
        self.sessionDao.addMessage(
            sessionId, "tool",
            content=result[:2000],
            roundIndex=self.sessionDao.getNextRoundIndex(sessionId),
            toolCallId=pending.get("call_id", actionId),
            metadata={"tool_name": "ask_choice"},
        )
        self.sessionDao.clearPendingChoice(sessionId)
        self.sessionDao.updateStatus(sessionId, "idle")

        # ── 发送事件 ──
        await self._send(websocket, sendLock, self._serverEvent(
            "choice.resolved", sessionId, None, {
                "action_id": actionId,
                "selection_id": selectionId,
                "custom_input": customInput,
            },
        ))
        await self._send(websocket, sendLock, self._serverEvent(
            "tool.result", sessionId, None, {
                "call_id": pending.get("call_id", actionId),
                "tool_name": "ask_choice",
                "success": True,
                "output": result[:2000],
            },
        ))
        await self._send(websocket, sendLock, self._serverEvent(
            "agent.ready", sessionId, None, {
                "sessionId": sessionId,
                "agentRunning": False,
                "status": "idle",
            },
        ))
        await self._send(websocket, sendLock, self._serverEvent(
            "done", sessionId, None, {},
        ))

        return True

    # ── 特权提权事件处理 ──

    async def _handleElevationResult(
        self, sessionId: str, websocket: WebSocket,
        sendLock: asyncio.Lock, tcData: dict,
    ) -> None:
        """处理 submitElevation 工具结果：推送 WS 事件 + 同步到本地 ElevationService。"""
        import json

        tool_output = tcData.get("output", "")
        try:
            result_data = (
                json.loads(tool_output)
                if isinstance(tool_output, str) else {}
            )
        except (json.JSONDecodeError, TypeError):
            _logger.warning("_handleElevationResult: 无法解析 tool output")
            return

        code = result_data.get("code")
        commands = result_data.get("commands", [])
        reason = result_data.get("reason", "")
        if not code or not commands:
            _logger.warning("_handleElevationResult: 缺少 code 或 commands")
            return

        elevation = ElevationService()
        entry = elevation.get_code(code)
        # 提取双通道字段（必须在 if entry is None 之前定义，供后续 ws_data 使用）
        inline_cmd = result_data.get("inline_cmd", "")
        script_path = result_data.get("script_path", "")
        if entry is None:
            from privileged_agent.crypto import (
                hash_payload as _hash_payload,
            )
            inline_cmd_hash = (
                _hash_payload({"cmd": inline_cmd}) if inline_cmd else None
            )
            script_hash = None
            if script_path:
                try:
                    _script_content = Path(script_path).read_text(
                        encoding="utf-8", errors="ignore",
                    )
                    script_hash = _hash_payload(
                        {"content": _script_content},
                    )
                except (OSError, FileNotFoundError):
                    _logger.warning(
                        "script_hash: 无法读取脚本文件 %s，"
                        "script_hash 将为空",
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
                "elevation: code=%s 已同步到 Gateway ElevationService "
                "(inline=%s script=%s)",
                code, bool(inline_cmd), bool(script_path),
            )

        ws_data = {
            "code": code,
            "commands": commands,
            "reason": reason,
            "ttl_seconds": result_data.get("ttl_seconds", 3600),
            "max_ops": result_data.get("max_ops", 10),
            "message": (
                f"Agent 请求特权操作，"
                f"请在 SSH 执行: sudo nereus approve {code}"
            ),
        }
        if inline_cmd:
            ws_data["inline_cmd"] = inline_cmd
        if script_path:
            ws_data["script_path"] = script_path
        await self._send(websocket, sendLock, self._serverEvent(
            "elevation.requested", sessionId,
            tcData.get("trace_id"), ws_data,
        ))

    # ── 公共推送 API ──

    async def pushElevationEvent(
        self, sessionId: str, eventType: str, data: dict,
    ) -> bool:
        """向指定 session 推送特权提权事件。"""
        pair = self._activeConns.get(sessionId)
        if pair is None:
            _logger.warning(
                "pushElevationEvent: session=%s 无活跃连接", sessionId,
            )
            return False
        websocket, sendLock = pair
        try:
            await self._send(websocket, sendLock, self._serverEvent(
                eventType, sessionId, None, data,
            ))
            return True
        except Exception:
            _logger.exception(
                "pushElevationEvent: session=%s 推送失败", sessionId,
            )
            self._activeConns.pop(sessionId, None)
            return False

    async def _pushTitleEvent(self, sessionId: str, title: str) -> None:
        """向前端推送标题更新事件。

        S6 保留：BackgroundRunner 也会推送 title.updated 到 buffer，
        此方法作为补充（直接推送，无需等待 buffer 轮询）。
        """
        pair = self._activeConns.get(sessionId)
        if pair is None:
            return
        websocket, sendLock = pair
        try:
            await self._send(websocket, sendLock, self._serverEvent(
                "title.updated", sessionId, None, {"title": title},
            ))
        except Exception as e:
            _logger.warning(
                "_pushTitleEvent: session=%s 推送失败: %s", sessionId, e,
            )

    # ── 事件流保活 ──

    async def _ensureStreamEvents(
        self, websocket: WebSocket, sendLock: asyncio.Lock,
        sessionId: str,
    ) -> None:
        """确保 _streamEvents 在运行（审批/计划/选择题成功后调用）。

        如果已有活跃的 stream task → no-op。
        如果没有 → 创建新的，订阅当前 buffer。
        """
        existing = self._streamTasks.get(sessionId)
        if existing and not existing.done():
            return  # 已在运行

        buffer = self._runner.getBuffer(sessionId)
        if buffer is None:
            return

        task = asyncio.create_task(
            self._streamEvents(websocket, sendLock, sessionId, buffer),
        )
        self._streamTasks[sessionId] = task

    # ── WS 连接计数 ──

    def _countWsConnections(self, sessionId: str) -> int:
        """统计指定 session 的活跃 WS 连接数。"""
        return 1 if sessionId in self._activeConns else 0

    # ── 静态工具方法 ──

    @staticmethod
    async def _send(websocket: WebSocket, lock: asyncio.Lock,
                    payload: dict[str, Any]) -> None:
        async with lock:
            await websocket.send_json(payload)

    @staticmethod
    def _formatAgentEvent(event: AgentEvent) -> dict[str, Any]:
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

    @staticmethod
    def _serverEvent(eventType: str, sessionId: str,
                     traceId: str | None,
                     data: dict[str, Any]) -> dict[str, Any]:
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
