"""
NDLMPanel-Agent — 智能运维 Agent 内核

纯 Python 标准库实现，零外部依赖。
目标平台：LoongArch + 麒麟高级服务器版 V11，Python 3.10+。

公共 API：
    from agent import AgentSession, AgentConfig, loadConfig
"""

__version__ = "0.1.0"

# 轻量导入 — 仅引入不会有 import 副作用的模块
from agent.shared.types import AgentConfig, AgentEvent, EventType
from agent.trace_log.logging_setup import setupLogging, getLogger

# AgentSession / loadConfig 有重型 transitive 依赖（OrmEngine/DB），
# 使用 PEP 562 __getattr__ 延迟到首次访问时加载。
# 这样 import agent（或 import agent.agent_mcp 等子包）不会触发 OrmEngine。
_LAZY_IMPORTS = {
    "AgentSession": ("agent.integration.session", "AgentSession"),
    "loadConfig": ("agent.config_envs.loader", "loadConfig"),
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        mod_path, attr_name = _LAZY_IMPORTS[name]
        import importlib

        mod = importlib.import_module(mod_path)
        return getattr(mod, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AgentSession",
    "AgentConfig",
    "AgentEvent",
    "EventType",
    "loadConfig",
    "setupLogging",
    "getLogger",
    "__version__",
]
