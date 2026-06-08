from pydantic import BaseModel


class DatabaseInstallInfo(BaseModel):
    isInstalled: bool
    version: str | None = None
    databaseType: str


class DatabaseStatus(BaseModel):
    isRunning: bool
    databaseType: str
    currentConnections: int | None = None
    slowQueryCount: int | None = None


class MysqlCreateDbResult(BaseModel):
    dbName: str
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_general_ci"
    isCreated: bool


class MysqlCreateUserResult(BaseModel):
    dbName: str
    username: str
    host: str = "localhost"
    privileges: str = "ALL PRIVILEGES"
    isGranted: bool
    isCreated: bool


class MysqlDatabaseListResult(BaseModel):
    databaseType: str = "mysql"
    databases: list[str]
