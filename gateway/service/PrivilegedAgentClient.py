import os
import socket
import uuid

from privileged_agent.models import (
    PrivilegedAction,
    PrivilegedRequest,
    PrivilegedRequestContext,
    PrivilegedResponse,
)


class PrivilegedAgentRemoteError(Exception):
    def __init__(self, code: str, message: str, details: str | None = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class PrivilegedAgentClient:
    def __init__(self):
        self.socket_path = os.getenv(
            "NDLM_PRIVILEGED_AGENT_SOCKET",
            "/run/ndlmpanel/privileged-agent.sock",
        )
        self.timeout_seconds = float(os.getenv("NDLM_PRIVILEGED_AGENT_TIMEOUT_SECONDS", "5"))

    def defaultContext(self, source: str) -> PrivilegedRequestContext:
        return PrivilegedRequestContext(source=source)

    def call(
        self,
        action: PrivilegedAction | str,
        payload: dict,
        context: PrivilegedRequestContext,
    ):
        request = PrivilegedRequest(
            requestId=str(uuid.uuid4()),
            action=action.value if isinstance(action, PrivilegedAction) else str(action),
            payload=payload,
            caller=context,
        )
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(self.timeout_seconds)
                client.connect(self.socket_path)
                client.sendall((request.model_dump_json() + "\n").encode("utf-8"))
                raw = b""
                while not raw.endswith(b"\n"):
                    chunk = client.recv(65536)
                    if not chunk:
                        break
                    raw += chunk
        except FileNotFoundError as exc:
            raise PrivilegedAgentRemoteError("PROXY_UNAVAILABLE", "特权代理未启动", str(exc)) from exc
        except PermissionError as exc:
            raise PrivilegedAgentRemoteError("PROXY_PERMISSION_DENIED", "无权访问特权代理", str(exc)) from exc
        except socket.timeout as exc:
            raise PrivilegedAgentRemoteError("PROXY_TIMEOUT", "特权代理响应超时", str(exc)) from exc
        except OSError as exc:
            raise PrivilegedAgentRemoteError("PROXY_UNAVAILABLE", "无法连接特权代理", str(exc)) from exc

        if not raw:
            raise PrivilegedAgentRemoteError("PROXY_PROTOCOL_ERROR", "特权代理返回空响应")

        try:
            response = PrivilegedResponse.model_validate_json(raw.decode("utf-8"))
        except Exception as exc:
            raise PrivilegedAgentRemoteError("PROXY_PROTOCOL_ERROR", "特权代理响应格式非法", str(exc)) from exc

        if not response.success:
            raise PrivilegedAgentRemoteError(
                response.errorCode or "PROXY_ERROR",
                response.errorMessage or "特权代理执行失败",
                response.errorDetails,
            )
        return response.data
