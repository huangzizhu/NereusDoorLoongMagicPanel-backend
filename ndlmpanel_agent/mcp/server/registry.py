"""Tool registry shared by the MCP server and the agent core."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable
from typing import Any

try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - pydantic is a project dependency.
    BaseModel = None  # type: ignore

from ndlmpanel_agent.mcp.protocol.schemas import (
    functionToMcpToolSchema,
    functionToToolSchema,
)

from .tool_adapter import AdaptedTool, ToolCallResult, ToolRiskLevel, buildDefaultTools


class ToolRegistry:
    def __init__(
        self,
        tools: list[AdaptedTool | Callable[..., Any]] | None = None,
        loadDefaults: bool = False,
    ):
        self._tools: dict[str, AdaptedTool | Callable[..., Any]] = {}
        self._riskLevels: dict[str, ToolRiskLevel] = {}
        initialTools = tools if tools is not None else (buildDefaultTools() if loadDefaults else [])
        for tool in initialTools:
            self.register(tool)

    @classmethod
    def withDefaultTools(cls) -> "ToolRegistry":
        return cls(loadDefaults=True)

    def register(
        self,
        tool: AdaptedTool | Callable[..., Any],
        riskLevel: ToolRiskLevel = ToolRiskLevel.WRITE,
    ) -> None:
        if isinstance(tool, AdaptedTool):
            self._tools[tool.name] = tool
            self._riskLevels[tool.name] = _coerceRiskLevel(tool.riskLevel)
            return

        if not callable(tool):
            raise TypeError("tool must be an AdaptedTool or callable")

        self._tools[tool.__name__] = tool
        self._riskLevels[tool.__name__] = _coerceRiskLevel(riskLevel)

    def unregister(self, name: str) -> bool:
        """按名称移除已注册工具（无人值守模式剔除交互类工具）。"""
        self._tools.pop(name, None)
        return self._riskLevels.pop(name, None) is not None

    def registerMany(
        self,
        funcs: list[Callable[..., Any]],
        riskLevel: ToolRiskLevel = ToolRiskLevel.WRITE,
    ) -> None:
        for func in funcs:
            self.register(func, riskLevel)

    def registerModule(self, module) -> int:
        toolMap: dict[str, ToolRiskLevel] = getattr(module, "TOOLS", {})
        count = 0
        for name, riskLevel in toolMap.items():
            func = getattr(module, name, None)
            if callable(func):
                self.register(func, riskLevel)
                count += 1
        return count

    def listTools(self) -> list[dict]:
        """Return OpenAI-style tool schemas used by the agent prompt/LLM layer."""
        schemas = []
        for name, tool in self._tools.items():
            schema = functionToToolSchema(_toolFunc(tool))
            risk = self._riskLevels.get(name, ToolRiskLevel.WRITE)
            # 给需要审批的工具（write/dangerous）注入 reason 参数
            # LLM 必须说明调用目的，用于审批弹窗展示
            if risk != ToolRiskLevel.READ_ONLY:
                params = schema.setdefault("function", {}).setdefault("parameters", {})
                props = params.setdefault("properties", {})
                props["reason"] = {
                    "type": "string",
                    "description": "调用此工具的原因和目的，向用户解释你的意图。必须说明你要做什么、为什么这样做。",
                }
                required = params.setdefault("required", [])
                if "reason" not in required:
                    required.append("reason")
            schemas.append(schema)
        schemas.sort(key=lambda item: item["function"]["name"])
        return schemas

    def listMcpTools(self) -> list[dict]:
        """Return MCP-style tool schemas used by tools/list."""
        schemas = []
        for name, tool in self._tools.items():
            if isinstance(tool, AdaptedTool):
                schema = tool.toMcpSchema()
            else:
                schema = functionToMcpToolSchema(tool, self.getRiskLevel(name).value)
            schemas.append(schema)
        schemas.sort(key=lambda item: item["name"])
        return schemas

    def getTool(self, name: str) -> AdaptedTool | Callable[..., Any] | None:
        return self._tools.get(name)

    def getRiskLevel(self, name: str) -> ToolRiskLevel:
        return self._riskLevels.get(name, ToolRiskLevel.WRITE)

    def callTool(self, name: str, arguments: dict) -> ToolCallResult:
        tool = self.getTool(name)
        if tool is None:
            raise KeyError(name)
        if isinstance(tool, AdaptedTool):
            return tool.call(arguments)
        try:
            return ToolCallResult.text(_serializeResult(tool(**arguments)))
        except TypeError as exc:
            return ToolCallResult.json(
                {
                    "success": False,
                    "errorCode": "INVALID_ARGUMENTS",
                    "errorMessage": f"Invalid tool arguments: {exc}",
                },
                isError=True,
            )
        except Exception as exc:
            return ToolCallResult.json(
                {
                    "success": False,
                    "errorCode": exc.__class__.__name__,
                    "errorMessage": str(exc),
                },
                isError=True,
            )


def _toolFunc(tool: AdaptedTool | Callable[..., Any]) -> Callable[..., Any]:
    return tool.func if isinstance(tool, AdaptedTool) else tool


def _coerceRiskLevel(value: Any) -> ToolRiskLevel:
    if isinstance(value, ToolRiskLevel):
        return value
    raw = getattr(value, "value", value)
    try:
        return ToolRiskLevel(raw)
    except ValueError:
        return ToolRiskLevel.WRITE


def _toJsonable(value: Any) -> Any:
    if BaseModel is not None and isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, list):
        return [_toJsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_toJsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _toJsonable(item) for key, item in value.items()}
    return value


def _serializeResult(result: Any) -> str:
    if result is None:
        return "(no result)"
    if isinstance(result, str):
        return result
    return json.dumps(_toJsonable(result), ensure_ascii=False, indent=2, default=str)
