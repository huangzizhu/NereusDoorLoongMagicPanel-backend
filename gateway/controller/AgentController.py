from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from Exception.InvalidParamException import InvalidParamException
from Exception.TokenAuthException import TokenAuthException
from gateway.Response import Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.dao.UserDaoOrm import UserDaoOrm
from gateway.orm.UserOrm import UserOrm
from gateway.service.AgentGatewayService import AgentGatewayService
from gateway.service.AgentLlmProfileService import AgentLlmProfileService
from gateway.service.AgentSessionService import AgentSessionService
from gateway.service.AgentTraceService import AgentTraceService
from pojo.Agent import (
    AgentLlmProfileBatchCreate,
    AgentLlmProfileCreate,
    AgentLlmProfileUpdate,
    AgentModelSwitch,
    AgentModeSwitch,
    AgentSessionCreate,
    AgentToolSourceSwitch,
)
from utils.JWTTokenTool import getUserId


class AgentController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/agent", tags=["Agent"])
        self.sessionService = AgentSessionService()
        self.gatewayService = AgentGatewayService()
        self.profileService = AgentLlmProfileService()
        self.traceService = AgentTraceService()
        self.userDao: UserDaoInterface = UserDaoOrm()
        super().__init__("agentController", self.router)
        self.routerSetup()

    def _getRequestUserId(self, request: Request) -> int:
        accessToken = request.cookies.get("accessToken")
        if not accessToken:
            raise TokenAuthException(userMessage="未携带accessToken")
        userId = getUserId(accessToken)
        if not userId:
            raise TokenAuthException(userMessage="Token非法")
        return int(userId)

    async def _getWsUser(self, websocket: WebSocket) -> UserOrm:
        accessToken = websocket.cookies.get("accessToken")
        if not accessToken:
            raise TokenAuthException(userMessage="未携带accessToken")
        userId = getUserId(accessToken)
        if not userId:
            raise TokenAuthException(userMessage="Token非法")
        user = self.userDao.getUserByUid(userId)
        if user is None:
            raise TokenAuthException(userMessage="Token非法")
        return user

    def routerSetup(self):
        @self.router.post("/sessions")
        def createAgentSession(request: Request, body: AgentSessionCreate):
            userId = self._getRequestUserId(request)
            return Response.success(self.sessionService.createSession(userId, body))

        @self.router.get("/sessions")
        def listAgentSessions(
            request: Request,
            page: int = Query(1, ge=1),
            pageSize: int = Query(20, ge=1, le=200),
            status: str | None = Query(None),
            keyword: str | None = Query(None),
        ):
            userId = self._getRequestUserId(request)
            return Response.success(
                self.sessionService.listSessions(userId, page, pageSize, status, keyword)
            )

        @self.router.get("/sessions/{sessionId}/messages")
        def listAgentMessages(request: Request, sessionId: str):
            userId = self._getRequestUserId(request)
            return Response.success(self.sessionService.listMessages(sessionId, userId))

        @self.router.get("/sessions/{sessionId}")
        def getAgentSession(request: Request, sessionId: str):
            userId = self._getRequestUserId(request)
            return Response.success(self.sessionService.getSession(sessionId, userId))

        @self.router.delete("/sessions/{sessionId}")
        def deleteAgentSession(request: Request, sessionId: str):
            userId = self._getRequestUserId(request)
            self.sessionService.deleteSession(sessionId, userId)
            return Response.success()

        @self.router.get("/sessions/{sessionId}/usage")
        def getTokenUsage(request: Request, sessionId: str):
            userId = self._getRequestUserId(request)
            return Response.success(self.sessionService.getTokenUsage(sessionId, userId))

        @self.router.get("/sessions/{sessionId}/billing")
        def getSessionBilling(request: Request, sessionId: str):
            userId = self._getRequestUserId(request)
            return Response.success(self.sessionService.getSessionBilling(sessionId, userId))

        @self.router.put("/sessions/{sessionId}/mark-read")
        def markSessionRead(request: Request, sessionId: str):
            """标记 completed_unread 为已读，恢复 idle 状态。"""
            userId = self._getRequestUserId(request)
            return Response.success(
                self.sessionService.markRead(sessionId, userId)
            )

        @self.router.put("/sessions/{sessionId}/tool-source")
        def switchAgentToolSource(request: Request, sessionId: str,
                                   body: AgentToolSourceSwitch):
            userId = self._getRequestUserId(request)
            mcps = [m.model_dump() for m in body.mcpServers] if body.mcpServers else None
            return Response.success(
                self.sessionService.switchToolSource(
                    sessionId, userId, body.toolSource, mcps
                )
            )

        @self.router.put("/sessions/{sessionId}/switch-model")
        def switchAgentModel(request: Request, sessionId: str,
                              body: AgentModelSwitch):
            userId = self._getRequestUserId(request)
            return Response.success(
                self.sessionService.switchModel(sessionId, userId, body.profileId)
            )

        @self.router.put("/sessions/{sessionId}/mode")
        def switchAgentMode(request: Request, sessionId: str,
                             body: AgentModeSwitch):
            userId = self._getRequestUserId(request)
            return Response.success(
                self.sessionService.switchMode(sessionId, userId, body.mode)
            )

        @self.router.post("/llm/profiles")
        def createLlmProfile(body: AgentLlmProfileCreate):
            return Response.success(self.profileService.createProfile(body))

        @self.router.post("/llm/profiles/batch")
        def createLlmProfilesBatch(body: AgentLlmProfileBatchCreate):
            return Response.success(self.profileService.createProfilesBatch(body))

        @self.router.get("/llm/profiles")
        def listLlmProfiles():
            return Response.success(self.profileService.listProfiles())

        @self.router.get("/llm/credentials/{credentialId}/models")
        def getCredentialModels(credentialId: int):
            return Response.success(self.profileService.getCredentialModels(credentialId))

        @self.router.post("/llm/profiles/{profileId}/test")
        async def testLlmProfileModel(profileId: int):
            return Response.success(await self.profileService.testProfileModel(profileId))

        @self.router.get("/llm/profiles/default")
        def getDefaultLlmProfile():
            return Response.success(self.profileService.getDefaultProfile())

        @self.router.put("/llm/profiles/{profileId}")
        def updateLlmProfile(profileId: int, body: AgentLlmProfileUpdate):
            return Response.success(self.profileService.updateProfile(profileId, body))

        @self.router.put("/llm/profiles/{profileId}/default")
        def setDefaultLlmProfile(profileId: int):
            return Response.success(self.profileService.setDefaultProfile(profileId))

        @self.router.delete("/llm/profiles/{profileId}")
        def deleteLlmProfile(profileId: int):
            self.profileService.deleteProfile(profileId)
            return Response.success()

        @self.router.get("/traces")
        def queryTraces(
            sessionId: str | None = Query(None),
            traceId: str | None = Query(None),
            eventType: str | None = Query(None),
            limit: int = Query(100, ge=1, le=1000),
        ):
            return Response.success(
                self.traceService.queryTraces(sessionId, traceId, eventType, limit)
            )

        @self.router.get("/traces/{sessionId}/timeline")
        def traceTimeline(sessionId: str, limit: int = Query(200, ge=1, le=1000)):
            return Response.success(self.traceService.timeline(sessionId, limit))

        @self.router.get("/traces/{sessionId}/summary")
        def traceSummary(sessionId: str):
            return Response.success(self.traceService.summary(sessionId))

        @self.router.websocket("/ws")
        async def agentWs(websocket: WebSocket, sessionId: str | None = Query(None)):
            try:
                user = await self._getWsUser(websocket)
            except TokenAuthException:
                await websocket.close(code=1008, reason="unauthorized")
                return

            await websocket.accept()
            try:
                await self.gatewayService.handleWebSocket(websocket, user.userId, sessionId)
            except WebSocketDisconnect:
                pass
            except (InvalidParamException, ValidationError) as exc:
                msg = exc.userMessage if isinstance(exc, InvalidParamException) else "Agent 消息格式不正确"
                try:
                    await websocket.send_json({"type": "error", "data": {"message": msg}})
                except Exception:
                    pass
            except Exception:
                try:
                    await websocket.send_json({"type": "error", "data": {"message": "Agent WebSocket 处理失败"}})
                except Exception:
                    pass
            finally:
                self.gatewayService._activeConns.pop(sessionId, None)
