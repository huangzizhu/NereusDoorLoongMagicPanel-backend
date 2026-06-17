"""Admin Controller — 供 CLI (sudo nereus) 调用的特权审批 API。

所有端点仅限 localhost 访问（通过 host 检查），
并用 /etc/nereus/admin_token 做 Bearer token 鉴权。
"""

import os
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from gateway.controller.AbstractController import AbstractController
from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.service.elevation_service import ElevationService
logger = logging.getLogger("admin_controller")

# token 路径可通过环境变量 NDLM_ADMIN_TOKEN_PATH 覆盖
# 在 .env 中:  NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token
# 在 systemd:  Environment=NDLM_ADMIN_TOKEN_PATH=/custom/path/admin_token
ADMIN_TOKEN_PATH = os.getenv("NDLM_ADMIN_TOKEN_PATH", "/etc/nereus/admin_token")


def verify_admin_token(request: Request) -> None:
    """验证 admin token。

    token 文件位于 /etc/nereus/admin_token，权限 400 root:root。
    CLI (sudo nereus) 读取此文件后以 Bearer token 形式发送。
    """
    # 仅允许 localhost 访问
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="仅允许本地访问")

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少 Authorization: Bearer <token>")

    token = auth.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token 为空")

    # 从文件读取期望的 token（文件只有 root 能读）
    try:
        expected = Path(ADMIN_TOKEN_PATH).read_text(encoding="utf-8").strip()
    except (FileNotFoundError, PermissionError):
        logger.warning("admin_token 文件不可读: %s", ADMIN_TOKEN_PATH)
        raise HTTPException(status_code=500, detail="服务器配置错误：admin_token 不可用")

    if token != expected:
        raise HTTPException(status_code=403, detail="Token 不匹配")


class AdminController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(
            prefix="/admin/elevation",
            tags=["管理员特权审批"],
            dependencies=[Depends(verify_admin_token)],
        )
        self.elevation_service = ElevationService()
        super().__init__("adminController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.get("/codes/{code}")
        def get_code(code: str) -> ResponseModel:
            """查询一个特权码的信息（给 CLI 展示用）。"""
            entry = self.elevation_service.get_code(code)
            if entry is None:
                return Response.error(msg="特权码不存在")
            return Response.success(data=entry.to_dict())

        @self.router.get("/pending")
        def list_pending() -> ResponseModel:
            """列出所有待审批的 code。"""
            pending = self.elevation_service.list_pending()
            return Response.success(data=pending)

        @self.router.post("/approve")
        def approve_code(body: dict) -> ResponseModel:
            """批准一个 pending 的 code。

            Body: {"code": "NGA7-K3X9", "approved_by": "admin"}
            """
            code = body.get("code", "").strip()
            approved_by = body.get("approved_by", "admin")

            if not code:
                return Response.error(msg="缺少 code")

            token = self.elevation_service.approve_code(code, approved_by)
            if token is None:
                return Response.error(msg="批准失败：code 不存在或状态不是 pending")

            # 推送 WS 事件通知前端（同步函数中通过 get_event_loop 获取 loop）
            import asyncio
            from gateway.service.AgentGatewayService import AgentGatewayService
            gw = AgentGatewayService()
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(gw.pushElevationEvent(
                        token.session_id, "elevation.resolved", {
                            "status": "approved",
                            "code": code,
                            "token_id": token.token_id,
                            "message": "管理员已批准特权请求，Agent 可继续执行",
                        }
                    ))
            except RuntimeError:
                pass  # 没有 event loop 时静默跳过 WS 推送

            return Response.success(data={
                "status": "approved",
                "code": code,
                "token_id": token.token_id,
                "max_ops": token.max_ops,
                "allowed_commands": token.allowed_commands,
            })

        @self.router.post("/reject")
        def reject_code(body: dict) -> ResponseModel:
            """拒绝一个 pending 的 code。

            Body: {"code": "NGA7-K3X9", "reason": "操作风险过高"}
            """
            code = body.get("code", "").strip()
            reason = body.get("reason", "管理员拒绝")

            if not code:
                return Response.error(msg="缺少 code")

            self.elevation_service.reject_code(code, reason)
            return Response.success(data={"status": "rejected", "code": code})

        @self.router.post("/revoke")
        def revoke_token(body: dict) -> ResponseModel:
            """吊销一个已签发的 token。

            Body: {"token_id": "..."}
            """
            token_id = body.get("token_id", "").strip()
            if not token_id:
                return Response.error(msg="缺少 token_id")

            ok = self.elevation_service.revoke_token(token_id)
            if not ok:
                return Response.error(msg="token 不存在或已过期")

            return Response.success(data={"status": "revoked", "token_id": token_id})

        @self.router.get("/history")
        def list_history(limit: int = 50) -> ResponseModel:
            """查询审批历史。"""
            history = self.elevation_service.list_history(limit=limit)
            return Response.success(data=history)
