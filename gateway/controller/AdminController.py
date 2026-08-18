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
from gateway.service.audit_service import audit_commands, audit_script_content
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

        @self.router.get("/authorization/{code}")
        def get_authorization(code: str) -> ResponseModel:
            """查询工具授权请求详情（给 CLI 审批展示用）。"""
            from gateway.service.ToolAuthorizationService import ToolAuthorizationService
            detail = ToolAuthorizationService().getRequestDetail(code)
            if detail is None:
                return Response.error(msg="工具授权请求不存在")
            return Response.success(data=detail)

        @self.router.get("/pending")
        def list_pending() -> ResponseModel:
            """列出所有待审批的 code。"""
            pending = self.elevation_service.list_pending()
            return Response.success(data=pending)

        @self.router.post("/approve")
        async def approve_code(body: dict) -> ResponseModel:
            """批准一个 pending 的 code。

            Body: {"code": "NGA7-K3X9", "approved_by": "admin"}
            """
            code = body.get("code", "").strip()
            approved_by = body.get("approved_by", "admin")

            if not code:
                return Response.error(msg="缺少 code")

            entry = self.elevation_service.get_code(code)
            token = self.elevation_service.approve_code(code, approved_by)
            if token is None:
                # 同步 DB 状态：工具授权请求的 code 过期/丢失时，
                # 把库内 pending 记录标记 expired（仅 pending 生效），
                # 避免残留记录与审计歧义
                from gateway.service.ToolAuthorizationService import ToolAuthorizationService
                ToolAuthorizationService().expire(code)
                return Response.error(msg="批准失败：code 不存在、已过期或状态不是 pending")

            request_type = getattr(entry, "request_type", "privileged") if entry else "privileged"
            task_id = getattr(entry, "task_id", None) if entry else None
            if request_type == "scheduled_task_policy" and task_id is not None:
                from gateway.service.ScheduledTaskService import ScheduledTaskService
                ok = ScheduledTaskService().approveScheduledTaskPolicy(
                    int(task_id),
                    approved_by,
                    token.token_id,
                )
                if not ok:
                    return Response.error(msg="批准失败：定时任务不存在或状态不是 pending_approval")
            elif request_type == "tool_authorization":
                from gateway.service.ToolAuthorizationService import ToolAuthorizationService
                ok = ToolAuthorizationService().approve(
                    code,
                    approved_by,
                    token.token_id,
                    path_prefix=body.get("path_prefix"),
                )
                if not ok:
                    # 写回失败时吊销刚签发的 token，避免"报错但特权通道已放开"
                    self.elevation_service.revoke_token(token.token_id)
                    return Response.error(msg="批准失败：工具授权请求不存在")

            # 推送 WS 事件通知前端（async handler 可直接 await）
            from gateway.service.AgentGatewayService import AgentGatewayService
            gw = AgentGatewayService()
            await gw.pushElevationEvent(
                token.session_id, "elevation.resolved", {
                    "status": "approved",
                    "request_type": request_type,
                    "taskId": task_id,
                    "code": code,
                    "token_id": token.token_id,
                    "message": "管理员已批准特权请求，Agent 可继续执行",
                }
            )

            return Response.success(data={
                "status": "approved",
                "request_type": request_type,
                "code": code,
                "token_id": token.token_id,
                "session_id": token.session_id,
                "taskId": task_id,
                "max_ops": token.max_ops,
                "allowed_commands": token.allowed_commands,
            })

        @self.router.post("/reject")
        async def reject_code(body: dict) -> ResponseModel:
            """拒绝一个 pending 的 code。

            Body: {"code": "NGA7-K3X9", "reason": "操作风险过高"}
            """
            code = body.get("code", "").strip()
            reason = body.get("reason", "管理员拒绝")

            if not code:
                return Response.error(msg="缺少 code")

            entry = self.elevation_service.get_code(code)
            if entry:
                self.elevation_service.reject_code(code, reason)
                request_type = getattr(entry, "request_type", "privileged")
                task_id = getattr(entry, "task_id", None)
                if request_type == "scheduled_task_policy" and task_id is not None:
                    from gateway.service.ScheduledTaskService import ScheduledTaskService
                    ScheduledTaskService().rejectScheduledTaskPolicy(int(task_id), reason)
                elif request_type == "tool_authorization":
                    from gateway.service.ToolAuthorizationService import ToolAuthorizationService
                    ToolAuthorizationService().reject(code, reason)
                # 推送 WS 事件通知前端
                from gateway.service.AgentGatewayService import AgentGatewayService
                gw = AgentGatewayService()
                await gw.pushElevationEvent(
                    entry.session_id, "elevation.resolved", {
                        "status": "rejected",
                        "request_type": request_type,
                        "taskId": task_id,
                        "code": code,
                        "reason": reason,
                        "message": "管理员已拒绝特权请求",
                    }
                )

            return Response.success(data={
                "status": "rejected",
                "code": code,
                "request_type": getattr(entry, "request_type", "privileged") if entry else None,
                "taskId": getattr(entry, "task_id", None) if entry else None,
            })

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

        @self.router.get("/audit/{code}")
        def audit_code(code: str) -> ResponseModel:
            """AI 安全审计一个待审批的 code 中的命令/脚本。

            返回结构化审计报告，CLI 用 rich Markdown 渲染。
            """
            print(f"[AUDIT_DEBUG] /audit/{code} 被调用", flush=True)
            entry = self.elevation_service.get_code(code)
            if entry is None:
                print(f"[AUDIT_DEBUG] code={code} 不存在", flush=True)
                return Response.error(msg="特权码不存在")
            if entry.status != "pending":
                return Response.error(msg=f"code 状态不是 pending (当前: {entry.status})")

            commands = entry.commands
            script_content = None

            if getattr(entry, "request_type", "privileged") == "scheduled_task_policy":
                return Response.success(data={
                    "code": code,
                    "audit": {
                        "risk_level": "MEDIUM",
                        "summary": "定时任务预授权策略，请人工核对允许工具和目录范围",
                        "findings": [],
                        "dangerous_commands": [],
                        "network_requests": False,
                        "nested_execution": False,
                        "ai_advice": "确认 allowedTools、allowedPaths、deniedPaths 是否符合最小权限原则",
                    },
                })

            # 检测脚本通道（script_path 指定了脚本文件）
            if entry.script_path:
                script_path_obj = Path(entry.script_path)
                if script_path_obj.exists():
                    try:
                        script_content = script_path_obj.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        pass

            # 执行审计
            print(f"[AUDIT_DEBUG] 开始审计: script_content={bool(script_content)} commands={len(commands)}条", flush=True)
            try:
                if script_content:
                    audit = audit_script_content(script_content, entry.script_path or "")
                else:
                    audit = audit_commands(commands)
                print(f"[AUDIT_DEBUG] 审计完成: risk_level={audit.get('risk_level')} ai_advice={audit.get('ai_advice','')[:30]}", flush=True)
            except Exception as exc:
                logger.exception("AI-SAST 审计异常")
                audit = {
                    "risk_level": "MEDIUM",
                    "summary": "AI 审计执行异常，已降级为规则扫描",
                    "findings": [{"severity": "warning", "description": f"审计异常: {exc}", "code_snippet": "", "recommendation": "请人工审核"}],
                    "dangerous_commands": [],
                    "network_requests": False,
                    "nested_execution": False,
                    "ai_advice": "审计异常，请人工审核",
                }

            return Response.success(data={
                "code": code,
                "audit": audit,
            })

        @self.router.get("/history")
        def list_history(limit: int = 50) -> ResponseModel:
            """查询审批历史。"""
            history = self.elevation_service.list_history(limit=limit)
            return Response.success(data=history)
