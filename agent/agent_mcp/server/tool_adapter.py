"""Adapters for Agent Core MCP tools."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from internal_rpc import BackendRpcClient, BackendRpcError

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


# ── 特殊工具：submitPlan（不是真正的 MCP 工具，由 AgentCore 拦截）──

def submitPlan(
    summary: str = "",
    steps: list[dict] | None = None,
    risks: list[str] | None = None,
    files: list[str] | None = None,
) -> str:
    """提交你的执行计划等待审批。调用此工具即表示你已经完成了分析和规划。

    请在所有分析工作完成后，调用此工具提交完整的执行计划。
    不要在计划中包含未经过读操作确认的假设。

    Args:
        summary: 计划概述，一句话说明要做什么
        steps: 执行步骤列表。每步包含 step_id(唯一标识), title(标题), action(操作描述),
               tool(可选预期工具), target(可选目标文件), risk("low"/"medium"/"high")
        risks: 整体风险说明列表
        files: 涉及的所有文件路径列表
    """
    # 实际逻辑由 AgentCore 拦截处理，此处仅作为 schema 定义
    return "[计划已提交，等待审批]"


# ── 特殊工具：ask_choice（选择题交互，由 AgentCore 拦截）──

def ask_choice(
    question: str = "",
    options: list[dict] | None = None,
) -> str:
    """向用户提出一个选择题，等待用户选择后继续。

    ⚠ 这是 PLAN 模式下向用户提问的唯一合法方式。严禁在文本回复中直接提问。

    在 PLAN 模式下，提交计划前必须使用此工具向用户澄清需求细节。
    你可以多次调用此工具进行多轮询问，直到你确信已经完全理解用户意图。
    当发现用户前后回答矛盾时，追问澄清。

    Args:
        question: 向用户展示的问题描述
        options: 选项列表，每项必须包含以下字段：
            - id (str): 稳定标识，使用大写字母 "A", "B", "C"...
            - title (str): 选项展示文本，简洁明了
            - summary (str, 可选): 副文本说明
            示例: [{"id": "A", "title": "磁盘空间清理", "summary": "分析大文件并清理"}]
    """
    # 实际逻辑由 AgentCore 拦截处理，此处仅作为 schema 定义
    return "[等待用户选择...]"


def createScheduledTask(
    name: str,
    cronExpression: str,
    taskDescription: str,
    approvalPolicy: dict[str, Any] | None = None,
) -> dict:
    """创建定时任务，到指定 cron 时间自动执行 taskDescription 描述的任务。

    Args:
        name: 任务名称
        cronExpression: 5 段 crontab 表达式，例如 "0 8 * * *"
        taskDescription: 到时间后交给后台 Agent 执行的任务描述
        approvalPolicy: 可选预授权策略，包含 allowedTools / allowedPaths 等字段
    """
    params = {
        "name": name,
        "cronExpression": cronExpression,
        "taskDescription": taskDescription,
    }
    if approvalPolicy is not None:
        params["approvalPolicy"] = approvalPolicy
    return _callBackendRpc(
        "scheduledTasks.create",
        params,
    )


def listScheduledTasks(status: str = "") -> dict:
    """列出定时任务，可用 status 筛选 active / paused。"""
    return _callBackendRpc("scheduledTasks.list", {"status": status or ""})


def deleteScheduledTask(taskId: int) -> dict:
    """删除指定定时任务。"""
    return _callBackendRpc("scheduledTasks.delete", {"taskId": taskId})


def pauseScheduledTask(taskId: int) -> dict:
    """暂停指定定时任务。"""
    return _callBackendRpc("scheduledTasks.pause", {"taskId": taskId})


def resumeScheduledTask(taskId: int) -> dict:
    """恢复指定定时任务。"""
    return _callBackendRpc("scheduledTasks.resume", {"taskId": taskId})


def _callBackendRpc(method: str, params: dict[str, Any]) -> dict:
    try:
        data = BackendRpcClient().call(method, params)
        return data if isinstance(data, dict) else {"success": True, "data": data}
    except BackendRpcError as exc:
        return {
            "success": False,
            "errorCode": exc.errorCode,
            "errorMessage": exc.errorMessage,
            "errorDetails": exc.errorDetails,
        }


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
    "submitPlan": "read_only",
    "ask_choice": "read_only",
    "createScheduledTask": "write",
    "listScheduledTasks": "read_only",
    "deleteScheduledTask": "write",
    "pauseScheduledTask": "write",
    "resumeScheduledTask": "write",
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
    "submitPlan": {"agentCore": True, "planSubmission": True},
    "ask_choice": {"agentCore": True, "elicitation": True},
    "createScheduledTask": {"agentCore": True},
    "listScheduledTasks": {"agentCore": True},
    "deleteScheduledTask": {"agentCore": True},
    "pauseScheduledTask": {"agentCore": True},
    "resumeScheduledTask": {"agentCore": True},
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
    submitPlan,
    ask_choice,
    createScheduledTask,
    listScheduledTasks,
    deleteScheduledTask,
    pauseScheduledTask,
    resumeScheduledTask,
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
