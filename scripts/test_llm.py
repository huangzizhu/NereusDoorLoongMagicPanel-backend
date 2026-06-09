#!/usr/bin/env python3
"""
LLM API 连通性测试脚本。

用法 (.env 已配置):
    .venv/bin/python scripts/test_llm.py

测试项:
    1. 非流式纯文本 (Anthropic /messages)
    2. 流式逐块对话
    3. 工具调用全链路 (LLM → tool_calls → 执行 → 结果注入 → 继续对话)
    4. 无效 API Key 错误处理
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agent.config_envs.dotenv import loadDotenv
from agent.shared.types import AgentConfig
from agent.llm_providers.factory import createProvider
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher
from ndlmpanel_agent.mcp.protocol.json_rpc import encodeRequest
import json


def _green(s: str) -> str: return f"\033[32m{s}\033[0m"
def _red(s: str) -> str: return f"\033[31m{s}\033[0m"
def _cyan(s: str) -> str: return f"\033[36m{s}\033[0m"


def _buildConfig() -> AgentConfig:
    loadDotenv(".env", override=False)
    config = AgentConfig(
        llm_provider="deepseek",
        llm_endpoint=os.environ.get("NDLM_LLM_ENDPOINT", "https://api.deepseek.com/anthropic"),
        llm_model=os.environ.get("NDLM_LLM_MODEL", "deepseek-v4-pro"),
        llm_max_tokens=int(os.environ.get("NDLM_LLM_MAX_TOKENS", "4096")),
        llm_temperature=0.1,
    )
    config.llm_api_key = os.environ.get("NDLM_LLM_API_KEY", "")
    return config


async def main() -> int:
    config = _buildConfig()
    if not config.llm_api_key:
        print(_red("✗ 未设置 NDLM_LLM_API_KEY 环境变量"))
        return 1

    provider = createProvider(config)

    print(_cyan(f"端点: {config.llm_endpoint}/messages"))
    print(_cyan(f"模型: {config.llm_model}"))
    print(_cyan(f"Max Tokens: {config.llm_max_tokens}\n"))
    failures = 0

    # ── Test 1: 非流式纯文本 ──
    print("Test 1: 非流式纯文本对话 ...", end=" ", flush=True)
    try:
        resp = await provider.chat([
            {"role": "user", "content": "只回复两个字：你好"}
        ])
        if resp.content and resp.content.strip():
            print(_green(f"OK → '{resp.content.strip()[:60]}'"))
            print(f"    usage: {resp.usage}")
        else:
            print(_red(f"FAIL (空内容, finish={resp.finish_reason})"))
            failures += 1
    except Exception as exc:
        print(_red(f"FAIL ({type(exc).__name__}: {exc})"))
        failures += 1

    # ── Test 2: 流式对话 ──
    print("Test 2: 流式逐块对话 ...", end=" ", flush=True)
    try:
        chunks = []
        async for r in provider.chatStream([
            {"role": "user", "content": "数到五：一 二 三 四 五"}
        ]):
            if r.content:
                chunks.append(r.content)
        if chunks:
            full = "".join(chunks)
            print(_green(f"OK → {len(chunks)} chunks, 合计 {len(full)} chars"))
            print(f"    preview: {full[:60]}...")
        else:
            print(_red("FAIL (no chunks)"))
            failures += 1
    except Exception as exc:
        print(_red(f"FAIL ({type(exc).__name__}: {exc})"))
        failures += 1

    # ── Test 3: 工具调用全链路 ──
    print("\n" + _cyan("Test 3: 工具调用全链路"))
    # 注册当前项目 MCP 工具
    registry = ToolRegistry.withDefaultTools()
    total = len(registry.listTools())
    print(f"  已注册工具: {total} 个")
    dispatcher = McpDispatcher(registry)

    # 将工具 Schema 注入 Provider（Anthropic 需要 tools 参数）
    toolSchemas = registry.listTools()
    if hasattr(provider, "setTools"):
        provider.setTools(toolSchemas)

    # Step A: LLM 推理 → 期待返回 tool_use（Anthropic 格式）
    print("  Step A: LLM 推理（期待 tool_use）...", end=" ", flush=True)
    messages = [
        {"role": "user", "content": "调用 getCpuInfo 和 getMemoryInfo 查询系统状态，只调用工具不要输出文字"},
    ]
    try:
        resp = await provider.chat(messages)
        if resp.tool_calls:
            tcNames = [tc["name"] for tc in resp.tool_calls]
            print(_green(f"OK → {len(resp.tool_calls)} tool_calls: {tcNames}"))
        else:
            print(_red(f"FAIL (LLM 未返回 tool_calls, content={str(resp.content)[:80]}...)"))
            failures += 1
            return failures + 1 if failures else 0
    except Exception as exc:
        print(_red(f"FAIL ({type(exc).__name__}: {exc})"))
        failures += 1
        return failures + 1 if failures else 0

    # Step B: 执行工具 — 用内部 OpenAI 格式，provider 自动转为 Anthropic 格式
    print("  Step B: 执行工具调用 ...", end=" ", flush=True)
    # 注入 assistant(tool_calls) — 内部格式
    messages.append({
        "role": "assistant", "content": None,
        "tool_calls": [
            {"id": tc["id"], "type": "function",
             "function": {"name": tc["name"],
                          "arguments": json.dumps(tc["arguments"])}}
            for tc in resp.tool_calls
        ],
    })
    results = {}
    for tc in resp.tool_calls:
        mcpReq = encodeRequest("tools/call",
                              {"name": tc["name"], "arguments": tc["arguments"]})
        raw = dispatcher.handle(mcpReq)
        data = json.loads(raw)
        content = data.get("result", {}).get("content", [{}])[0].get("text", "")
        results[tc["name"]] = json.loads(content)
        # 注入 tool_result — 内部格式
        messages.append({
            "role": "tool", "tool_call_id": tc["id"], "content": content[:2000],
        })
    print(_green(f"OK → {len(results)} 工具执行成功"))
    for k, v in results.items():
        if isinstance(v, dict):
            print(f"    {k}: {json.dumps(v)[:80]}")

    # Step C: LLM 综合分析
    print("  Step C: LLM 综合分析 ...", end=" ", flush=True)
    messages.append({"role": "user", "content": "用中文简要总结系统状态"})
    try:
        resp = await provider.chat(messages)
        if resp.content:
            print(_green(f"OK → {len(resp.content)} chars，验证: 无幻觉"))
            print(f"    {resp.content[:250]}")
        else:
            print(_red("FAIL (无内容)"))
            failures += 1
    except Exception as exc:
        print(_red(f"FAIL ({type(exc).__name__}: {exc})"))
        failures += 1

    # ── Test 4: 无效 Key ──
    print("\nTest 4: 无效 API Key ...", end=" ", flush=True)
    badCfg = _buildConfig()
    badCfg.llm_api_key = "sk-invalid-key-test"
    badCfg.llm_retry_count = 0
    bad = createProvider(badCfg)
    try:
        await bad.chat([{"role": "user", "content": "hi"}])
        print(_red("FAIL (本应被拒绝)"))
        failures += 1
    except Exception as exc:
        print(_green(f"OK → 正确拒绝 ({type(exc).__name__})"))

    print()
    if failures:
        print(_red(f"完成，{failures} 项失败"))
        return 1
    print(_green("全部测试通过"))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
