"""Tool registry for the Agent Core MCP server."""

from __future__ import annotations

from .tool_adapter import AgentAdaptedTool, AgentToolCallResult, buildAgentTools


class AgentToolRegistry:
    def __init__(self, tools: list[AgentAdaptedTool] | None = None):
        self._tools: dict[str, AgentAdaptedTool] = {}
        for tool in tools if tools is not None else buildAgentTools():
            self.register(tool)

    def register(self, tool: AgentAdaptedTool) -> None:
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """按名称移除已注册工具（无人值守模式剔除交互类工具）。"""
        return self._tools.pop(name, None) is not None

    def listTools(self) -> list[dict]:
        schemas = [tool.toMcpSchema() for tool in self._tools.values()]
        schemas.sort(key=lambda item: item["name"])
        return schemas

    def getTool(self, name: str) -> AgentAdaptedTool | None:
        return self._tools.get(name)

    def callTool(self, name: str, arguments: dict) -> AgentToolCallResult:
        tool = self.getTool(name)
        if tool is None:
            raise KeyError(name)
        return tool.call(arguments)
