#!/usr/bin/env python3
"""Interactive smoke runner for the merged NDLMPanel Agent.

Examples:
  python scripts/agent_chat.py --list-tools
  python scripts/agent_chat.py --mock-demo
  NDLM_LLM_API_KEY=... python scripts/agent_chat.py --provider deepseek
  NDLM_LLM_API_KEY=... python scripts/agent_chat.py --include-core-tools
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.agent_mcp.server.tool_adapter import buildAgentTools  # noqa: E402
from agent.agent_router.router import AgentMode  # noqa: E402
from agent.config_envs.dotenv import loadDotenv  # noqa: E402
from agent.integration.session import AgentSession  # noqa: E402
from agent.llm_providers.mock import MockProvider  # noqa: E402
from ndlmpanel_agent.mcp.server.registry import ToolRegistry  # noqa: E402
from agent.shared.types import AgentConfig, EventType  # noqa: E402


PROVIDER_ENDPOINT_DEFAULTS = {
    "deepseek": "https://api.deepseek.com/anthropic",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai_compat": "https://api.test.com",
    "mock": "https://api.test.com",
}

PROVIDER_MODEL_DEFAULTS = {
    "deepseek": "deepseek-v4-pro",
    "qwen": "qwen-plus",
    "openai_compat": "deepseek-chat",
    "mock": "mock",
}


def build_config(args: argparse.Namespace) -> AgentConfig:
    provider = args.provider
    endpoint = (
        args.endpoint
        or os.environ.get("NDLM_LLM_ENDPOINT")
        or PROVIDER_ENDPOINT_DEFAULTS[provider]
    )
    model = (
        args.model
        or os.environ.get("NDLM_LLM_MODEL")
        or PROVIDER_MODEL_DEFAULTS[provider]
    )
    config = AgentConfig(
        llm_provider=provider,
        llm_endpoint=endpoint,
        llm_model=model,
        llm_max_tokens=args.max_tokens,
        llm_temperature=args.temperature,
        max_tool_rounds=args.max_rounds,
        trace_db_path=args.trace_db,
    )
    config.llm_api_key = args.api_key or os.environ.get("NDLM_LLM_API_KEY", "")
    return config


def list_tools() -> None:
    current = ToolRegistry.withDefaultTools()
    current_names = [tool["function"]["name"] for tool in current.listTools()]
    core_tools = buildAgentTools()
    core_names = [tool.name for tool in core_tools]
    collisions = sorted(set(current_names) & set(core_names))

    print(f"current MCP tools: {len(current_names)}")
    for name in current_names:
        print(f"  mcp.{name}")

    print(f"\nagent core MCP tools: {len(core_names)}")
    for name in core_names:
        marker = " (name collision)" if name in collisions else ""
        print(f"  core.{name}{marker}")

    print(f"\nname collisions: {len(collisions)}")
    for name in collisions:
        print(f"  {name}")


async def run_turn(session: AgentSession, message: str) -> None:
    async for event in session.submit(message):
        etype = event.type
        data = event.data
        if etype == EventType.THINKING_START:
            print(f"[thinking] round={data.get('round')}")
        elif etype == EventType.SAFETY_CHECKED:
            print(
                "[safety] "
                f"tool={data.get('tool')} risk={data.get('risk')} "
                f"verdict={data.get('verdict')} reason={data.get('reason')}"
            )
        elif etype == EventType.APPROVAL_REQUIRED:
            print(
                "[approval required] "
                f"tool={data.get('tool_name')} reason={data.get('reason')}"
            )
            decision = input("approve? [y/N] ").strip().lower()
            if decision in {"y", "yes"}:
                session.approve(data["action_id"])
            else:
                reason = input("reject reason: ").strip() or "rejected in CLI"
                session.reject(data["action_id"], reason)
        elif etype == EventType.APPROVAL_RESOLVED:
            print(
                "[approval resolved] "
                f"approved={data.get('approved')} reason={data.get('reason', '')}"
            )
        elif etype == EventType.TOOL_RESULT:
            output = str(data.get("output", ""))
            print(f"[tool result] {data.get('tool_name')}: {output[:800]}")
        elif etype == EventType.TEXT_DELTA:
            print(data.get("content", ""), end="", flush=True)
        elif etype == EventType.TEXT_DONE:
            print()
        elif etype == EventType.ERROR:
            print(f"[error] {data.get('message')}")
        elif etype == EventType.DONE:
            print("[done]")


async def main_async(args: argparse.Namespace) -> int:
    loadDotenv(".env", override=False)

    if args.list_tools:
        list_tools()
        return 0

    config = build_config(args)
    if args.mcp_command:
        mcpServers = [
            {
                "name": "default",
                "command": shlex.split(args.mcp_command),
                "cwd": args.mcp_cwd,
            }
        ]
    else:
        mcpServers = None
    session = AgentSession(
        config,
        mode=AgentMode(args.mode),
        toolSource=args.tool_source,
        includeCoreTools=args.include_core_tools,
        mcpServers=mcpServers,
    )

    if args.mock_demo:
        session._core._llm = MockProvider(
            [
                {
                    "tool_calls": [
                        {"id": "tc1", "name": "getCpuInfo", "arguments": {}}
                    ]
                },
                {"content": "Mock demo complete. CPU data was read successfully."},
            ]
        )

    print("NDLMPanel Agent chat")
    print(
        f"mode={args.mode} provider={config.llm_provider} model={config.llm_model} "
        f"tool_source={args.tool_source} include_core_tools={args.include_core_tools}"
    )
    print("Commands: /quit, /trace, /tools")
    if not config.llm_api_key and not args.mock_demo:
        print("No NDLM_LLM_API_KEY found. Provider will fall back to MockProvider.")

    try:
        while True:
            message = input("\nyou> ").strip()
            if not message:
                continue
            if message in {"/quit", "/exit"}:
                break
            if message == "/trace":
                traces = session.getTrace()
                print(f"trace entries: {len(traces)}")
                for item in traces[-10:]:
                    print(f"  {item.get('event_type')} {item.get('entry_hash', '')[:12]}")
                continue
            if message == "/tools":
                tools = session._core._registry.listTools()
                print(f"tools: {len(tools)}")
                for tool in tools:
                    print(f"  {tool['function']['name']}")
                continue
            await run_turn(session, message)
            if args.mock_demo:
                print("Mock demo responses are exhausted; use /quit or restart.")
    finally:
        session.close()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-tools", action="store_true")
    parser.add_argument("--mock-demo", action="store_true")
    parser.add_argument("--include-core-tools", action="store_true")
    parser.add_argument(
        "--tool-source",
        choices=["current_mcp", "mcp", "stdio", "mcp_stdio"],
        default="current_mcp",
    )
    parser.add_argument(
        "--mcp-command",
        help="Command string for --tool-source stdio, for example: python -m ndlmpanel_agent.mcp",
    )
    parser.add_argument(
        "--mcp-cwd",
        help="Working directory for --tool-source stdio.",
    )
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in AgentMode],
        default=AgentMode.AGENT.value,
    )
    parser.add_argument(
        "--provider",
        choices=["deepseek", "qwen", "openai_compat", "mock"],
        default=os.environ.get("NDLM_LLM_PROVIDER", "deepseek"),
    )
    parser.add_argument("--endpoint")
    parser.add_argument("--model")
    parser.add_argument("--api-key")
    parser.add_argument("--max-rounds", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--trace-db", default="/tmp/ndlm_agent_chat_traces.db")
    return parser.parse_args()


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
