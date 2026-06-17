import json

from Exception.DataBaseException import DataBaseException
from Exception.InvalidParamException import InvalidParamException
from agent.config_envs.loader import loadMcpServersFromProject
from agent.shared.id_gen import gen_session_id
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.AgentSessionDaoOrm import AgentSessionDaoOrm
from pojo.Agent import (
    AgentMessageResponse,
    AgentSessionCreate,
    AgentSessionResponse,
    McpServerSpec,
)
from pojo.Common import ListResponse


class AgentSessionService(Singleton):
    @singletonInit
    def __init__(self):
        self.dao = AgentSessionDaoOrm()

    # ── 会话 CRUD ──

    def createSession(self, userId: int,
                      request: AgentSessionCreate) -> AgentSessionResponse:
        try:
            resolved = request
            if request.toolSource == "stdio" and not request.mcpServers:
                projectServers = loadMcpServersFromProject()
                if projectServers:
                    resolved = request.model_copy(
                        update={
                            "mcpServers": [
                                McpServerSpec(**s) for s in projectServers
                            ]
                        }
                    )
            data = self.dao.createSession(gen_session_id(), userId, resolved)
            return AgentSessionResponse.model_validate(data)
        except Exception as exc:
            raise DataBaseException(
                innerMessage=str(exc),
                userMessage="数据库操作错误，请重试或联系管理员",
                cause=exc,
            )

    def getSession(self, sessionId: str, userId: int) -> AgentSessionResponse:
        data = self.dao.getSession(sessionId, userId)
        if data is None:
            raise InvalidParamException(
                userMessage=f"不存在 sessionId 为 {sessionId} 的 Agent 会话"
            )
        return AgentSessionResponse.model_validate(data)

    def listSessions(self, userId: int, page: int, pageSize: int,
                     status: str | None = None,
                     keyword: str | None = None) -> ListResponse:
        try:
            total, rows = self.dao.listSessions(userId, page, pageSize, status, keyword)
            items = [
                AgentSessionResponse.model_validate(row)
                for row in rows
            ]
            return ListResponse(total=total, items=items)
        except Exception as exc:
            raise DataBaseException(
                innerMessage=str(exc),
                userMessage="数据库操作错误，请重试或联系管理员",
                cause=exc,
            )

    def listMessages(self, sessionId: str, userId: int) -> ListResponse:
        if self.dao.getSession(sessionId, userId) is None:
            raise InvalidParamException(
                userMessage=f"不存在 sessionId 为 {sessionId} 的 Agent 会话"
            )
        rows = self.dao.listMessages(sessionId)
        items = []
        for row in rows:
            message = AgentMessageResponse.model_validate(row)
            if message.metadata:
                try:
                    message.metadata = json.loads(message.metadata)
                except Exception:
                    pass
            items.append(message)
        return ListResponse(total=len(items), items=items)

    def deleteSession(self, sessionId: str, userId: int) -> None:
        try:
            rowCount = self.dao.deleteSession(sessionId, userId)
            if not rowCount:
                raise InvalidParamException(
                    userMessage=f"不存在 sessionId 为 {sessionId} 的 Agent 会话"
                )
        except InvalidParamException:
            raise
        except Exception as exc:
            raise DataBaseException(
                innerMessage=str(exc),
                userMessage="数据库操作错误，请重试或联系管理员",
                cause=exc,
            )

    # ── 切换端点 ──

    def switchToolSource(self, sessionId: str, userId: int,
                         toolSource: str,
                         mcpServers: list[dict] | None = None) -> AgentSessionResponse:
        from datetime import datetime
        from gateway.orm.AgentSessionOrm import AgentSessionOrm
        from gateway.service.AgentGatewayService import AgentGatewayService

        self.getSession(sessionId, userId)  # 验证存在

        session = self.dao.SessionLocal()
        try:
            updateData = {"toolSource": toolSource, "updatedAt": datetime.now()}
            if mcpServers is not None:
                updateData["mcpServersJson"] = (
                    json.dumps(mcpServers, ensure_ascii=False) if mcpServers else None
                )
            rowCount = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId
            ).update(updateData)
            session.commit()
            if not rowCount:
                raise InvalidParamException(userMessage=f"更新会话 {sessionId} 失败")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        AgentGatewayService().invalidateRuntime(sessionId)
        return self.getSession(sessionId, userId)

    def switchModel(self, sessionId: str, userId: int,
                    profileId: int) -> AgentSessionResponse:
        from datetime import datetime
        from gateway.orm.AgentSessionOrm import AgentSessionOrm
        from gateway.orm.AgentLlmProfileOrm import AgentLlmProfileOrm
        from gateway.service.AgentGatewayService import AgentGatewayService

        self.getSession(sessionId, userId)  # 验证存在

        session = self.dao.SessionLocal()
        try:
            profile = session.query(AgentLlmProfileOrm).filter(
                AgentLlmProfileOrm.profileId == profileId,
                AgentLlmProfileOrm.isActive == True,
            ).one_or_none()
            if profile is None:
                raise InvalidParamException(
                    userMessage=f"不存在可用的 id 为 {profileId} 的 LLM Profile"
                )
            rowCount = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId
            ).update({"profileId": profileId, "updatedAt": datetime.now()})
            session.commit()
            if not rowCount:
                raise InvalidParamException(userMessage=f"更新会话 {sessionId} 失败")
        except InvalidParamException:
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        AgentGatewayService().invalidateRuntime(sessionId)
        return self.getSession(sessionId, userId)

    def switchMode(self, sessionId: str, userId: int,
                   mode: str) -> AgentSessionResponse:
        """切换 Agent 运行模式，即时在运行时生效 + 持久化到 DB。"""
        from datetime import datetime
        from gateway.orm.AgentSessionOrm import AgentSessionOrm
        from gateway.service.AgentGatewayService import AgentGatewayService
        from agent.agent_router.router import AgentMode

        self.getSession(sessionId, userId)  # 验证存在

        # 验证 mode 合法
        try:
            target_mode = AgentMode(mode)
        except ValueError:
            raise InvalidParamException(
                userMessage=f"不支持的 Agent 模式: {mode}，"
                f"可选: read_only / plan / agent / break_glass"
            )

        # 持久化到 DB
        session = self.dao.SessionLocal()
        try:
            rowCount = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId,
            ).update({
                "mode": target_mode.value,
                "updatedAt": datetime.now(),
            })
            session.commit()
            if rowCount == 0:
                raise InvalidParamException(userMessage=f"更新会话 {sessionId} 失败")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        # 即时生效：在运行时 session 上切换（不重建）
        gateway = AgentGatewayService()
        gateway.switchMode(sessionId, target_mode)
        return self.getSession(sessionId, userId)

    # ── Token 计费 ──

    def getTokenUsage(self, sessionId: str, userId: int) -> list:
        session = self.dao.getSession(sessionId, userId)
        if session is None:
            raise InvalidParamException(
                userMessage=f"不存在 sessionId 为 {sessionId} 的 Agent 会话"
            )
        # 获取 credentialId 以匹配用户自定义价
        credentialId = self._getCredentialId(session)
        from gateway.dao.AgentTokenUsageDaoOrm import AgentTokenUsageDaoOrm
        usageDao = AgentTokenUsageDaoOrm()
        return usageDao.getSessionUsage(sessionId, credentialId=credentialId)

    def getSessionBilling(self, sessionId: str, userId: int) -> dict:
        session = self.dao.getSession(sessionId, userId)
        if session is None:
            raise InvalidParamException(
                userMessage=f"不存在 sessionId 为 {sessionId} 的 Agent 会话"
            )
        # 获取 credentialId 以匹配用户自定义价
        credentialId = self._getCredentialId(session)
        from gateway.dao.AgentTokenUsageDaoOrm import AgentTokenUsageDaoOrm
        usageDao = AgentTokenUsageDaoOrm()
        return usageDao.getSessionBilling(sessionId, credentialId=credentialId)

    # ── 已读标记 ──

    def markRead(self, sessionId: str, userId: int) -> AgentSessionResponse:
        """标记 completed_unread 为已读（恢复为 idle）。

        前端在查看会话详情时调用，清除未读状态。
        """
        self.getSession(sessionId, userId)  # 验证存在 + 权限
        self.dao.markRead(sessionId)
        return self.getSession(sessionId, userId)

    @staticmethod
    def _getCredentialId(session) -> int | None:
        """从 session 对象获取 credentialId，用于价格匹配。"""
        from gateway.dao.AgentConfigDaoOrm import AgentConfigDaoOrm
        profileId = getattr(session, "profileId", None)
        if profileId is None:
            return None
        try:
            profile = AgentConfigDaoOrm().getProfileById(profileId)
            return profile.credentialId if profile else None
        except Exception:
            return None
