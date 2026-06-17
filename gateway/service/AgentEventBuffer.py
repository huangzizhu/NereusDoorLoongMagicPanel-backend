"""Agent 事件环形缓冲区。

特性：
- 有容量上限（默认 1000 条事件）
- 超出上限时丢弃最旧的事件（FIFO）
- 支持从指定偏移量开始读取（重连追进度）
- 线程安全（通过 asyncio.Lock）
- 双重存储：asyncio.Queue（实时消费）+ deque（重放 / 积压读取）
"""
from __future__ import annotations
import asyncio
import time
from collections import deque
from typing import Any


class AgentEventBuffer:
    """Agent 事件缓冲区 — 解耦 Agent 生产者与 WS 消费者。

    每条事件自动附加 _seq（全局单调递增序列号）和 _ts（时间戳），
    支持客户端通过 lastSeq 精确定位断连期间的事件。
    """

    def __init__(self, maxSize: int = 1000):
        self._maxSize = maxSize
        self._events: deque[dict[str, Any]] = deque()
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._totalEmitted = 0  # 全局单调递增序列号
        self._done = False       # agent 是否已结束
        self._finalStatus: str | None = None  # 结束时的状态

    async def push(self, event: dict[str, Any]) -> int:
        """推入一条事件，同时写入 queue（实时）和 deque（重放）。

        Returns:
            该事件的序列号
        """
        async with self._lock:
            seq = self._totalEmitted
            event["_seq"] = seq
            event["_ts"] = time.time()
            self._events.append(event)
            self._totalEmitted += 1

            # 超出上限 → 丢弃最旧的
            while len(self._events) > self._maxSize:
                self._events.popleft()

            # 写入实时队列（非阻塞 — 如果 queue 满了说明消费者太慢，
            # 此时积压事件仍可从 deque 通过 readSince 读取）
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

            return seq

    async def readSince(self, lastSeq: int = -1) -> list[dict[str, Any]]:
        """读取 lastSeq 之后的所有事件（用于重连时追进度）。

        Args:
            lastSeq: 客户端上报的最后收到的序列号（-1 表示从头开始）

        Returns:
            _seq > lastSeq 的事件列表
        """
        async with self._lock:
            return [e for e in self._events if e["_seq"] > lastSeq]

    async def getQueue(self) -> asyncio.Queue[dict[str, Any]]:
        """获取实时事件队列（供 _streamEvents 消费）。"""
        return self._queue

    async def markDone(self, finalStatus: str = "idle") -> None:
        """标记 agent 执行完成。"""
        async with self._lock:
            self._done = True
            self._finalStatus = finalStatus

    async def resetForNewRound(self) -> None:
        """重置 buffer 为新一轮运行状态。"""
        async with self._lock:
            self._done = False
            self._finalStatus = None

    async def getState(self) -> dict[str, Any]:
        """获取当前缓冲区状态（供前端轮询 / 重连时使用）。"""
        async with self._lock:
            return {
                "totalEmitted": self._totalEmitted,
                "bufferedCount": len(self._events),
                "done": self._done,
                "finalStatus": self._finalStatus,
            }
