from __future__ import annotations

from agent.integration.session import AgentSession


def test_current_mcp_with_core_tools_contains_ops_and_agent_core_tools():
    registry, _dispatcher, _bridge = AgentSession._buildToolBackend(
        "current_mcp",
        includeCoreTools=True,
        mcpServers=None,
    )
    tool_names = {item["function"]["name"] for item in registry.listTools()}

    assert "getDiskInfo" in tool_names
    assert "querySystemLogs" in tool_names
    assert "runCommand" in tool_names
    assert "runShellCommand" in tool_names
