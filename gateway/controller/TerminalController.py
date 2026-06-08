from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from Exception.InvalidParamException import InvalidParamException
from Exception.TokenAuthException import TokenAuthException
from Exception.GatewayAbstractException import GatewayAbstractException
from Exception.TerminalEnvironmentUnavailableException import TerminalEnvironmentUnavailableException
from gateway.Response import Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.dao.UserDaoOrm import UserDaoOrm
from gateway.orm.UserOrm import UserOrm
from gateway.service.TerminalService import TerminalService
from pojo.Terminal import TerminalAdminLoginMessage, TerminalInputMessage, TerminalLogSearchRequest, \
    TerminalResizeMessage
from utils.JWTTokenTool import getUserId


class TerminalController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/terminal", tags=["终端"])
        self.terminalService: TerminalService = TerminalService()
        self.userDao: UserDaoInterface = UserDaoOrm()
        super().__init__("terminalController", self.router)
        self.routerSetup()

    async def _getCurrentUser(self, websocket: WebSocket) -> UserOrm:
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

    async def _sendWsError(self, websocket: WebSocket, code: str, msg: str):
        await websocket.send_json({
            "type": "error",
            "code": code,
            "msg": msg,
        })

    async def _handleNormalSessionMessages(self, websocket: WebSocket, sessionId: str):
        while True:
            payload = await websocket.receive_json()
            messageType = payload.get("type")
            if messageType == "input":
                message = TerminalInputMessage.model_validate(payload)
                self.terminalService.writeInput(sessionId, message.data)
            elif messageType == "resize":
                message = TerminalResizeMessage.model_validate(payload)
                self.terminalService.resize(sessionId, message.cols, message.rows)
            elif messageType == "admin_login":
                message = TerminalAdminLoginMessage.model_validate(payload)
                result = await self.terminalService.upgradeToAdmin(sessionId, message.username, message.password)
                await websocket.send_json(result.model_dump())
            else:
                raise InvalidParamException(userMessage=f"不支持的终端消息类型: {messageType}")

    async def _handleAdminSessionMessages(self, websocket: WebSocket, sessionId: str):
        authenticated = False
        while True:
            payload = await websocket.receive_json()
            messageType = payload.get("type")

            if not authenticated:
                if messageType != "admin_login":
                    raise InvalidParamException(userMessage="管理员直连首条消息必须为admin_login")
                message = TerminalAdminLoginMessage.model_validate(payload)
                result = await self.terminalService.upgradeToAdmin(sessionId, message.username, message.password)
                await websocket.send_json(result.model_dump())
                authenticated = result.success
                continue

            if messageType == "input":
                message = TerminalInputMessage.model_validate(payload)
                self.terminalService.writeInput(sessionId, message.data)
            elif messageType == "resize":
                message = TerminalResizeMessage.model_validate(payload)
                self.terminalService.resize(sessionId, message.cols, message.rows)
            elif messageType == "admin_login":
                message = TerminalAdminLoginMessage.model_validate(payload)
                result = await self.terminalService.upgradeToAdmin(sessionId, message.username, message.password)
                await websocket.send_json(result.model_dump())
            else:
                raise InvalidParamException(userMessage=f"不支持的终端消息类型: {messageType}")

    def routerSetup(self):
        @self.router.get("/available")
        def getTerminalAvailability():
            res = self.terminalService.getAvailability()
            return Response.success(res)

        @self.router.websocket("/ws")
        async def terminalWs(
                websocket: WebSocket,
                cols: int = Query(120, ge=1, le=500),
                rows: int = Query(30, ge=1, le=500),
        ):
            try:
                user = await self._getCurrentUser(websocket)
                self.terminalService.assertNormalTerminalAvailable()
            except TokenAuthException:
                await websocket.close(code=1008, reason="unauthorized")
                return
            except TerminalEnvironmentUnavailableException:
                await websocket.close(code=1008, reason="terminal_unavailable")
                return

            await websocket.accept()
            sessionId = None
            clientIp = websocket.client.host if websocket.client and websocket.client.host else "unknown"

            try:
                sessionId = await self.terminalService.openNormalSession(
                    userId=user.userId,
                    panelUsername=user.username,
                    clientIp=clientIp,
                    ws=websocket,
                    cols=cols,
                    rows=rows,
                )
                await self._handleNormalSessionMessages(websocket, sessionId)
            except WebSocketDisconnect:
                pass
            except (InvalidParamException, ValidationError) as e:
                msg = e.userMessage if isinstance(e, InvalidParamException) else "终端消息格式不正确"
                await self._sendWsError(websocket, "invalid_message", msg)
            except GatewayAbstractException as e:
                await self._sendWsError(websocket, "terminal_error", e.userMessage or "终端操作失败")
            except Exception:
                try:
                    await self._sendWsError(websocket, "terminal_error", "终端操作失败，请稍后重试")
                except Exception:
                    pass
            finally:
                if sessionId is not None:
                    await self.terminalService.closeSession(sessionId, closeReason="client_disconnect", shouldCloseWebSocket=False)

        @self.router.websocket("/admin/ws")
        async def adminTerminalWs(
                websocket: WebSocket,
                cols: int = Query(120, ge=1, le=500),
                rows: int = Query(30, ge=1, le=500),
        ):
            try:
                user = await self._getCurrentUser(websocket)
            except TokenAuthException:
                await websocket.close(code=1008, reason="unauthorized")
                return

            await websocket.accept()
            sessionId = None
            clientIp = websocket.client.host if websocket.client and websocket.client.host else "unknown"

            try:
                sessionId = await self.terminalService.createPendingAdminSession(
                    userId=user.userId,
                    panelUsername=user.username,
                    clientIp=clientIp,
                    ws=websocket,
                    cols=cols,
                    rows=rows,
                )
                await self._handleAdminSessionMessages(websocket, sessionId)
            except WebSocketDisconnect:
                pass
            except (InvalidParamException, ValidationError) as e:
                msg = e.userMessage if isinstance(e, InvalidParamException) else "终端消息格式不正确"
                await self._sendWsError(websocket, "invalid_message", msg)
            except GatewayAbstractException as e:
                await self._sendWsError(websocket, "terminal_error", e.userMessage or "终端操作失败")
            except Exception:
                try:
                    await self._sendWsError(websocket, "terminal_error", "终端操作失败，请稍后重试")
                except Exception:
                    pass
            finally:
                if sessionId is not None:
                    await self.terminalService.closeSession(sessionId, closeReason="client_disconnect", shouldCloseWebSocket=False)

        @self.router.post("/session/log")
        def getTerminalSessionLog(request: TerminalLogSearchRequest):
            res = self.terminalService.getLog(request)
            return Response.success(res)
