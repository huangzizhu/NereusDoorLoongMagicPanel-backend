"""Adapters for Agent Core MCP tools."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

try:
    from ndlmpanel_agent.mcp.protocol.schemas import functionToMcpToolSchema
except ModuleNotFoundError:  # Allows `python -m agent_mcp` from ndlmpanel_agent/.
    from mcp.protocol.schemas import functionToMcpToolSchema

from ..tools.command import runCommand, runShellCommand
from ..tools.filesystem import (
    applyPatch,
    copyPath,
    createDirectory,
    deletePath,
    editBatch,
    formatPatchDiagnostics,
    insertText,
    listFiles,
    movePath,
    readFile,
    readFiles,
    replaceRange,
    replaceRegex,
    replaceText,
    searchFiles,
    searchText,
    searchTexts,
    statPaths,
    writeFile,
    writeFiles,
)
from ..tools.web import webFetch, webSearch
from ..tools.project import (
    detectProjectCommands,
    explainToolError,
    getGitDiff,
    getGitStatus,
    getRecentCommandResults,
    listGitChangedFiles,
    runProjectCheck,
    summarizeFile,
    summarizeWorkspace,
)
from ..tools.workspace import getWorkspaceContext


TOOL_RISK_LEVELS: dict[str, str] = {
    "getWorkspaceContext": "read_only",
    "listFiles": "read_only",
    "readFile": "read_only",
    "readFiles": "read_only",
    "searchText": "read_only",
    "searchTexts": "read_only",
    "searchFiles": "read_only",
    "statPaths": "read_only",
    "writeFile": "write",
    "writeFiles": "write",
    "replaceText": "write",
    "replaceRange": "write",
    "insertText": "write",
    "replaceRegex": "write",
    "editBatch": "write",
    "applyPatch": "write",
    "formatPatchDiagnostics": "read_only",
    "createDirectory": "write",
    "copyPath": "write",
    "movePath": "write",
    "deletePath": "dangerous",
    "getGitStatus": "read_only",
    "getGitDiff": "read_only",
    "listGitChangedFiles": "read_only",
    "detectProjectCommands": "read_only",
    "runProjectCheck": "dangerous",
    "summarizeFile": "read_only",
    "summarizeWorkspace": "read_only",
    "explainToolError": "read_only",
    "getRecentCommandResults": "read_only",
    "runCommand": "dangerous",
    "webFetch": "read_only",
    "webSearch": "read_only",
    "runShellCommand": "dangerous",
}

TOOL_ANNOTATIONS: dict[str, dict[str, Any]] = {
    "getWorkspaceContext": {"agentCore": True},
    "listFiles": {"agentCore": True},
    "readFile": {"agentCore": True, "mayReturnLargeOutput": True},
    "readFiles": {"agentCore": True, "batchTool": True, "mayReturnLargeOutput": True},
    "searchText": {"agentCore": True, "mayReturnLargeOutput": True},
    "searchTexts": {"agentCore": True, "batchTool": True, "mayReturnLargeOutput": True},
    "searchFiles": {"agentCore": True},
    "statPaths": {"agentCore": True, "batchTool": True},
    "writeFile": {"agentCore": True},
    "writeFiles": {"agentCore": True, "batchTool": True},
    "replaceText": {"agentCore": True},
    "replaceRange": {"agentCore": True, "agentFriendlyEdit": True},
    "insertText": {"agentCore": True, "agentFriendlyEdit": True},
    "replaceRegex": {"agentCore": True, "agentFriendlyEdit": True},
    "editBatch": {"agentCore": True, "agentFriendlyEdit": True, "batchTool": True},
    "applyPatch": {"agentCore": True, "preferredForCodeEdits": True},
    "formatPatchDiagnostics": {"agentCore": True},
    "createDirectory": {"agentCore": True},
    "copyPath": {"agentCore": True},
    "movePath": {"agentCore": True},
    "deletePath": {"agentCore": True, "mayDeleteData": True},
    "getGitStatus": {"agentCore": True},
    "getGitDiff": {"agentCore": True, "mayReturnLargeOutput": True},
    "listGitChangedFiles": {"agentCore": True},
    "detectProjectCommands": {"agentCore": True},
    "runProjectCheck": {"agentCore": True, "usesShell": False},
    "summarizeFile": {"agentCore": True},
    "summarizeWorkspace": {"agentCore": True},
    "explainToolError": {"agentCore": True},
    "getRecentCommandResults": {"agentCore": True},
    "runCommand": {
        "agentCore": True,
        "usesShell": False,
        "mayMutateSystem": True,
        "preferredDefaultCommandTool": True,
        "descriptionHint": "Use this by default for argv-style commands. It does not interpret pipes, redirects, globs, variables, or shell operators.",
    },
    "webFetch": {"agentCore": True},
    "webSearch": {"agentCore": True},
    "runShellCommand": {
        "agentCore": True,
        "usesShell": True,
        "mayMutateSystem": True,
        "advancedTool": True,
        "descriptionHint": "Use only when shell features are required, such as pipes, redirects, globs, variables, command substitution, or &&/|| chains.",
    },
}

AGENT_TOOL_FUNCTIONS: tuple[Callable[..., Any], ...] = (
    getWorkspaceContext,
    listFiles,
    readFile,
    readFiles,
    searchText,
    searchTexts,
    searchFiles,
    statPaths,
    writeFile,
    writeFiles,
    replaceText,
    replaceRange,
    insertText,
    replaceRegex,
    editBatch,
    applyPatch,
    formatPatchDiagnostics,
    createDirectory,
    copyPath,
    movePath,
    deletePath,
    getGitStatus,
    getGitDiff,
    listGitChangedFiles,
    detectProjectCommands,
    runProjectCheck,
    summarizeFile,
    summarizeWorkspace,
    explainToolError,
    getRecentCommandResults,
    webFetch,
    webSearch,
    runCommand,
    runShellCommand,
)


@dataclass(frozen=True)
class AgentToolCallResult:
    content: list[dict[str, str]]
    isError: bool = False

    @classmethod
    def json(cls, payload: Any, isError: bool = False) -> "AgentToolCallResult":
        return cls(
            content=[{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2, default=str)}],
            isError=isError,
        )


@dataclass(frozen=True)
class AgentAdaptedTool:
    name: str
    func: Callable[..., Any]
    riskLevel: str
    annotations: dict[str, Any] = dataclasses.field(default_factory=dict)

    def toMcpSchema(self) -> dict:
        schema = functionToMcpToolSchema(self.func, self.riskLevel)
        schema.setdefault("annotations", {})
        schema["annotations"].update(TOOL_ANNOTATIONS.get(self.name, {}))
        schema["annotations"].update(self.annotations)
        return schema

    def call(self, arguments: dict[str, Any]) -> AgentToolCallResult:
        try:
            return AgentToolCallResult.json(self.func(**arguments))
        except TypeError as exc:
            return AgentToolCallResult.json(
                {
                    "success": False,
                    "errorCode": "INVALID_ARGUMENTS",
                    "errorMessage": f"Invalid tool arguments: {exc}",
                },
                isError=True,
            )
        except Exception as exc:
            return AgentToolCallResult.json(
                {
                    "success": False,
                    "errorCode": exc.__class__.__name__,
                    "errorMessage": str(exc),
                },
                isError=True,
            )


def buildAgentTools() -> list[AgentAdaptedTool]:
    return [
        AgentAdaptedTool(
            name=fn.__name__,
            func=fn,
            riskLevel=TOOL_RISK_LEVELS.get(fn.__name__, "write"),
        )
        for fn in AGENT_TOOL_FUNCTIONS
    ]
