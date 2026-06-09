"""
OpenAI-compatible Provider。

使用 stdlib urllib.request 发送请求，零外部依赖。
支持流式(stream=True，逐行读取)和非流式调用，含指数退避重试与结构化错误。
"""
from __future__ import annotations
import asyncio
import json
import urllib.error
import urllib.request
from collections.abc import AsyncIterator

from agent.llm_providers.base import LLMProvider
from agent.shared.errors import AgentError, ErrorCode
from agent.shared.types import LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI Compatible API Provider — urllib 实现。"""

    def __init__(self, endpoint: str, apiKey: str = "",
                 model: str = "deepseek-chat", maxTokens: int = 4096,
                 temperature: float = 0.7, retryCount: int = 2,
                 retryDelay: float = 1.0, timeout: float = 120.0):
        self._endpoint = endpoint.rstrip("/")
        self._apiKey = apiKey
        self._model = model
        self._maxTokens = maxTokens
        self._temperature = temperature
        self._retryCount = retryCount
        self._retryDelay = retryDelay
        self._timeout = timeout
        self._tools: list[dict] | None = None

    def setTools(self, tools: list[dict]) -> None:
        """Set OpenAI-compatible function tools for subsequent chat requests."""
        self._tools = tools

    # ── 非流式 ──

    async def chat(self, messages: list[dict]) -> LLMResponse:
        body = self._buildBody(messages, stream=False)
        raw = await self._postWithRetry(body)
        return self._parseResponse(raw)

    # ── 流式（逐行读取）──

    async def chatStream(
        self, messages: list[dict]
    ) -> AsyncIterator[LLMResponse]:
        """流式对话 — 逐行读取 SSE，边到边 yield。

        支持流式 tool_calls：增量 arguments 会在内部累积，当收到
        finish_reason="tool_calls" 时一次性发出完整的 tool_calls。
        """
        body = self._buildBody(messages, stream=True)
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        _SENTINEL = object()
        # 流式 tool_calls 累积器：{index: {"id":..., "name":..., "arguments": "..."}}
        tcBuffer: dict[int, dict] = {}

        def _runner():
            try:
                req = self._buildRequest(body)
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    for rawLine in resp:
                        line = rawLine.decode("utf-8", errors="replace").strip()
                        if not line or not line.startswith("data:"):
                            continue
                        payload = line[len("data:"):].strip()
                        if payload == "[DONE]":
                            break
                        loop.call_soon_threadsafe(queue.put_nowait, payload)
            except Exception as exc:  # noqa: BLE001 — 转交主协程统一抛出
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _SENTINEL)

        loop.run_in_executor(None, _runner)

        while True:
            item = await queue.get()
            if item is _SENTINEL:
                break
            if isinstance(item, Exception):
                raise self._wrapHttpError(item)

            parsed, tcPartial = self._parseStreamChunk(item, tcBuffer)
            if tcPartial is not None:
                tcBuffer = tcPartial
                continue  # 仍在累积 tool_calls，不 yield
            if parsed is not None:
                # 如果是 tool_calls 结束块，把累积的 tool_calls 注入
                if parsed.finish_reason == "tool_calls" and tcBuffer:
                    calls = []
                    for idx in sorted(tcBuffer.keys()):
                        t = tcBuffer[idx]
                        try:
                            args = json.loads(t.get("arguments", "{}"))
                        except json.JSONDecodeError:
                            args = {}
                        calls.append({
                            "id": t.get("id", ""),
                            "name": t.get("name", ""),
                            "arguments": args,
                        })
                    parsed.tool_calls = calls
                    tcBuffer = {}
                yield parsed

        # 结束标记（无更多 tool_calls）
        yield LLMResponse(content=None, finish_reason="stop")

    # ── 内部：请求构造 ──

    def _buildBody(self, messages: list[dict], stream: bool) -> bytes:
        body: dict = {
            "model": self._model,
            "messages": messages,
            "max_tokens": self._maxTokens,
            "temperature": self._temperature,
            "stream": stream,
        }
        if self._tools:
            body["tools"] = self._tools
            body["tool_choice"] = "auto"
        return json.dumps(body).encode("utf-8")

    def _buildRequest(self, body: bytes) -> urllib.request.Request:
        return urllib.request.Request(
            f"{self._endpoint}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._apiKey}",
            },
            method="POST",
        )

    # ── 内部：带重试的同步 POST ──

    async def _postWithRetry(self, body: bytes) -> str:
        loop = asyncio.get_running_loop()
        lastError: AgentError | None = None

        for attempt in range(self._retryCount + 1):
            try:
                return await loop.run_in_executor(None, self._httpPost, body)
            except urllib.error.HTTPError as exc:
                wrapped = self._wrapHttpError(exc)
                # 401/4xx（除 429）不可恢复，立即抛出
                if exc.code != 429 and 400 <= exc.code < 500:
                    raise wrapped
                lastError = wrapped
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                lastError = self._wrapHttpError(exc)

            if attempt < self._retryCount:
                delay = self._retryDelay * (2 ** attempt)  # 指数退避
                await asyncio.sleep(delay)

        assert lastError is not None
        raise lastError

    def _httpPost(self, body: bytes) -> str:
        """同步 HTTP POST。在 run_in_executor 中执行。"""
        req = self._buildRequest(body)
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return resp.read().decode("utf-8")

    def _wrapHttpError(self, exc: Exception) -> AgentError:
        """把底层异常映射为带错误码的 AgentError。"""
        if isinstance(exc, AgentError):
            return exc
        if isinstance(exc, urllib.error.HTTPError):
            status = exc.code
            try:
                detailBody = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001
                detailBody = ""
            finally:
                try:
                    exc.close()
                except Exception:  # noqa: BLE001
                    pass
            if status == 429:
                return AgentError(ErrorCode.LLM_RATE_LIMITED,
                                  "LLM API 限流 (429)",
                                  {"status": status, "body": detailBody})
            if status == 401:
                return AgentError(ErrorCode.LLM_CONNECTION_FAILED,
                                  "LLM API Key 无效或未授权 (401)",
                                  {"status": status})
            detail = f": {detailBody}" if detailBody else ""
            return AgentError(ErrorCode.LLM_CONNECTION_FAILED,
                              f"LLM API HTTP 错误 ({status}){detail}",
                              {"status": status, "body": detailBody})
        if isinstance(exc, (TimeoutError,)):
            return AgentError(ErrorCode.TIMEOUT, "LLM API 请求超时")
        # URLError / OSError
        return AgentError(ErrorCode.LLM_CONNECTION_FAILED,
                          f"LLM API 连接失败: {exc}")

    # ── 内部：响应解析 ──

    def _parseResponse(self, raw: str) -> LLMResponse:
        """解析非流式 JSON 响应为 LLMResponse。"""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AgentError(ErrorCode.LLM_RESPONSE_MALFORMED,
                             f"LLM 响应非合法 JSON: {exc}") from exc

        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})

        content = msg.get("content")
        toolCalls = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            toolCalls.append({
                "id": tc.get("id", ""),
                "name": fn.get("name", ""),
                "arguments": args,
            })

        return LLMResponse(content=content, tool_calls=toolCalls,
                           finish_reason=choice.get("finish_reason", "stop"),
                           usage=data.get("usage", {}))

    def _parseStreamChunk(
        self, payload: str,
        tcBuffer: dict[int, dict] | None = None,
    ) -> tuple[LLMResponse | None, dict[int, dict] | None]:
        """解析单个 SSE data chunk。

        Args:
            payload: SSE data 行内容
            tcBuffer: 当前 tool_calls 累积器

        Returns:
            (parsed_response, updated_tcBuffer)
            - parsed_response: 可 yield 的 LLMResponse（文本 delta / 结束标记）
            - updated_tcBuffer: 更新后的累积器（仍在收集 tool_calls 时）
        """
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            return None, tcBuffer
        choices = obj.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            return None, tcBuffer
        choice = choices[0]
        delta = choice.get("delta", {})
        finish = choice.get("finish_reason") or ""

        # 流式 tool_calls：累积增量片段
        rawTcList = delta.get("tool_calls")
        if rawTcList and isinstance(rawTcList, list):
            if tcBuffer is None:
                tcBuffer = {}
            for rawTc in rawTcList:
                idx = rawTc.get("index", len(tcBuffer))
                if idx not in tcBuffer:
                    tcBuffer[idx] = {"id": "", "name": "", "arguments": ""}
                entry = tcBuffer[idx]
                if rawTc.get("id"):
                    entry["id"] = rawTc["id"]
                fn = rawTc.get("function", {}) or {}
                if fn.get("name"):
                    entry["name"] = fn["name"]
                if fn.get("arguments"):
                    entry["arguments"] += fn["arguments"]
            return None, tcBuffer  # 仍在累积，不 yield

        # 文本增量
        content = delta.get("content")
        if content:
            return LLMResponse(content=content, finish_reason=finish,
                               usage=obj.get("usage", {})), None

        # 结束标记（含 tool_calls 的 finish）
        if finish:
            return LLMResponse(content=None, finish_reason=finish,
                               usage=obj.get("usage", {})), None

        return None, tcBuffer
