"""事件流 — 管理 AgentEvent 的生产和消费。"""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
from agent.shared.types import AgentEvent, EventType
from agent.shared.id_gen import gen_trace_id


class EventStream:
    """Agent 事件流 — 基于 asyncio.Queue 的生产者-消费者模式。"""

    def __init__(self, sessionId: str):
        self._sessionId = sessionId
        self._traceId = gen_trace_id()
        self._queue: asyncio.Queue[AgentEvent] = asyncio.Queue()
        self._closed = False

    @property
    def traceId(self) -> str:
        return self._traceId

    def emit(self, eventType: EventType, data: dict | None = None) -> None:
        """同步发送事件（在 async 上下文中调用）。"""
        self._queue.put_nowait(AgentEvent(
            type=eventType, session_id=self._sessionId,
            trace_id=self._traceId, data=data or {},
        ))

    async def aEmit(self, eventType: EventType, data: dict | None = None) -> None:
        """异步发送事件。"""
        await self._queue.put(AgentEvent(
            type=eventType, session_id=self._sessionId,
            trace_id=self._traceId, data=data or {},
        ))

    async def __aiter__(self) -> AsyncIterator[AgentEvent]:
        """消费事件流。"""
        while True:
            ev = await self._queue.get()
            yield ev
            if ev.type == EventType.DONE or ev.type == EventType.ERROR:
                break

    def close(self) -> None:
        """关闭流。"""
        if not self._closed:
            self._closed = True
            self.emit(EventType.DONE, {"reason": "closed"})
