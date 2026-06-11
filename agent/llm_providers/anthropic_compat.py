"""
Anthropic Messages API Provider。

DeepSeek 提供 Anthropic 兼容端点 (https://api.deepseek.com/anthropic)，
使用 Anthropic Messages API 格式。本 Provider 将内部 OpenAI 风格 messages
双向转换为 Anthropic 格式，对上层（AgentCore）透明。

关键差异 vs OpenAI：
  - 端点: /messages (非 /chat/completions)
  - Auth: x-api-key (非 Authorization: Bearer)
  - 头部: anthropic-version: 2023-06-01
  - 响应: content 是数组，含 text/tool_use 两种 block
  - 流式: SSE event: 行前缀，delta.type=text_delta
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


class AnthropicProvider(LLMProvider):
    """Anthropic Messages API Provider — urllib 实现。"""

    def __init__(self, endpoint: str, apiKey: str = "",
                 model: str = "deepseek-v4-pro", maxTokens: int = 4096,
                 temperature: float = 0.7, retryCount: int = 2,
                 retryDelay: float = 1.0, timeout: float = 120.0,
                 tools: list[dict] | None = None):
        self._endpoint = endpoint.rstrip("/")
        self._apiKey = apiKey
        self._model = model
        self._maxTokens = maxTokens
        self._temperature = temperature
        self._retryCount = retryCount
        self._retryDelay = retryDelay
        self._timeout = timeout
        self._tools: list[dict] | None = tools

    def setTools(self, tools: list[dict]) -> None:
        """设置可用工具列表（OpenAI function-calling 格式），
        在每次请求时自动转为 Anthropic tools 格式发送。"""
        self._tools = tools

    # ── 非流式 ──

    async def chat(self, messages: list[dict]) -> LLMResponse:
        body = self._buildBody(messages, stream=False)
        raw = await self._postWithRetry(body)
        return self._parseResponse(raw)

    # ── 流式 ──

    async def chatStream(self, messages: list[dict]
                         ) -> AsyncIterator[LLMResponse]:
        body = self._buildBody(messages, stream=True)
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        _SENTINEL = object()

        def _runner():
            try:
                req = self._buildRequest(body)
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    buf = ""
                    for rawLine in resp:
                        line = rawLine.decode("utf-8", errors="replace")
                        if line.startswith("event:") or line.startswith("data:"):
                            buf += line
                        if line.strip() == "" and buf:
                            loop.call_soon_threadsafe(
                                queue.put_nowait, buf.strip())
                            buf = ""
            except Exception as exc:
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
            parsed = self._parseStreamEvent(item)
            if parsed is not None:
                yield parsed
        yield LLMResponse(content=None, finish_reason="stop")

    # ── 消息格式转换 ──

    def _buildBody(self, messages: list[dict], stream: bool) -> bytes:
        body: dict = {
            "model": self._model,
            "max_tokens": self._maxTokens,
            "temperature": self._temperature,
        }
        # tools 放在 messages 之前 → 使 tool schema 进入 KV-cache 前缀
        if self._tools:
            body["tools"] = self._convertTools(self._tools)
        body["messages"] = self._convertMessages(messages)
        body["stream"] = stream
        return json.dumps(body).encode("utf-8")

    @staticmethod
    def _convertTools(tools: list[dict]) -> list[dict]:
        """OpenAI function-calling schema → Anthropic tools schema。
        OpenAI: {"type":"function","function":{"name":"x","description":"...","parameters":{...}}}
        Anthropic: {"name":"x","description":"...","input_schema":{...}}
        """
        result = []
        for t in tools:
            fn = t.get("function", t)
            name = fn.get("name", "")
            input_schema = fn.get("parameters", {"type": "object", "properties": {}, "required": []})
            result.append({
                "name": name,
                "description": fn.get("description", ""),
                "input_schema": input_schema,
            })
        return result

    def _convertMessages(self, messages: list[dict]) -> list[dict]:
        """OpenAI 风格 messages → Anthropic 风格。

        转换规则：
        - system → 保留
        - user/assistant（纯文本）→ 保留，content 为字符串
        - assistant + tool_calls → assistant 含 tool_use blocks
        - tool → user 含 tool_result blocks
          **关键**：连续 N 条 tool 消息合并为一个 user 消息，
          内含 N 个 tool_result block（Anthropic 强制约束：一次
          tool_use 组中的所有结果必须在同一个 user 消息中返回）
        """
        converted: list[dict] = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            role = msg.get("role", "user")
            content = msg.get("content")

            if role == "system":
                converted.append({"role": "system", "content": content or ""})
            elif role == "tool":
                # 收集连续 tool 消息，合并为一个 user 消息
                toolResults: list[dict] = []
                while i < len(messages) and messages[i].get("role") == "tool":
                    tm = messages[i]
                    toolResults.append({
                        "type": "tool_result",
                        "tool_use_id": tm.get("tool_call_id", ""),
                        "content": tm.get("content", ""),
                    })
                    i += 1
                converted.append({"role": "user", "content": toolResults})
                continue  # 跳过 while 末尾的 i += 1
            elif role == "assistant" and msg.get("tool_calls"):
                blocks: list[dict] = []
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    args_str = fn.get("arguments", "{}")
                    try:
                        inp = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        inp = {}
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "input": inp,
                    })
                converted.append({"role": "assistant", "content": blocks})
            else:
                converted.append({"role": role, "content": content or ""})
            i += 1
        return converted

    # ── 响应解析 ──

    def _parseResponse(self, raw: str) -> LLMResponse:
        """解析非流式 Anthropic Messages 响应 → LLMResponse。"""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AgentError(ErrorCode.LLM_RESPONSE_MALFORMED,
                             f"Anthropic 响应非合法 JSON: {exc}") from exc

        contentBlocks = data.get("content", [])
        textParts = []
        toolCalls = []
        for block in contentBlocks:
            if block.get("type") == "text":
                textParts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                toolCalls.append({
                    "id": block.get("id", ""),
                    "name": block.get("name", ""),
                    "arguments": block.get("input", {}),
                })

        usage = {}
        if "usage" in data:
            u = data["usage"]
            usage = {
                "prompt_tokens": u.get("input_tokens", 0),
                "completion_tokens": u.get("output_tokens", 0),
                "total_tokens": (u.get("input_tokens", 0) +
                                 u.get("output_tokens", 0)),
            }

        finish = "tool_calls" if toolCalls else "stop"
        return LLMResponse(
            content="".join(textParts) or None,
            tool_calls=toolCalls,
            finish_reason=finish,
            usage=usage,
        )

    def _parseStreamEvent(self, buf: str) -> LLMResponse | None:
        """解析单个 SSE event block → 增量 LLMResponse。

        buf 包含 "event: ...\ndata: {...}" 两行。
        """
        dataStr = ""
        for line in buf.split("\n"):
            stripped = line.strip()
            if stripped.startswith("data:"):
                dataStr = stripped[len("data:"):].strip()
        if not dataStr:
            return None
        try:
            obj = json.loads(dataStr)
        except json.JSONDecodeError:
            return None

        etype = obj.get("type", "")
        if etype == "content_block_delta":
            delta = obj.get("delta", {})
            if delta.get("type") == "text_delta":
                return LLMResponse(content=delta.get("text", ""), finish_reason="")
        elif etype == "content_block_start":
            cb = obj.get("content_block", {})
            if cb.get("type") == "tool_use":
                return LLMResponse(
                    content=None,
                    tool_calls=[{
                        "id": cb.get("id", ""),
                        "name": cb.get("name", ""),
                        "arguments": cb.get("input", {}),
                    }],
                    finish_reason="",
                )
        elif etype == "message_delta":
            # usage info, stop_reason
            d = obj.get("delta", {})
            u = obj.get("usage", {})
            usage = {"prompt_tokens": u.get("input_tokens", 0),
                     "completion_tokens": u.get("output_tokens", 0),
                     "total_tokens": u.get("input_tokens", 0) + u.get("output_tokens", 0)} if u else {}
            return LLMResponse(content=None, finish_reason=d.get("stop_reason", "stop"),
                               usage=usage)
        return None

    # ── HTTP ──

    def _buildRequest(self, body: bytes) -> urllib.request.Request:
        return urllib.request.Request(
            f"{self._endpoint}/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._apiKey,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

    async def _postWithRetry(self, body: bytes) -> str:
        loop = asyncio.get_running_loop()
        lastError: AgentError | None = None
        for attempt in range(self._retryCount + 1):
            try:
                return await loop.run_in_executor(None, self._httpPost, body)
            except urllib.error.HTTPError as exc:
                wrapped = self._wrapHttpError(exc)
                if exc.code != 429 and 400 <= exc.code < 500:
                    raise wrapped
                lastError = wrapped
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                lastError = self._wrapHttpError(exc)
            if attempt < self._retryCount:
                await asyncio.sleep(self._retryDelay * (2 ** attempt))
        assert lastError is not None
        raise lastError

    def _httpPost(self, body: bytes) -> str:
        import http.client as _hc
        req = self._buildRequest(body)
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            try:
                raw = resp.read()
            except _hc.IncompleteRead as e:
                raw = e.partial  # 使用已读取的部分数据
            return raw.decode("utf-8")

    def _wrapHttpError(self, exc: Exception) -> AgentError:
        if isinstance(exc, AgentError):
            return exc
        if isinstance(exc, urllib.error.HTTPError):
            status = exc.code
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                detail = ""
            finally:
                try: exc.close()
                except Exception: pass
            if status == 429:
                return AgentError(ErrorCode.LLM_RATE_LIMITED,
                                  "API 限流 (429)", {"status": status, "body": detail})
            if status == 401:
                return AgentError(ErrorCode.LLM_CONNECTION_FAILED,
                                  "API Key 无效 (401)", {"status": status})
            return AgentError(ErrorCode.LLM_CONNECTION_FAILED,
                              f"HTTP {status}", {"status": status, "body": detail})
        if isinstance(exc, TimeoutError):
            return AgentError(ErrorCode.TIMEOUT, "API 请求超时")
        return AgentError(ErrorCode.LLM_CONNECTION_FAILED, f"连接失败: {exc}")
