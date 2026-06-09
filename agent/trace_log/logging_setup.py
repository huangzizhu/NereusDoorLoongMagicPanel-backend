"""
日志初始化 — 纯标准库，零依赖。

提供结构化（JSON Lines）的运行日志，与 trace_log（审计哈希链）分工：
- 本模块：面向运维/调试的运行日志（DEBUG/INFO/WARNING/ERROR），
  控制台输出人类可读格式，文件输出 JSON Lines 便于机器解析
- trace_log：面向审计的防篡改事件链，独立存储

约定：
- logger 命名空间统一为 "ndlmpanel"，子模块用 "ndlmpanel.<module>"
- setupLogging() 幂等：重复调用不会重复挂载 handler
- 敏感字段（api_key/token/password）由 trace_log.sanitizer 负责脱敏；
  本模块不主动记录敏感配置，调用方需自行避免把密钥写进 log message
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time

_ROOT_LOGGER_NAME = "ndlmpanel"
_CONFIGURED = False


class StructuredFormatter(logging.Formatter):
    """JSON Lines 格式化器，每条日志一行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": round(record.created, 3),
            "time": time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        # 附加 extra 中的自定义字段（如 session_id / trace_id）
        for key in ("session_id", "trace_id", "tool", "event"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        return json.dumps(entry, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """人类可读的控制台格式。"""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )


def setupLogging(
    level: str = "INFO",
    logFile: str | None = "runtime/logs/agent.log",
    console: bool = True,
) -> logging.Logger:
    """初始化 ndlmpanel 日志体系（幂等）。

    Args:
        level: 根日志级别（DEBUG/INFO/WARNING/ERROR）
        logFile: JSON Lines 日志文件路径；None 表示不写文件
        console: 是否输出到控制台（stderr）

    Returns:
        配置好的 "ndlmpanel" logger
    """
    global _CONFIGURED
    logger = logging.getLogger(_ROOT_LOGGER_NAME)

    if _CONFIGURED:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False  # 不向 root logger 冒泡，避免重复输出

    if console:
        ch = logging.StreamHandler(sys.stderr)
        ch.setFormatter(ConsoleFormatter())
        logger.addHandler(ch)

    if logFile:
        try:
            os.makedirs(os.path.dirname(logFile), exist_ok=True)
            fh = logging.FileHandler(logFile, encoding="utf-8")
            fh.setFormatter(StructuredFormatter())
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)
        except OSError:
            # 文件不可写（如只读环境）时降级为仅控制台，不阻断启动
            logger.warning("无法创建日志文件 %s，降级为仅控制台输出", logFile)

    _CONFIGURED = True
    return logger


def getLogger(name: str = "") -> logging.Logger:
    """获取 ndlmpanel 命名空间下的子 logger。"""
    if name:
        return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
    return logging.getLogger(_ROOT_LOGGER_NAME)


def _resetForTest() -> None:
    """仅供测试：重置初始化状态并关闭/清空 handler。"""
    global _CONFIGURED
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()
    _CONFIGURED = False
