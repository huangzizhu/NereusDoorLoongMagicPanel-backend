"""ContextManagement — 系统快照采集 + 上下文压缩。"""
from agent.context_mgmt.collectors import getSystemSnapshot
from agent.context_mgmt.compressor import compressHistory
__all__ = ["getSystemSnapshot", "compressHistory"]
