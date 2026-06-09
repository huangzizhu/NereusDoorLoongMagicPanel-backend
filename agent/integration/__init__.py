"""Integration 对接层 — AgentSession + EventStream。

注意：为避免 AgentSession 与 AgentCore 之间的循环导入，
AgentSession 不在模块顶层导入（__init__.py），各调用方直接
from agent.integration.session import AgentSession。
"""
from agent.integration.event_stream import EventStream

__all__ = ["EventStream"]
