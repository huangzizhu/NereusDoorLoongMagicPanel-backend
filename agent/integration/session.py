"""AgentSession — 对外唯一入口。

后端（FastAPI）通过 AgentSession 与 Agent 内核交互：
    session = AgentSession(config)
    async for event in session.submit("帮我看看磁盘") :
        yield formatSSE(event)

S6 更新：AgentCore 替换 Worker 模式。
"""
from __future__ import annotations
import asyncio
import logging
from collections.abc import AsyncIterator
from agent.shared.types import AgentConfig, AgentEvent, EventType
from agent.shared.id_gen import gen_session_id, gen_trace_id
from agent.config_envs.loader import loadConfig
from agent.integration.event_stream import EventStream
from agent.prompt_loader import loadPrompt
from agent.safety.rule_engine import RuleEngine
from agent.safety.canary import CanaryManager
from agent.safety.llm_classifier import InjectionClassifier
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher
from agent.agent_core.prompt_builder import PromptBuilder
from agent.agent_core.agent_loop import AgentCore
from agent.trace_log.recorder import TraceRecorder
from agent.llm_providers.factory import createProvider
from agent.agent_router.router import AgentMode
from agent.agent_mcp.server.tool_adapter import buildAgentTools
from agent.integration.mcp_stdio import MultiServerSpec, MultiStdioMcpBridge, StdioMcpBridge


def _aliasedTool(func, name: str):
    def wrapper(**kwargs):
        return func(**kwargs)

    wrapper.__name__ = name
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = getattr(func, "__annotations__", {})
    return wrapper


def _writeAgentAlert(level: int, message: str) -> None:
    """写入 alert_events 告警表。

    延迟 import gateway DAO：避免 agent 包模块加载时依赖 gateway，
    仅在运行时（AgentSession 由 gateway 进程创建后）调用。
    失败仅记 warning（不记录 message 原文，避免敏感内容进日志），
    告警写入不得阻断 Agent 主流程。
    """
    try:
        from gateway.dao.SystemInfoDao import SystemInfoDao
        SystemInfoDao().createAlert(level, str(message)[:500])
    except Exception:
        logging.getLogger("ndlmpanel.agent_session").warning(
            "alert_events 告警写入失败（level=%s），已忽略", level)


class AgentSession:
    """Agent 会话 — 一次对话的生命周期。"""

    def __init__(self, config: AgentConfig,
                 userId: str = "default",
                 sessionId: str | None = None,
                 mode: AgentMode = AgentMode.AGENT,
                 toolSource: str = "current_mcp",
                 includeCoreTools: bool = False,
                 mcpServers: list[dict] | None = None,
                 autoApproveScheduled: bool = False,
                 nonInteractiveApprovals: bool = False,
                 scheduledApprovalPolicy: dict | None = None,
                 source: str = "manual",
                 autoRunTaskId: int | None = None,
                 autoRunGuidance: str = ""):
        self._config = config
        self._userId = userId
        self._sessionId = sessionId or gen_session_id()
        self._mode = mode

        # 初始化日志体系（幂等，多 session 共享同一套 handler）
        from agent.trace_log.logging_setup import setupLogging
        setupLogging()

        # 加载 Prompt 模板
        import os as _os
        # 项目根 = 3 层上级（agent/integration/session.py → agent → 项目根）
        root = _os.path.dirname(_os.path.dirname(
            _os.path.dirname(_os.path.abspath(__file__))))

        # ── Agent 工作区路径（优先从配置读取，兜底为项目根目录下的 workspace/）──
        configured = getattr(config, "workspace_dir", "") or ""
        if not configured:
            try:
                from agent.config_envs.loader import loadWorkspaceDirFromProject
                configured = loadWorkspaceDirFromProject()
            except Exception:
                pass
        if configured:
            self._workspaceDir = configured
        else:
            self._workspaceDir = _os.path.join(root, "workspace")
        _os.makedirs(self._workspaceDir, exist_ok=True)

        sysPrompt = loadPrompt(
            "system/v1.2.0.txt", fallback="你是一个智能运维助手。"
        )

        # 模式指令不再拼入 system prompt — 由 AgentCore._injectModePrompt 在每次 LLM 调用前注入
        # （KV-Cache 优化：固定 system prompt → 前缀缓存命中）
        safetyRules = loadPrompt("safety/rules_summary.txt", fallback="")

        # ── 为 MCP 子进程注入默认 workspace cwd ──
        if mcpServers and toolSource in ("stdio", "mcp_stdio", "stdio_mcp"):
            mcpServers = [
                {**s, "cwd": s.get("cwd") or self._workspaceDir}
                for s in mcpServers
            ]

        registry, dispatcher, self._stdioMcpBridge = self._buildToolBackend(
            toolSource,
            includeCoreTools,
            mcpServers,
            excludeInteractiveTools=nonInteractiveApprovals,
        )
        self._registry = registry

        # 核心组件
        safety = RuleEngine(config.safety_policy)
        canary = CanaryManager(enabled=config.canary_enabled)

        # ── 运维经验库摘要（组织记忆，会话固定一次，KV-Cache 前缀稳定）──
        # 表不存在/服务异常时返回空摘要，绝不阻塞会话创建
        extraKnowledge: str | None = None
        try:
            from gateway.service.OpsExperienceService import OpsExperienceService
            summary = OpsExperienceService().knowledgeSummary()
            extraKnowledge = summary or None
        except Exception:
            logging.getLogger("ndlmpanel.agent_session").warning(
                "运维经验库摘要生成失败，本次会话跳过经验注入")

        promptBuilder = PromptBuilder(
            sysPrompt, safetyRules, canary=canary, extraKnowledge=extraKnowledge
        )

        # LLM Provider — 由工厂按 config.llm_provider 选择，
        # 无 api_key 时自动回退 MockProvider
        self._llm = createProvider(config)

        # ── 注入防护：第三方 LLM 分类器（独立 provider，避免与主对话共享状态）──
        injectionClassifier: InjectionClassifier | None = None
        if config.injection_llm_mode != "off" and config.llm_api_key:
            from agent.llm_providers.mock import MockProvider
            clfProvider = createProvider(config)
            if not isinstance(clfProvider, MockProvider):
                injectionClassifier = InjectionClassifier(
                    provider=clfProvider,
                    mode=config.injection_llm_mode,
                    samplingRate=config.injection_sampling_rate,
                )
        # 注册全部工具 — 不再按模式过滤
        # （KV-Cache 优化：tools 参数始终一致 → 前缀缓存命中）
        # 模式门控下沉到 RuleEngine（后端硬规则）
        if hasattr(self._llm, "setTools"):
            self._llm.setTools(registry.listTools())

        self._recorder = TraceRecorder(config.trace_db_path)
        self._core = AgentCore(
            llmProvider=self._llm, registry=registry,
            dispatcher=dispatcher, safety=safety,
            promptBuilder=promptBuilder,
            maxRounds=config.max_tool_rounds,
            maxTokens=config.llm_max_tokens,
            contextWindow=config.llm_context_window,
            maxToolCallsPerRound=config.max_tool_calls_per_round,
            mode=self._mode,
            autoApproveScheduled=autoApproveScheduled,
            nonInteractiveApprovals=nonInteractiveApprovals,
            scheduledApprovalPolicy=scheduledApprovalPolicy,
            autoRunTaskId=autoRunTaskId,
            autoRunSource=source,
            autoRunGuidance=autoRunGuidance,
            injectionClassifier=injectionClassifier,
            canary=canary,
            alertSink=_writeAgentAlert,
        )
        self._core.setRecorder(self._recorder)
        self._runTask: "asyncio.Task | None" = None

    @staticmethod
    def _buildToolBackend(
        toolSource: str,
        includeCoreTools: bool,
        mcpServers: list[dict] | None = None,
        excludeInteractiveTools: bool = False,
    ):
        normalized = toolSource.replace("-", "_").lower()
        if normalized in {"current_mcp", "mcp"}:
            # current_mcp 模式下忽略 mcpServers（从 stdio 切回时 DB 可能残留旧值）
            registry = ToolRegistry.withDefaultTools()
            dispatcher = McpDispatcher(registry)
            bridge = None
        elif normalized in {"stdio", "mcp_stdio", "stdio_mcp"}:
            if includeCoreTools:
                raise ValueError("includeCoreTools is not supported with stdio MCP")
            if not mcpServers:
                raise ValueError(
                    "toolSource=stdio requires at least one mcpServers entry"
                )
            specs = [
                MultiServerSpec(
                    name=s["name"],
                    command=s["command"],
                    cwd=s.get("cwd"),
                )
                for s in mcpServers
            ]
            bridge = MultiStdioMcpBridge(specs)
            registry = bridge.registry
            dispatcher = bridge.dispatcher
        else:
            raise ValueError(
                "toolSource must be one of: current_mcp, mcp, stdio, mcp_stdio"
            )

        # 始终注册 submitPlan + ask_choice（两阶段 Plan 模式必需，不依赖 includeCoreTools）
        # 无人值守（定时任务/巡检）除外：这些交互工具需要人工在线响应，直接剔除。
        existing = {
            tool["function"]["name"]
            for tool in registry.listTools()
        }
        if "submitPlan" not in existing and not excludeInteractiveTools:
            from agent.agent_mcp.server.tool_adapter import submitPlan as _submitPlan
            registry.register(_submitPlan, "read_only")
            existing.add("submitPlan")
        if "ask_choice" not in existing and not excludeInteractiveTools:
            from agent.agent_mcp.server.tool_adapter import ask_choice as _ask_choice
            registry.register(_ask_choice, "read_only")
            existing.add("ask_choice")

        if includeCoreTools:
            for tool in buildAgentTools():
                func = tool.func
                name = tool.name
                if name == "submitPlan" and not excludeInteractiveTools:
                    continue  # 已在上方注册
                if name in existing:
                    name = f"core_{name}"
                    func = _aliasedTool(tool.func, name)
                registry.register(func, tool.riskLevel)
                existing.add(name)

        # 无人值守：剔除需人工在线的交互/特权工具（默认工具集中可能已注册）
        if excludeInteractiveTools:
            for name in (
                "submitPlan", "ask_choice", "submitElevation",
                "runPrivileged", "writePrivilegedFile",
                "nginxWriteStaticFile",
            ):
                unregister = getattr(registry, "unregister", None)
                if unregister is not None:
                    unregister(name)

        return registry, dispatcher, bridge

    @classmethod
    def fromConfigFile(cls, path: str, **kwargs) -> AgentSession:
        config = loadConfig(path)
        return cls(config, **kwargs)

    async def submit(
        self,
        message: str,
        conversationHistory: list[dict] | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """提交用户消息，返回事件流。"""
        stream = EventStream(self._sessionId)
        stream.emit(EventType.SESSION_CREATED, {"user_id": self._userId})
        self._recorder.record(stream.traceId, self._sessionId,
                              EventType.SESSION_CREATED, {"user_id": self._userId})

        # 运行 AgentCore 循环。run() 内部保证无论成功/异常都会向 stream
        # 发出终止事件（DONE / ERROR），因此消费端 async for 不会永久挂起。
        self._runTask = asyncio.create_task(
            self._core.run(message, stream, conversationHistory=conversationHistory)
        )

        try:
            async for ev in stream:
                yield ev
        finally:
            # 消费提前结束（如调用方 break）时，确保后台任务被妥善取消
            if self._runTask and not self._runTask.done():
                self._runTask.cancel()

    def approve(self, actionId: str) -> bool:
        """批准一个待审批的高危动作。

        Returns:
            True = 成功放行；False = 无此 action_id（已超时或已处理）
        """
        ok = self._core.approve(actionId)
        if ok:
            self._recorder.record(gen_trace_id(), self._sessionId,
                                  EventType.APPROVAL_RESOLVED,
                                  {"action_id": actionId, "approved": True})
        return ok

    def reject(self, actionId: str, reason: str = "") -> bool:
        """拒绝一个待审批的高危动作。"""
        ok = self._core.reject(actionId, reason)
        if ok:
            self._recorder.record(gen_trace_id(), self._sessionId,
                                  EventType.APPROVAL_RESOLVED,
                                  {"action_id": actionId, "approved": False,
                                   "reason": reason})
        return ok

    def approvePlan(self) -> bool:
        """批准当前待审批的计划（两阶段 Plan 模式）。"""
        return self._core.approvePlan()

    def rejectPlan(self, reason: str = "") -> bool:
        """拒绝当前待审批的计划。"""
        return self._core.rejectPlan(reason)

    def resolveChoice(self, actionId: str,
                      selectionId: str, customInput: str = "") -> bool:
        """响应当前待回复的选择题。"""
        return self._core.resolveChoice(selectionId, customInput)

    def switchMode(self, mode: AgentMode) -> None:
        """切换 Agent 运行模式，即时生效。

        KV-Cache 优化：不再重新 setTools — tools 参数始终不变。
        模式门控通过 AgentCore._injectModePrompt（前端文本约束）
        + RuleEngine（后端硬规则）实现。

        更新影响：
        1. self._mode / self._core._mode — 影响 RuleEngine 执行层门控
        2. AgentCore 的 _mode — 影响 _injectModePrompt 选择哪个模式指令

        Args:
            mode: 目标模式（read_only / plan / agent / break_glass / executing）
        """
        self._mode = mode
        self._core._mode = mode

    def getTrace(self) -> list[dict]:
        """获取当前会话的全部审计记录。"""
        return self._recorder.query(sessionId=self._sessionId)

    def close(self) -> None:
        """关闭会话，释放资源。"""
        if self._runTask and not self._runTask.done():
            self._runTask.cancel()
        if self._stdioMcpBridge is not None:
            self._stdioMcpBridge.close()
            self._stdioMcpBridge = None
        self._recorder.close()
