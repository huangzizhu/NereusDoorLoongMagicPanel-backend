import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ProjectRoot import getProjectRootPath
from gateway.Singleton import Singleton

_logger = logging.getLogger(__name__)

# 增量迁移注册表：{表名: [(列名, 列定义SQL), ...]}
_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "agent_sessions": [
        ("mcpServers", "mcpServers TEXT"),
    ],
}

# 需要重建（DROP + CREATE）的表 — 当表结构发生破坏性变更时
# 删表前会检查旧 schema 摘要（通过 column count），匹配时才重建
_DROP_AND_RECREATE: dict[str, int] = {
    "agent_messages": 6,   # 旧列数
    "agent_token_usage": 11,  # 去掉 cost 列，旧表 11 列（原始结构含 inputCost/outputCost/totalCost）
    "agent_model_pricing": 0, # 全新表，0 表示不存在就建
}


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
        self.engine = create_engine(self.DATABASE_URL, echo=True)
        self.Base = declarative_base()
        self.Base.metadata.create_all(self.engine)
        _runMigrations(self.engine)

    def createSessionFactory(self):
        return sessionmaker(bind=self.engine)

    def getBase(self):
        return self.Base
