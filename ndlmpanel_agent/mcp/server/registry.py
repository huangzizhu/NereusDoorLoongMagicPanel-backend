"""MCP tool registry backed by utils.toolFunction adapters."""

from __future__ import annotations

from .tool_adapter import AdaptedTool, ToolCallResult, buildDefaultTools


class ToolRegistry:
    def __init__(self, tools: list[AdaptedTool] | None = None):
        self._tools: dict[str, AdaptedTool] = {}
        for tool in tools if tools is not None else buildDefaultTools():
            self.register(tool)

    def register(self, tool: AdaptedTool) -> None:
        self._tools[tool.name] = tool

    def listTools(self) -> list[dict]:
        schemas = [tool.toMcpSchema() for tool in self._tools.values()]
        schemas.sort(key=lambda item: item["name"])
        return schemas

    def getTool(self, name: str) -> AdaptedTool | None:
        return self._tools.get(name)

    def callTool(self, name: str, arguments: dict) -> ToolCallResult:
        tool = self.getTool(name)
        if tool is None:
            raise KeyError(name)
        return tool.call(arguments)
