from gateway.Singleton import Singleton, singletonInit
from utils.toolFunction import (
    checkDatabaseInstalled,
    getDatabaseStatus,
    testMysqlConnection,
    _getCreateDbInfo,
    _getCreateUserInfo,
    _getDatabaseListSql,
)
from utils.toolFunction.exceptions import (
    PermissionDeniedException,
    ServiceUnavailableException,
    ToolExecutionException,
)
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from Exception.ExecutePermissionDeniedException import ExecutePermissionDeniedException
from gateway.service.PrivilegedAgentClient import (
    PrivilegedAgentClient,
    PrivilegedAgentRemoteError,
)
from privileged_agent.models import PrivilegedAction
from pojo.Database import MysqlConnectionTestRequest, CreateDatabaseRequest, CreateUserRequest


class DatabaseService(Singleton):
    @singletonInit
    def __init__(self):
        self.privilegedAgentClient = PrivilegedAgentClient()

    def _agentContext(self):
        return self.privilegedAgentClient.defaultContext("gateway.database")

    def _callPrivilegedAgent(self, action: PrivilegedAction, payload: dict, userMessage: str):
        try:
            return self.privilegedAgentClient.call(action, payload, self._agentContext())
        except PrivilegedAgentRemoteError as e:
            if e.code in ["PERMISSION_DENIED", "PROXY_PERMISSION_DENIED"]:
                raise ExecutePermissionDeniedException(
                    innerMessage=e.details or e.message,
                    userMessage=userMessage,
                    cause=e,
                )
            raise BuiltinToolExecutionException(
                innerMessage=e.details or e.message,
                userMessage=userMessage,
                cause=e,
            )

    def _wrap(self, userMessage: str, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(
                innerMessage=e.innerMessage,
                userMessage=userMessage,
                cause=e,
            )
        except ServiceUnavailableException as e:
            raise BuiltinToolExecutionException(
                innerMessage=e.innerMessage,
                userMessage=e.userMessage or userMessage,
                cause=e,
            )
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(
                innerMessage=e.innerMessage,
                userMessage=userMessage,
                cause=e,
            )

    # ── 已有接口 ──

    def getInstallInfo(self, databaseType: str):
        return self._wrap("读取数据库安装信息失败", checkDatabaseInstalled, databaseType)

    def getStatus(self, databaseType: str):
        return self._wrap("读取数据库运行状态失败", getDatabaseStatus, databaseType)

    def testMysql(self, request: MysqlConnectionTestRequest):
        return self._wrap(
            "测试 MySQL 连接失败",
            testMysqlConnection,
            request.host,
            request.port,
            request.username,
            request.password,
        )

    # ── 新建：创建数据库（通过 PrivilegedAgent） ──

    def createDatabase(self, request: CreateDatabaseRequest) -> dict:
        dbInfo = _getCreateDbInfo(request.dbName)
        return self._callPrivilegedAgent(
            PrivilegedAction.MYSQL_CREATE_DATABASE,
            {"dbName": dbInfo["dbName"]},
            "创建数据库失败",
        )

    # ── 新建：创建用户并授权（通过 PrivilegedAgent） ──

    def createUser(self, request: CreateUserRequest) -> dict:
        userInfo = _getCreateUserInfo(request.dbName, request.username, request.password)
        return self._callPrivilegedAgent(
            PrivilegedAction.MYSQL_CREATE_USER,
            {
                "dbName": userInfo["dbName"],
                "username": userInfo["username"],
                "password": userInfo["password"],
            },
            "创建用户失败",
        )

    # ── 新建：获取数据库列表（通过 PrivilegedAgent） ──

    def getDatabaseList(self) -> list[str]:
        result = self._callPrivilegedAgent(
            PrivilegedAction.MYSQL_GET_DATABASE_LIST,
            {},
            "获取数据库列表失败",
        )
        return result.get("databases", [])
