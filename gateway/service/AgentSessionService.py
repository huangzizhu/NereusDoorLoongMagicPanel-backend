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

    # ── Token 计费 ──

    def getTokenUsage(self, sessionId: str, userId: int) -> list:
        if self.dao.getSession(sessionId, userId) is None:
            raise InvalidParamException(
                userMessage=f"不存在 sessionId 为 {sessionId} 的 Agent 会话"
            )
        from gateway.dao.AgentTokenUsageDaoOrm import AgentTokenUsageDaoOrm
        from pojo.Agent import AgentTokenUsageResponse
        usageDao = AgentTokenUsageDaoOrm()
        rows = usageDao.getSessionUsage(sessionId)
        return [AgentTokenUsageResponse.model_validate(r) for r in rows]

    def getSessionBilling(self, sessionId: str, userId: int) -> dict:
        if self.dao.getSession(sessionId, userId) is None:
            raise InvalidParamException(
                userMessage=f"不存在 sessionId 为 {sessionId} 的 Agent 会话"
            )
        from gateway.dao.AgentTokenUsageDaoOrm import AgentTokenUsageDaoOrm
        usageDao = AgentTokenUsageDaoOrm()
        return usageDao.getSessionBilling(sessionId)
