"""
Agent 路由器 — 模式控制与意图路由。

轻量实现：四种运行模式通过 System Prompt 注入实现，
不做完整的意图分类器（比赛演示不需要）。
"""
from agent.agent_router.router import AgentMode, AgentRouter, getModePrompt
__all__ = ["AgentMode", "AgentRouter", "getModePrompt"]
