"""
数据库管理工具函数。

双入口：
  - LLM Agent 入口：函数直接调用（useSudo=True）
  - REST API 入口：走 Service → PrivilegedAgent

新增函数供 PrivilegedAgent 使用：
  - _getCreateDbInfo(dbName) → 返回 { dbName, sql }
  - _getCreateUserInfo(dbName, username, password) → 返回 { dbName, username, password }
  - _getDatabaseListSql() → 返回 { sql }
"""

import re
from typing import Any

from utils.toolFunction.exceptions import ToolExecutionException
from utils.toolFunction.models.ops.misc.database_models import (
    DatabaseInstallInfo,
    DatabaseStatus,
    MysqlCreateDbResult,
    MysqlCreateUserResult,
    MysqlDatabaseListResult,
)
from utils.toolFunction.tools.ops._command_runner import runCommand

# 数据库类型 → 版本检测命令
_VERSION_COMMANDS: dict[str, list[str]] = {
    "mysql": ["mysql", "--version"],
    "mariadb": ["mysql", "--version"],
    "postgresql": ["psql", "--version"],
    "postgres": ["psql", "--version"],
    "redis": ["redis-server", "--version"],
    "mongodb": ["mongod", "--version"],
}

# 数据库类型 → systemd 服务名候选
_SERVICE_NAMES: dict[str, list[str]] = {
    "mysql": ["mysql", "mysqld", "mariadb"],
    "mariadb": ["mariadb", "mysql", "mysqld"],
    "postgresql": ["postgresql", "postgres"],
    "postgres": ["postgresql", "postgres"],
    "redis": ["redis", "redis-server"],
    "mongodb": ["mongod", "mongodb"],
}


# ═══════════════════════════════════════════════════════════
# 基础检测
# ═══════════════════════════════════════════════════════════

def checkDatabaseInstalled(databaseType: str = "mysql") -> DatabaseInstallInfo:
    dbType = databaseType.lower()
    cmd = _VERSION_COMMANDS.get(dbType)
    if not cmd:
        return DatabaseInstallInfo(isInstalled=False, databaseType=databaseType)

    try:
        result = runCommand(cmd, checkReturnCode=False)
        output = result.stdout.strip() or result.stderr.strip()
        match = re.search(r"(\d+\.\d+\.\d+)", output)
        return DatabaseInstallInfo(
            isInstalled=True,
            version=match.group(1) if match else output[:50],
            databaseType=databaseType,
        )
    except ToolExecutionException:
        return DatabaseInstallInfo(isInstalled=False, databaseType=databaseType)


def getDatabaseStatus(databaseType: str = "mysql") -> DatabaseStatus:
    dbType = databaseType.lower()
    serviceNames = _SERVICE_NAMES.get(dbType, [dbType])

    isRunning = False
    for name in serviceNames:
        try:
            result = runCommand(["systemctl", "is-active", name], checkReturnCode=False)
            if result.stdout.strip() == "active":
                isRunning = True
                break
        except ToolExecutionException:
            continue

    currentConnections = None
    slowQueryCount = None

    if isRunning and dbType in ("mysql", "mariadb"):
        try:
            result = runCommand(
                ["mysqladmin", "status"], checkReturnCode=False, timeout=5
            )
            if result.returncode == 0:
                tMatch = re.search(r"Threads:\s*(\d+)", result.stdout)
                sMatch = re.search(r"Slow queries:\s*(\d+)", result.stdout)
                if tMatch:
                    currentConnections = int(tMatch.group(1))
                if sMatch:
                    slowQueryCount = int(sMatch.group(1))
        except ToolExecutionException:
            pass

    return DatabaseStatus(
        isRunning=isRunning,
        databaseType=databaseType,
        currentConnections=currentConnections,
        slowQueryCount=slowQueryCount,
    )


# ═══════════════════════════════════════════════════════════
# MySQL 连接测试
# ═══════════════════════════════════════════════════════════

def testMysqlConnection(host: str, port: int, username: str, password: str) -> dict:
    cmd = [
        "mysqladmin",
        "-h", str(host),
        "-P", str(port),
        "-u", username,
        f"-p{password}",
        "ping",
    ]
    result = runCommand(cmd, checkReturnCode=False, timeout=5)

    is_connectable = result.returncode == 0 and "is alive" in result.stdout.lower()

    if is_connectable:
        return {
            "isConnectable": True,
            "host": host,
            "port": port,
            "username": username,
        }
    errorMessage = result.stderr.strip() or result.stdout.strip()
    return {
        "isConnectable": False,
        "host": host,
        "port": port,
        "username": username,
        "errorMessage": errorMessage,
    }


# ═══════════════════════════════════════════════════════════
# 标识符校验 & 转义（内部使用）
# ═══════════════════════════════════════════════════════════

def _validateMysqlIdentifier(name: str, fieldName: str = "名称") -> str:
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ToolExecutionException(
            f"{fieldName} '{name}' 不合法。"
            "必须以字母或下划线开头，后续字符只能是字母、数字或下划线。"
        )
    return name


def _escapeMysqlString(value: str) -> str:
    """转义 MySQL 字符串字面量中的特殊字符，用于 '...' 内部"""
    return value.replace("\\", "\\\\").replace("'", "\\'")


# ═══════════════════════════════════════════════════════════
# 建库（LLM Agent 入口 / PrivilegedAgent 信息生成）
# ═══════════════════════════════════════════════════════════

def _getCreateDbInfo(dbName: str) -> dict:
    """
    返回建库操作所需信息（供 Service→PrivilegedAgent 使用）。
    返回 { dbName, sql }。
    """
    dbName = _validateMysqlIdentifier(dbName, "数据库名称")
    sql = (
        f"CREATE DATABASE IF NOT EXISTS `{dbName}`"
        " CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
    )
    return {"dbName": dbName, "sql": sql}


def createMysqlDatabase(dbName: str) -> dict:
    """创建 MySQL 数据库（LLM Agent 入口，内部 useSudo=True）。"""
    dbName = _validateMysqlIdentifier(dbName, "数据库名称")

    sql = (
        f"CREATE DATABASE IF NOT EXISTS `{dbName}`"
        " CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
    )
    result = runCommand(["mysql", "-e", sql], useSudo=True, checkReturnCode=False)

    if result.returncode != 0:
        errorMessage = result.stderr.strip() or result.stdout.strip()
        raise ToolExecutionException(f"创建数据库失败: {errorMessage}")

    return {
        "dbName": dbName,
        "charset": "utf8mb4",
        "collation": "utf8mb4_general_ci",
        "isCreated": True,
    }


# ═══════════════════════════════════════════════════════════
# 建用户授权（LLM Agent 入口 / PrivilegedAgent 信息生成）
# ═══════════════════════════════════════════════════════════

def _getCreateUserInfo(dbName: str, username: str, password: str) -> dict:
    """
    返回建用户操作所需信息（供 Service→PrivilegedAgent 使用）。
    返回 { dbName, username, password }。
    """
    dbName = _validateMysqlIdentifier(dbName, "数据库名称")
    username = _validateMysqlIdentifier(username, "用户名")
    return {"dbName": dbName, "username": username, "password": password}


def createMysqlUserAndGrant(dbName: str, username: str, password: str) -> dict:
    """创建 MySQL 用户并授权指定数据库（LLM Agent 入口，内部 useSudo=True）。"""
    dbName = _validateMysqlIdentifier(dbName, "数据库名称")
    username = _validateMysqlIdentifier(username, "用户名")
    escapedPassword = _escapeMysqlString(password)

    sql = (
        f"CREATE USER IF NOT EXISTS '{username}'@'localhost' "
        f"IDENTIFIED BY '{escapedPassword}'; "
        f"ALTER USER '{username}'@'localhost' IDENTIFIED BY '{escapedPassword}'; "
        f"GRANT ALL PRIVILEGES ON `{dbName}`.* TO '{username}'@'localhost'; "
        "FLUSH PRIVILEGES;"
    )
    result = runCommand(["mysql", "-e", sql], useSudo=True, checkReturnCode=False)

    if result.returncode != 0:
        errorMessage = result.stderr.strip() or result.stdout.strip()
        raise ToolExecutionException(f"创建用户或授权失败: {errorMessage}")

    return {
        "dbName": dbName,
        "username": username,
        "host": "localhost",
        "privileges": "ALL PRIVILEGES",
        "isGranted": True,
        "isCreated": True,
    }


# ═══════════════════════════════════════════════════════════
# 数据库列表（LLM Agent 入口 / PrivilegedAgent 信息生成）
# ═══════════════════════════════════════════════════════════

def _getDatabaseListSql() -> dict:
    """返回查询数据库列表的 SQL（供 Service→PrivilegedAgent 使用）。"""
    return {"sql": "SHOW DATABASES;"}


def getMysqlDatabaseList() -> list[str]:
    """获取所有 MySQL 数据库列表（LLM Agent 入口，内部 useSudo=True）。"""
    result = runCommand(
        ["mysql", "-e", "SHOW DATABASES;"],
        useSudo=True,
        checkReturnCode=False,
    )

    if result.returncode != 0:
        errorMessage = result.stderr.strip() or result.stdout.strip()
        raise ToolExecutionException(f"获取数据库列表失败: {errorMessage}")

    databases = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line and not line.startswith("Database"):
            databases.append(line)

    return databases
