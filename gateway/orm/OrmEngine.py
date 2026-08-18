import logging
import os
import threading
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ProjectRoot import getProjectRootPath
from gateway.Singleton import Singleton

_logger = logging.getLogger(__name__)
_SQL_LOGGER_NAME = "sqlalchemy.engine"
_SQL_LOG_MAX_BYTES = 1 * 1024 * 1024

# 增量迁移注册表：{表名: [(列名, 列定义SQL), ...]}
_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "agent_sessions": [
        ("mcpServers", "mcpServers TEXT"),
        ("pendingChoice", "pendingChoice TEXT"),
        ("source", "source VARCHAR(32) DEFAULT 'manual'"),
    ],
    "scheduled_tasks": [
        ("approvalPolicy", "approvalPolicy TEXT"),
        ("approvalCode", "approvalCode TEXT"),
        ("approvalStatus", "approvalStatus TEXT"),
        ("approvalApprovedAt", "approvalApprovedAt DATETIME"),
        ("approvalApprovedBy", "approvalApprovedBy TEXT"),
        ("approvalTokenId", "approvalTokenId TEXT"),
        ("approvalRejectedReason", "approvalRejectedReason TEXT"),
    ],
}

# 自动删表重建 — ⚠️ 危险！仅在你确认旧 schema 数据可以丢弃时启用
# 匹配逻辑：列数 == oldColCount 时 DROP TABLE，由 SQLAlchemy create_all 重建
# 生产环境请保持为空（或至少移除你不想丢失的表）
_DROP_AND_RECREATE: dict[str, int] = {
    # "agent_messages": 6,         # 已禁用：会丢失消息历史
    # "agent_token_usage": 11,     # 已禁用：会丢失计费记录
    "agent_model_pricing": 0,      # 0 = 不存在就建，安全
}


class _DateSplitFileHandler(logging.Handler):

    def __init__(self, logDir: Path, maxBytes: int, encoding: str = "utf-8"):
        super().__init__()
        self.logDir = logDir
        self.maxBytes = maxBytes
        self.encoding = encoding
        self._fileHandler: logging.FileHandler | None = None
        self._currentPath: Path | None = None
        self._handlerLock = threading.RLock()

    def close(self) -> None:
        with self._handlerLock:
            if self._fileHandler is not None:
                self._fileHandler.close()
                self._fileHandler = None
                self._currentPath = None
        super().close()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            with self._handlerLock:
                targetPath = self._resolveTargetPath(message)
                if self._currentPath != targetPath:
                    self._switchFile(targetPath)
                if self._fileHandler is not None:
                    self._fileHandler.emit(record)
        except Exception:
            self.handleError(record)

    def _switchFile(self, targetPath: Path) -> None:
        if self._fileHandler is not None:
            self._fileHandler.close()
        fileHandler = logging.FileHandler(targetPath, encoding=self.encoding)
        fileHandler.setFormatter(self.formatter)
        self._fileHandler = fileHandler
        self._currentPath = targetPath

    def _resolveTargetPath(self, message: str) -> Path:
        currentDate = datetime.now().strftime("%Y-%m-%d")
        messageSize = len((message + "\n").encode(self.encoding))
        index = 0
        while True:
            candidate = self._buildLogPath(currentDate, index)
            if not candidate.exists():
                return candidate
            if candidate.stat().st_size + messageSize <= self.maxBytes:
                return candidate
            index += 1

    def _buildLogPath(self, currentDate: str, index: int) -> Path:
        if index == 0:
            fileName = f"{currentDate}.log"
        else:
            fileName = f"{currentDate}-{index}.log"
        return self.logDir.joinpath(fileName)


def _configureSqlAlchemyFileLogging(projectRoot: Path, enabled: bool) -> None:
    logDir = projectRoot.joinpath("log")
    logDir.mkdir(parents=True, exist_ok=True)

    sqlLogger = logging.getLogger(_SQL_LOGGER_NAME)
    sqlLogger.propagate = False

    hasHandler = False
    for handler in list(sqlLogger.handlers):
        if isinstance(handler, _DateSplitFileHandler) and handler.logDir.resolve() == logDir.resolve():
            hasHandler = True
            continue
        if isinstance(handler, logging.FileHandler):
            sqlLogger.removeHandler(handler)
            handler.close()

    if not hasHandler:
        fileHandler = _DateSplitFileHandler(logDir=logDir, maxBytes=_SQL_LOG_MAX_BYTES)
        fileHandler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        ))
        sqlLogger.addHandler(fileHandler)

    sqlLogger.setLevel(logging.INFO if enabled else logging.WARNING)


def _runMigrations(engine) -> None:
    """检查已有表的列是否完整，执行增量迁移或重建。"""
    with engine.connect() as conn:
        # 1. 重建需要 DROP+CREATE 的表
        for table, oldColCount in _DROP_AND_RECREATE.items():
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=:t",
            ), {"t": table})
            if result.fetchone() is None:
                continue  # 表不存在，create_all 会自动建
            col_result = conn.execute(text(f"PRAGMA table_info(\"{table}\")"))
            cols = col_result.fetchall()
            if oldColCount > 0 and len(cols) == oldColCount:
                _logger.info("Schema rebuild: dropping %s (cols=%d, old_col_count=%d)",
                             table, len(cols), oldColCount)
                conn.execute(text(f"DROP TABLE IF EXISTS \"{table}\""))
                _logger.info("Dropped table %s, will be recreated by create_all", table)

        # 2. 增量 ADD COLUMN 迁移
        for table, columns in _MIGRATIONS.items():
            result = conn.execute(text(f"PRAGMA table_info(\"{table}\")"))
            existing = {row[1] for row in result.fetchall()}
            for col_name, col_def in columns:
                if col_name not in existing:
                    sql = f'ALTER TABLE "{table}" ADD COLUMN {col_def}'
                    conn.execute(text(sql))
                    _logger.info("Migration: %s", sql)
        conn.commit()


class OrmEngine(Singleton):

    def __init__(self):
        projectRoot = getProjectRootPath()
        self.dbFile: Path = projectRoot.joinpath("panel.db")
        self.DATABASE_URL = f"sqlite:///{self.dbFile.resolve().as_posix()}"
        echo_sql = os.getenv("NDLM_SQLALCHEMY_ECHO", "").lower() in {"1", "true", "yes", "on"}
        _configureSqlAlchemyFileLogging(projectRoot, echo_sql)
        self.engine = create_engine(self.DATABASE_URL, echo=False)
        self.Base = declarative_base()
        self._db_initialized = False
        # 先确保数据库文件所在目录存在，避免首次部署时目录缺失导致初始化失败。
        self.dbFile.parent.mkdir(parents=True, exist_ok=True)

    def ensureDbInit(self) -> None:
        """延迟初始化：在所有 ORM 模型加载完成后，创建表并运行迁移。

        必须在所有 ORM 模型（继承 self.Base 的类）被 Python 加载后调用，
        否则 self.Base.metadata 为空，表不会被创建。
        最佳调用时机：应用启动时，所有 controller import 完成之后。
        """
        if not self._db_initialized:
            # SQLite 在首次连接时会创建空文件，这里显式 touch 一次便于部署期校验。
            self.dbFile.touch(exist_ok=True)
            self.Base.metadata.create_all(self.engine)
            _runMigrations(self.engine)
            self._db_initialized = True

    def createSessionFactory(self):
        self.ensureDbInit()
        return sessionmaker(bind=self.engine)

    def getBase(self):
        return self.Base
