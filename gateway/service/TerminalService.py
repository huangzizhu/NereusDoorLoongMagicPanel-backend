import asyncio
import errno
import fcntl
import os
import pty
import select
import shutil
import signal
import struct
import subprocess
import termios
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from Exception.DataBaseException import DataBaseException
from Exception.InvalidParamException import InvalidParamException
from Exception.TerminalAuthenticationException import TerminalAuthenticationException
from Exception.TerminalEnvironmentUnavailableException import TerminalEnvironmentUnavailableException
from Exception.TerminalProcessException import TerminalProcessException
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.TerminalDaoInterface import TerminalDaoInterface
from gateway.dao.TerminalDaoOrm import TerminalDaoOrm
from pojo.Common import ListResponse
from pojo.Terminal import (
    TerminalAdminLoginResultMessage,
    TerminalErrorMessage,
    TerminalMode,
    TerminalOutputMessage,
    TerminalSessionAdminAuthUpdate,
    TerminalSessionCloseUpdate,
    TerminalSessionLogCreate,
    TerminalStateMessage,
)


AUTH_TIMEOUT_SECONDS = 8
AUTH_PASSWORD_PROMPTS = ("assword", "密码")


@dataclass
class TerminalRuntimeSession:
    sessionId: str
    userId: int
    panelUsername: str
    clientIp: str
    ws: any
    loop: asyncio.AbstractEventLoop
    cols: int
    rows: int
    normalContainerName: str
    idleTimeoutSeconds: int
    adminMaxFailedAttempts: int
    mode: TerminalMode = "normal"
    linuxUser: str = "appuser"
    title: str = "Web Terminal"
    process: Optional[subprocess.Popen] = None
    masterFd: Optional[int] = None
    slaveFd: Optional[int] = None
    generation: int = 0
    switching: bool = False
    closed: bool = False
    lastActiveAt: float = field(default_factory=time.time)
    adminAuthAttempted: bool = False
    adminAuthSucceeded: bool = False
    adminAuthFailedCount: int = 0
    outputEscapeBuffer: str = ""
    idleTask: Optional[asyncio.Task] = None
    lock: threading.RLock = field(default_factory=threading.RLock)


class TerminalService(Singleton):
    @singletonInit
    def __init__(self):
        self.terminalDao: TerminalDaoInterface = TerminalDaoOrm()
        self.sessions: dict[str, TerminalRuntimeSession] = {}
        self.sessionsLock = threading.RLock()

    def _getNormalContainerName(self) -> str:
        return os.getenv("NDLM_TERMINAL_NORMAL_CONTAINER", "app-container")

    def _getNormalLinuxUser(self) -> str:
        return os.getenv("NDLM_TERMINAL_NORMAL_LINUX_USER", "appuser")

    def _getNormalShell(self) -> str:
        return os.getenv("NDLM_TERMINAL_NORMAL_SHELL", "bash")

    def _getIdleTimeoutSeconds(self) -> int:
        raw = os.getenv("NDLM_TERMINAL_IDLE_TIMEOUT_SECONDS", "1800")
        try:
            timeout = int(raw)
        except ValueError:
            timeout = 1800
        return max(timeout, 60)

    def _getAdminMaxFailedAttempts(self) -> int:
        raw = os.getenv("NDLM_TERMINAL_ADMIN_MAX_FAILED_ATTEMPTS", "5")
        try:
            limit = int(raw)
        except ValueError:
            limit = 5
        return max(limit, 1)

    def _touchSession(self, session: TerminalRuntimeSession):
        session.lastActiveAt = time.time()

    def _getSession(self, sessionId: str) -> TerminalRuntimeSession:
        with self.sessionsLock:
            session = self.sessions.get(sessionId)
        if session is None or session.closed:
            raise InvalidParamException(userMessage="终端会话不存在或已关闭")
        return session

    def _safeCloseFd(self, fd: Optional[int]):
        if fd is None:
            return
        try:
            os.close(fd)
        except OSError:
            pass

    def _safeTerminateProcess(self, process: Optional[subprocess.Popen]):
        if process is None or process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=2)
        except Exception:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except Exception:
                pass

    def _setWindowSize(self, fd: int, cols: int, rows: int):
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        try:
            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        except OSError as e:
            raise TerminalProcessException(
                innerMessage=str(e),
                userMessage="设置终端窗口大小失败",
                cause=e,
            )

    def _spawnProcess(self, session: TerminalRuntimeSession, command: list[str], mode: TerminalMode, linuxUser: str, title: str):
        masterFd = None
        slaveFd = None
        process = None
        try:
            masterFd, slaveFd = pty.openpty()
            self._setWindowSize(slaveFd, session.cols, session.rows)
            process = subprocess.Popen(
                command,
                stdin=slaveFd,
                stdout=slaveFd,
                stderr=slaveFd,
                start_new_session=True,
                close_fds=True,
                env=os.environ.copy(),
            )
        except TerminalProcessException:
            self._safeCloseFd(masterFd)
            self._safeCloseFd(slaveFd)
            self._safeTerminateProcess(process)
            raise
        except Exception as e:
            self._safeCloseFd(masterFd)
            self._safeCloseFd(slaveFd)
            self._safeTerminateProcess(process)
            raise TerminalProcessException(
                innerMessage=str(e),
                userMessage="创建终端进程失败",
                cause=e,
            )

        oldMasterFd = session.masterFd
        oldSlaveFd = session.slaveFd
        oldProcess = session.process

        session.masterFd = masterFd
        session.slaveFd = slaveFd
        session.process = process
        session.mode = mode
        session.linuxUser = linuxUser
        session.title = title
        session.generation += 1
        generation = session.generation

        self._startReaderThread(session, generation)
        self._terminateProcess(session, oldProcess, oldMasterFd, oldSlaveFd)

    def _terminateProcess(
            self,
            session: Optional[TerminalRuntimeSession],
            process: Optional[subprocess.Popen],
            masterFd: Optional[int],
            slaveFd: Optional[int],
    ):
        self._safeCloseFd(slaveFd)
        self._safeCloseFd(masterFd)

        if process is not None:
            self._safeTerminateProcess(process)

        if session is not None and session.process is process:
            session.process = None
            session.masterFd = None
            session.slaveFd = None

    def _startReaderThread(self, session: TerminalRuntimeSession, generation: int):
        t = threading.Thread(
            target=self._readerLoop,
            args=(session.sessionId, generation),
            daemon=True,
        )
        t.start()

    def _sanitizeTerminalOutput(self, session: TerminalRuntimeSession, text: str) -> str:
        if not text and not session.outputEscapeBuffer:
            return ""

        combined = session.outputEscapeBuffer + text
        session.outputEscapeBuffer = ""
        sanitizedParts: list[str] = []
        index = 0

        while index < len(combined):
            escIndex = combined.find("\x1b]", index)
            if escIndex < 0:
                sanitizedParts.append(combined[index:])
                break

            sanitizedParts.append(combined[index:escIndex])
            terminatorEsc = combined.find("\x1b\\", escIndex + 2)
            terminatorBel = combined.find("\x07", escIndex + 2)

            if terminatorBel < 0 and terminatorEsc < 0:
                session.outputEscapeBuffer = combined[escIndex:]
                break

            if terminatorBel >= 0 and (terminatorEsc < 0 or terminatorBel < terminatorEsc):
                index = terminatorBel + 1
                continue

            index = terminatorEsc + 2

        return "".join(sanitizedParts)

    def _readerLoop(self, sessionId: str, generation: int):
        while True:
            try:
                session = self._getSession(sessionId)
            except InvalidParamException:
                return

            with session.lock:
                if session.closed or session.generation != generation:
                    return
                masterFd = session.masterFd

            if masterFd is None:
                return

            try:
                readable, _, _ = select.select([masterFd], [], [], 0.5)
                if not readable:
                    continue
                data = os.read(masterFd, 4096)
                if not data:
                    raise TerminalProcessException(userMessage="终端连接已关闭")
                with session.lock:
                    sanitized = self._sanitizeTerminalOutput(session, data.decode(errors="ignore"))
                if not sanitized:
                    continue
                message = TerminalOutputMessage(data=sanitized)
                future = asyncio.run_coroutine_threadsafe(
                    session.ws.send_json(message.model_dump()),
                    session.loop,
                )
                future.result(timeout=5)
            except Exception:
                closeFuture = asyncio.run_coroutine_threadsafe(
                    self.closeSession(
                        sessionId,
                        closeReason="process_exited",
                        shouldCloseWebSocket=True,
                        expectedGeneration=generation,
                    ),
                    session.loop,
                )
                try:
                    closeFuture.result(timeout=5)
                except Exception:
                    pass
                return

    async def _watchIdleTimeout(self, sessionId: str):
        while True:
            await asyncio.sleep(30)
            try:
                session = self._getSession(sessionId)
            except InvalidParamException:
                return
            if session.closed:
                return
            if time.time() - session.lastActiveAt > session.idleTimeoutSeconds:
                await self.closeSession(sessionId, closeReason="idle_timeout", shouldCloseWebSocket=True)
                return

    def _createNormalCommand(self, session: TerminalRuntimeSession) -> list[str]:
        return [
            "docker",
            "exec",
            "-it",
            session.normalContainerName,
            self._getNormalShell(),
        ]

    def assertNormalTerminalAvailable(self):
        containerName = self._getNormalContainerName()
        if shutil.which("docker") is None:
            raise TerminalEnvironmentUnavailableException(userMessage="当前服务器未安装 Docker，普通终端功能不可用")

        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", containerName],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception as e:
            raise TerminalEnvironmentUnavailableException(
                innerMessage=str(e),
                userMessage="普通终端环境检查失败，请稍后重试",
                cause=e,
            )

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            if "No such object" in stderr or "No such container" in stderr:
                raise TerminalEnvironmentUnavailableException(
                    innerMessage=stderr,
                    userMessage=f"普通终端容器 {containerName} 不存在，当前不允许使用终端功能",
                )
            raise TerminalEnvironmentUnavailableException(
                innerMessage=stderr or "unknown error",
                userMessage="Docker 环境不可用，当前不允许使用普通终端",
            )

        if result.stdout.strip().lower() != "true":
            raise TerminalEnvironmentUnavailableException(
                userMessage=f"普通终端容器 {containerName} 未运行，当前不允许使用终端功能"
            )

    def getAvailability(self) -> dict:
        self.assertNormalTerminalAvailable()
        return {
            "normalTerminalAvailable": True,
            "normalContainerName": self._getNormalContainerName(),
        }

    def _createAdminCommand(self, username: str) -> list[str]:
        return [
            "sudo",
            "-u",
            username,
            "-i",
        ]

    def _authenticateLinuxUser(self, username: str, password: str):
        if not username.strip():
            raise InvalidParamException(userMessage="Linux 用户名不能为空")
        if not password:
            raise InvalidParamException(userMessage="Linux 用户密码不能为空")
        if shutil.which("su") is None:
            raise TerminalEnvironmentUnavailableException(userMessage="当前服务器未安装 su，无法进行 Linux 用户认证")

        masterFd = None
        slaveFd = None
        process = None
        outputChunks: list[bytes] = []
        passwordSent = False
        startedAt = time.time()
        ptyClosed = False
        try:
            masterFd, slaveFd = pty.openpty()
            process = subprocess.Popen(
                ["su", "-", username, "-c", "true"],
                stdin=slaveFd,
                stdout=slaveFd,
                stderr=slaveFd,
                start_new_session=True,
                close_fds=True,
                env=os.environ.copy(),
            )
            self._safeCloseFd(slaveFd)
            slaveFd = None

            while True:
                if process.poll() is not None:
                    break
                if time.time() - startedAt > AUTH_TIMEOUT_SECONDS:
                    raise TerminalProcessException(userMessage="Linux 用户认证超时，请稍后重试")

                readable, _, _ = select.select([masterFd], [], [], 0.2)
                if readable:
                    try:
                        chunk = os.read(masterFd, 4096)
                    except OSError as e:
                        if e.errno == errno.EIO:
                            ptyClosed = True
                            break
                        raise
                    if chunk:
                        outputChunks.append(chunk)
                        outputText = b"".join(outputChunks).decode(errors="ignore")
                        if (not passwordSent) and any(prompt in outputText for prompt in AUTH_PASSWORD_PROMPTS):
                            os.write(masterFd, (password + "\n").encode())
                            passwordSent = True
                    else:
                        break
                elif not passwordSent and time.time() - startedAt > 0.5:
                    os.write(masterFd, (password + "\n").encode())
                    passwordSent = True

            if ptyClosed and process.poll() is None:
                process.wait(timeout=2)

            returnCode = process.wait(timeout=1)
            if returnCode == 0:
                return

            outputText = b"".join(outputChunks).decode(errors="ignore").lower()
            if "authentication failure" in outputText or "failure" in outputText:
                raise TerminalAuthenticationException(userMessage="Linux 用户名或密码错误")

            raise TerminalProcessException(
                innerMessage=outputText,
                userMessage="Linux 用户认证执行失败，请稍后重试",
            )
        except (InvalidParamException, TerminalAuthenticationException, TerminalEnvironmentUnavailableException, TerminalProcessException):
            raise
        except Exception as e:
            raise TerminalProcessException(
                innerMessage=str(e),
                userMessage="Linux 用户认证执行失败，请稍后重试",
                cause=e,
            )
        finally:
            self._safeCloseFd(slaveFd)
            self._safeCloseFd(masterFd)
            self._safeTerminateProcess(process)

    def _buildSession(self, userId: int, panelUsername: str, clientIp: str, ws, cols: int, rows: int) -> TerminalRuntimeSession:
        return TerminalRuntimeSession(
            sessionId=uuid.uuid4().hex,
            userId=userId,
            panelUsername=panelUsername,
            clientIp=clientIp,
            ws=ws,
            loop=asyncio.get_running_loop(),
            cols=cols,
            rows=rows,
            normalContainerName=self._getNormalContainerName(),
            idleTimeoutSeconds=self._getIdleTimeoutSeconds(),
            adminMaxFailedAttempts=self._getAdminMaxFailedAttempts(),
            linuxUser=self._getNormalLinuxUser(),
            title=f"{panelUsername}@{self._getNormalContainerName()}",
        )

    def _persistSessionCreate(self, session: TerminalRuntimeSession):
        request = TerminalSessionLogCreate(
            sessionId=session.sessionId,
            userId=session.userId,
            panelUsername=session.panelUsername,
            clientIp=session.clientIp,
            mode=session.mode,
            normalContainerName=session.normalContainerName,
            adminLinuxUsername=None,
            adminAuthAttempted=False,
            adminAuthSucceeded=False,
            adminAuthFailedCount=0,
            startTime=datetime.now(),
            endTime=None,
            closeReason=None,
            exitCode=None,
        )
        try:
            self.terminalDao.insertSession(request)
        except Exception as e:
            raise DataBaseException(innerMessage=str(e), userMessage="创建终端会话失败", cause=e)

    def _persistAdminAuthResult(self, session: TerminalRuntimeSession):
        request = TerminalSessionAdminAuthUpdate(
            sessionId=session.sessionId,
            mode=session.mode,
            adminLinuxUsername=(session.linuxUser if session.mode == "admin" else None),
            adminAuthAttempted=session.adminAuthAttempted,
            adminAuthSucceeded=session.adminAuthSucceeded,
            adminAuthFailedCount=session.adminAuthFailedCount,
        )
        try:
            self.terminalDao.markAdminAuthResult(request)
        except Exception as e:
            raise DataBaseException(innerMessage=str(e), userMessage="保存终端认证结果失败", cause=e)

    async def _sendState(self, session: TerminalRuntimeSession):
        message = TerminalStateMessage(
            sessionId=session.sessionId,
            mode=session.mode,
            linuxUser=session.linuxUser,
            title=session.title,
        )
        await session.ws.send_json(message.model_dump())

    async def _sendError(self, session: TerminalRuntimeSession, code: str, msg: str):
        message = TerminalErrorMessage(code=code, msg=msg)
        await session.ws.send_json(message.model_dump())

    async def openNormalSession(
            self,
            userId: int,
            panelUsername: str,
            clientIp: str,
            ws,
            cols: int,
            rows: int,
    ) -> str:
        session = self._buildSession(userId, panelUsername, clientIp, ws, cols, rows)

        with self.sessionsLock:
            self.sessions[session.sessionId] = session

        try:
            self.assertNormalTerminalAvailable()
            self._persistSessionCreate(session)
            with session.lock:
                self._spawnProcess(
                    session,
                    self._createNormalCommand(session),
                    mode="normal",
                    linuxUser=self._getNormalLinuxUser(),
                    title=f"{panelUsername}@{self._getNormalContainerName()}",
                )
            session.idleTask = asyncio.create_task(self._watchIdleTimeout(session.sessionId))
            await self._sendState(session)
            return session.sessionId
        except (DataBaseException, InvalidParamException, TerminalEnvironmentUnavailableException, TerminalProcessException):
            await self.closeSession(session.sessionId, closeReason="open_failed", shouldCloseWebSocket=False)
            raise

    async def createPendingAdminSession(
            self,
            userId: int,
            panelUsername: str,
            clientIp: str,
            ws,
            cols: int,
            rows: int,
    ) -> str:
        session = self._buildSession(userId, panelUsername, clientIp, ws, cols, rows)
        session.title = f"{panelUsername}@host"

        with self.sessionsLock:
            self.sessions[session.sessionId] = session

        try:
            self._persistSessionCreate(session)
            session.idleTask = asyncio.create_task(self._watchIdleTimeout(session.sessionId))
            return session.sessionId
        except DataBaseException:
            await self.closeSession(session.sessionId, closeReason="open_failed", shouldCloseWebSocket=False)
            raise

    def writeInput(self, sessionId: str, data: str):
        session = self._getSession(sessionId)
        self._touchSession(session)
        with session.lock:
            if session.masterFd is None:
                raise InvalidParamException(userMessage="终端会话未准备完成")
            try:
                os.write(session.masterFd, data.encode())
            except OSError as e:
                raise TerminalProcessException(
                    innerMessage=str(e),
                    userMessage="写入终端失败",
                    cause=e,
                )

    def resize(self, sessionId: str, cols: int, rows: int):
        session = self._getSession(sessionId)
        self._touchSession(session)
        with session.lock:
            session.cols = cols
            session.rows = rows
            if session.masterFd is not None:
                self._setWindowSize(session.masterFd, cols, rows)

    async def upgradeToAdmin(self, sessionId: str, username: str, password: str) -> TerminalAdminLoginResultMessage:
        session = self._getSession(sessionId)
        self._touchSession(session)

        with session.lock:
            if session.mode == "admin":
                return TerminalAdminLoginResultMessage(success=True, mode="admin", msg="当前已经是管理员终端")
            if session.adminAuthFailedCount >= session.adminMaxFailedAttempts:
                return TerminalAdminLoginResultMessage(success=False, mode=session.mode, msg="管理员认证失败次数过多，请重新创建终端")
            session.adminAuthAttempted = True

        try:
            self._authenticateLinuxUser(username, password)
            with session.lock:
                session.switching = True
                self._spawnProcess(
                    session,
                    self._createAdminCommand(username),
                    mode="admin",
                    linuxUser=username,
                    title=f"{username}@host",
                )
                session.adminAuthSucceeded = True
                session.switching = False
            self._persistAdminAuthResult(session)
        except (TerminalAuthenticationException, TerminalEnvironmentUnavailableException, TerminalProcessException, DataBaseException) as e:
            with session.lock:
                session.switching = False
                session.adminAuthFailedCount += 1
            self._persistAdminAuthResult(session)
            return TerminalAdminLoginResultMessage(success=False, mode=session.mode, msg=e.userMessage or "管理员认证失败")

        await self._sendState(session)
        return TerminalAdminLoginResultMessage(success=True, mode="admin", msg="管理员终端创建成功")

    async def closeSession(
            self,
            sessionId: str,
            closeReason: str,
            shouldCloseWebSocket: bool = True,
            expectedGeneration: Optional[int] = None,
    ):
        with self.sessionsLock:
            session = self.sessions.get(sessionId)
            if session is None:
                return
            if session.closed:
                self.sessions.pop(sessionId, None)
                return

        with session.lock:
            if expectedGeneration is not None and session.generation != expectedGeneration:
                return
            if session.closed:
                return
            session.closed = True
            process = session.process
            masterFd = session.masterFd
            slaveFd = session.slaveFd
            session.process = None
            session.masterFd = None
            session.slaveFd = None
            exitCode = process.poll() if process is not None else None

        if session.idleTask is not None:
            session.idleTask.cancel()

        self._terminateProcess(None, process, masterFd, slaveFd)

        try:
            updateRequest = TerminalSessionCloseUpdate(
                sessionId=sessionId,
                mode=session.mode,
                endTime=datetime.now(),
                closeReason=closeReason[:100],
                exitCode=exitCode,
                adminLinuxUsername=(session.linuxUser if session.mode == "admin" else None),
            )
            self.terminalDao.closeSession(updateRequest)
        except Exception:
            pass

        with self.sessionsLock:
            self.sessions.pop(sessionId, None)

        if shouldCloseWebSocket:
            try:
                await session.ws.close()
            except Exception:
                pass

    def getLog(self, request) -> ListResponse:
        try:
            total = self.terminalDao.getTotal()
            items = self.terminalDao.getLog(request.page, request.pageSize)
            return ListResponse(total=total, items=items)
        except Exception as e:
            raise DataBaseException(innerMessage=str(e), userMessage="数据库异常", cause=e)
