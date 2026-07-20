"""Command line entrypoint for the Agent Core MCP server."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

# Load .env so TAVILY_API_KEY is available in the environment
_env = Path(__file__).resolve().parents[2] / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("\"'")
            if key and not os.environ.get(key):
                os.environ[key] = val

try:
    from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher
    from ndlmpanel_agent.mcp.transports.stdio import stdioServe
except ModuleNotFoundError:  # Allows `python -m agent_mcp` from ndlmpanel_agent/.
    from mcp.server.dispatcher import McpDispatcher
    from mcp.transports.stdio import stdioServe

from .server.registry import AgentToolRegistry


def buildDispatcher() -> McpDispatcher:
    return McpDispatcher(
        AgentToolRegistry(),
        serverName="ndlmpanel-agent-core",
        serverVersion="0.1.0",
    )


def main(argv: list[str] | None = None) -> int:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(prog="ndlmpanel-agent-core-mcp")
    parser.add_argument(
        "--transport",
        choices=("stdio",),
        default="stdio",
        help="MCP transport to run.",
    )
    parser.parse_args(argv)

    dispatcher = buildDispatcher()
    stdioServe(dispatcher.handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
