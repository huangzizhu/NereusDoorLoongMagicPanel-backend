"""Command line entrypoint for the NDLM Panel MCP server."""

from __future__ import annotations

import argparse

from .server.dispatcher import McpDispatcher
from .server.registry import ToolRegistry
from .transports.stdio import stdioServe


def buildDispatcher() -> McpDispatcher:
    return McpDispatcher(ToolRegistry())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ndlmpanel-agent-mcp")
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="MCP transport to run. HTTP is reserved for the next phase.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host for future use.")
    parser.add_argument("--port", type=int, default=8765, help="HTTP port for future use.")
    args = parser.parse_args(argv)

    if args.transport == "http":
        parser.error("HTTP transport is planned but not implemented in this phase")

    dispatcher = buildDispatcher()
    stdioServe(dispatcher.handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
