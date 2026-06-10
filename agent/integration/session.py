"""AgentSession — 对外唯一入口。

后端（FastAPI）通过 AgentSession 与 Agent 内核交互：
    session = AgentSession(config)
    async for event in session.submit("帮我看看磁盘") :
        yield formatSSE(event)

S6 更新：AgentCore 替换 Worker 模式。
"""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
from agent.shared.types import AgentConfig, AgentEvent, EventType
from agent.shared.id_gen import gen_session_id, gen_trace_id
from agent.config_envs.loader import loadConfig
from agent.integration.event_stream import EventStream
from agent.safety.rule_engine import RuleEngine
from ndlmpanel_agent.mcp.server.registry import ToolRegistry
from ndlmpanel_agent.mcp.server.dispatcher import McpDispatcher
from agent.agent_core.prompt_builder import PromptBuilder
from agent.agent_core.agent_loop import AgentCore
from agent.trace_log.recorder import TraceRecorder
from agent.llm_providers.factory import createProvider
from agent.agent_router.router import AgentMode, getModePrompt
from agent.agent_mcp.server.tool_adapter import buildAgentTools
from agent.integration.mcp_stdio import MultiServerSpec, MultiStdioMcpBridge, StdioMcpBridge


def _aliasedTool(func, name: str):
    def wrapper(**kwargs):
        return func(**kwargs)

    wrapper.__name__ = name
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = getattr(func, "__annotations__", {})
    return wrapper


class AgentSession:
    """Agent 会话 — 一次对话的生命周期。"""

    def __init__(self, config: AgentConfig,
                 userId: str = "default",
                 sessionId: str | None = None,
                 mode: AgentMode = AgentMode.AGENT,
                 toolSource: str = "current_mcp",
                 includeCoreTools: bool = False,
                 mcpServers: list[dict] | None = None):
        self._config = config
        self._userId = userId
        self._sessionId = sessionId or gen_session_id()
        self._mode = mode

        # 初始化日志体系（幂等，多 session 共享同一套 handler）
        from agent.trace_log.logging_setup import setupLogging
        setupLogging()

        # 加载 Prompt 模板
        import os as _os
        root = _os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.dirname(_os.path.abspath(__file__)))))
        sysPromptPath = _os.path.join(root, "conf", "prompts", "system", "v1.1.0.txt")
        safetyRulesPath = _os.path.join(root, "conf", "prompts", "safety", "rules_summary.txt")

        try:
            with open(sysPromptPath) as f:
                sysPrompt = f.read()
        except FileNotFoundError:
            sysPrompt = "你是一个智能运维助手。"

        # 注入模式约束 (ReadOnly/Plan/Agent/BreakGlass)
        sysPrompt += getModePrompt(mode)
        try:
            with open(safetyRulesPath) as f:
                safetyRules = f.read()
        except FileNotFoundError:
            safetyRules = ""

        registry, dispatcher, self._stdioMcpBridge = self._buildToolBackend(
            toolSource,
            includeCoreTools,
            mcpServers,
        )

        # 核心组件
        safety = RuleEngine(config.safety_policy)
        promptBuilder = PromptBuilder(sysPrompt, safetyRules)

        # LLM Provider — 由工厂按 config.llm_provider 选择，
        # 无 api_key 时自动回退 MockProvider
        self._llm = createProvider(config)
        # Anthropic 格式需要把工具列表作为 tools 参数发送
        if hasattr(self._llm, "setTools"):
            self._llm.setTools(registry.listTools())

        self._recorder = TraceRecorder(config.trace_db_path)
        self._core = AgentCore(
            llmProvider=self._llm, registry=registry,
            dispatcher=dispatcher, safety=safety,
            promptBuilder=promptBuilder,
            maxRounds=config.max_tool_rounds,
            maxTokens=config.llm_max_tokens,
            maxToolCallsPerRound=config.max_tool_calls_per_round,
        )
        self._core.setRecorder(self._recorder)
        self._runTask: "asyncio.Task | None" = None

    @staticmethod
    def _buildToolBackend(
        toolSource: str,
        includeCoreTools: bool,
        mcpServers: list[dict] | None = None,
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

        if includeCoreTools:
            existing = {
                tool["function"]["name"]
                for tool in registry.listTools()
            }
            for tool in buildAgentTools():
                func = tool.func
                name = tool.name
                if name in existing:
                    name = f"core_{name}"
                    func = _aliasedTool(tool.func, name)
                registry.register(func, tool.riskLevel)
                existing.add(name)

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
