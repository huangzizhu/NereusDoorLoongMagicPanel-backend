"""TraceLog — 审计日志系统。JSONL + SQLite + 哈希链 + 脱敏。"""

# TraceRecorder / TraceStorage 等有重型 transitive 依赖（OrmEngine/DB），
# 使用 PEP 562 __getattr__ 延迟到首次访问时加载。
# 这样 import agent.trace_log（或 import agent.trace_log.logging_setup）不会触发 OrmEngine。
_LAZY_IMPORTS = {
    "TraceRecorder": ("agent.trace_log.recorder", "TraceRecorder"),
    "TraceStorage": ("agent.trace_log.storage", "TraceStorage"),
    "HashChain": ("agent.trace_log.hash_chain", "HashChain"),
    "sanitize": ("agent.trace_log.sanitizer", "sanitize"),
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        mod_path, attr_name = _LAZY_IMPORTS[name]
        import importlib

        mod = importlib.import_module(mod_path)
        return getattr(mod, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["TraceRecorder", "TraceStorage", "HashChain", "sanitize"]
