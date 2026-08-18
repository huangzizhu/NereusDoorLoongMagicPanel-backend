import json
import logging
from typing import Any

from gateway.Singleton import Singleton, singletonInit
from gateway.dao.ToolAuthorizationDaoOrm import ToolAuthorizationDaoOrm
from gateway.orm.ToolAuthorizationOrm import (
    AUTH_REQ_SOURCE_MANUAL,
    AUTH_REQ_STATUS_APPROVED,
    AUTH_REQ_STATUS_EXPIRED,
    AUTH_REQ_STATUS_PENDING,
    AUTH_REQ_STATUS_REJECTED,
)

_logger = logging.getLogger(__name__)

# 命令执行类工具：授权时额外匹配命令白名单
_COMMAND_TOOLS = {"runCommand", "runShellCommand"}

# 复用特权码的默认参数
# 无人值守审批码默认 7 小时（管理员可能隔天登录审批）；
# 实际值由 agent 从任务/巡检策略的 ttlSeconds 继承（见 agent_loop）
_DEFAULT_TTL_SECONDS = 25200
_DEFAULT_MAX_RUNS = 100


class ToolAuthorizationService(Singleton):
    """工具授权请求闭环：提交 → CLI 审批 → 写回策略。

    - 提交：Agent 在预授权未覆盖时调用，生成一次性审批码（复用 ElevationService
      的 code 生命周期，request_type="tool_authorization"），请求落库 pending。
    - 审批：管理员 `sudo nereus approve <CODE>`（或 /admin/elevation/approve），
      ElevationService 签发 JIT token；本服务把授权片段写回来源策略
      （定时任务 approvalPolicy / 巡检策略），后续运行自动放行。
    - 拒绝：请求标记 rejected，Agent 下次运行可换方案。
    """

    @singletonInit
    def __init__(self):
        self.dao = ToolAuthorizationDaoOrm()

    # ── 提交 ──

    def submitRequest(
        self,
        *,
        sessionId: str,
        toolName: str,
        args: dict | None = None,
        paths: list[str] | None = None,
        commandLine: str | None = None,
        reason: str | None = None,
        policyReason: str | None = None,
        riskLevel: str | None = None,
        sourceType: str = AUTH_REQ_SOURCE_MANUAL,
        taskId: int | None = None,
        ttlSeconds: int = _DEFAULT_TTL_SECONDS,
        maxRuns: int = _DEFAULT_MAX_RUNS,
    ) -> tuple[str, bool]:
        """提交授权请求。返回 (code, created)；同 session 同工具同命令的
        pending 请求复用已有 code，避免重复审批。"""
        existing = self.dao.findPendingBySessionAndTool(
            sessionId, toolName, commandLine
        )
        if existing is not None:
            return existing.code, False

        from gateway.service.elevation_service import ElevationService

        commands: list[dict[str, Any]] = []
        inline_cmd: str | None = None
        # 命令执行类工具：命令文本走 inline_cmd 通道（CLI 展示 + AI-SAST 审计），
        # 同时放入 commands 的 exec_arbitrary_cmd 条目，使审批后签发的 token
        # 可被 runPrivileged(token_id, command_index=0, args=[命令], session_id)
        # 消费——支持同 session 内"审批后补执行"（Channel 1 走 cmd_hash 校验）。
        if toolName == "runShellCommand" and commandLine:
            inline_cmd = commandLine
            commands = [{"command": "exec_arbitrary_cmd", "args": [commandLine]}]
        elif toolName == "runCommand" and commandLine:
            inline_cmd = commandLine
            commands = [{"command": "exec_arbitrary_cmd", "args": [commandLine]}]

        entry = ElevationService().generate_code(
            session_id=sessionId,
            commands=commands,
            reason=reason or f"工具授权请求: {toolName}",
            ttl_seconds=ttlSeconds,
            max_ops=maxRuns,
            inline_cmd=inline_cmd,
            inline_cmd_hash=(
                None if inline_cmd is None else self._hashCmd(inline_cmd)
            ),
            request_type="tool_authorization",
            task_id=taskId,
            expire_previous=False,
        )
        self.dao.createRequest(
            code=entry.code,
            sessionId=sessionId,
            sourceType=sourceType,
            taskId=taskId,
            toolName=toolName,
            args=args,
            paths=paths,
            commandLine=commandLine,
            reason=reason,
            policyReason=policyReason,
            riskLevel=riskLevel,
            ttlSeconds=ttlSeconds,
            maxRuns=maxRuns,
        )
        _logger.info(
            "工具授权请求已提交: code=%s session=%s tool=%s source=%s task=%s cmd=%s",
            entry.code, sessionId, toolName, sourceType, taskId,
            (commandLine or "")[:80],
        )
        return entry.code, True

    @staticmethod
    def _hashCmd(text: str) -> str:
        """与特权通道一致的 cmd hash（create_signed_request 校验用）。"""
        from privileged_agent.crypto import hash_payload

        return hash_payload({"cmd": text})

    # ── 审批 ──

    def approve(
        self,
        code: str,
        approved_by: str,
        token_id: str,
        path_prefix: str | None = None,
    ) -> bool:
        """审批通过：更新请求状态，并把授权写回来源策略。

        path_prefix: 管理员指定的允许路径前缀（覆盖请求原路径，写回
        allowedPaths 用前缀匹配，支持该前缀下任意子路径）。
        """
        request = self.dao.findByCode(code)
        if request is None:
            return False
        if request.status != AUTH_REQ_STATUS_PENDING:
            _logger.warning(
                "授权请求 %s 状态不是 pending（当前 %s），拒绝写回",
                code, request.status,
            )
            return False

        grant = self._buildGrant(request)
        if path_prefix:
            grant["paths"] = [path_prefix]
        source_type, task_id = self._resolveSource(request.sessionId)

        if source_type == "scheduled" and task_id is not None:
            self._grantToScheduledTask(task_id, grant)
        elif source_type == "inspection":
            self._grantToInspectionPolicy(grant)
        else:
            _logger.info(
                "授权请求 %s 无法关联持久化策略（source=%s），仅本次 JIT token 生效",
                code, source_type,
            )

        ok = self.dao.updateStatus(
            code,
            AUTH_REQ_STATUS_APPROVED,
            approvedBy=approved_by,
            tokenId=token_id,
            grant=grant,
        )
        _logger.info(
            "工具授权请求已批准: code=%s by=%s tool=%s grant=%s",
            code, approved_by, request.toolName,
            json.dumps(grant, ensure_ascii=False)[:200],
        )
        return ok

    def reject(self, code: str, reason: str) -> bool:
        request = self.dao.findByCode(code)
        if request is None:
            return False
        ok = self.dao.updateStatus(
            code, AUTH_REQ_STATUS_REJECTED, rejectReason=reason
        )
        _logger.info(
            "工具授权请求已拒绝: code=%s tool=%s reason=%s",
            code, request.toolName, reason[:100],
        )
        return ok

    def expire(self, code: str) -> bool:
        """把 pending 记录标记为过期（幂等；非 pending 状态不覆盖）。"""
        request = self.dao.findByCode(code)
        if request is None or request.status != AUTH_REQ_STATUS_PENDING:
            return False
        return self.dao.updateStatus(code, AUTH_REQ_STATUS_EXPIRED)

    # ── 授权片段构建与写回 ──

    @staticmethod
    def _buildGrant(request) -> dict[str, Any]:
        """把请求转成可合并进 approvalPolicy 的授权片段。"""
        grant: dict[str, Any] = {"toolName": request.toolName}
        paths = request.paths or []
        if paths:
            grant["paths"] = list(dict.fromkeys(paths))
        if request.commandLine:
            grant["commandLine"] = request.commandLine
        return grant

    def _grantToScheduledTask(self, taskId: int, grant: dict[str, Any]) -> bool:
        from gateway.dao.ScheduledTaskDaoOrm import ScheduledTaskDaoOrm

        dao = ScheduledTaskDaoOrm()
        task = dao.getTask(taskId)
        if task is None or task.status == "deleted":
            _logger.warning("授权写回失败：定时任务 %s 不存在", taskId)
            return False
        policy = dict(task.approvalPolicy or {})
        merged = self._mergeGrant(policy, grant)
        dao.updateTask(taskId, {"approvalPolicy": merged}, userId=None)
        _logger.info("授权已写回定时任务策略: task=%s", taskId)
        return True

    def _grantToInspectionPolicy(self, grant: dict[str, Any]) -> bool:
        from gateway.service.InspectionService import InspectionService

        service = InspectionService()
        with service._policy_lock:
            policy = service.loadInspectionPolicy()
            merged = self._mergeGrant(policy, grant)
            service.saveInspectionPolicy(merged)
        _logger.info("授权已写回巡检策略")
        return True

    @staticmethod
    def _mergeGrant(policy: dict, grant: dict[str, Any]) -> dict:
        """把授权片段合并进现有 approvalPolicy（去重、保留其它字段）。"""
        merged = dict(policy or {})

        allowed_tools = [str(x) for x in merged.get("allowedTools") or []]
        tool = grant.get("toolName")
        if tool and tool not in allowed_tools:
            allowed_tools.append(tool)
        merged["allowedTools"] = allowed_tools

        for path in grant.get("paths") or []:
            paths = [str(x) for x in merged.get("allowedPaths") or []]
            if path not in paths:
                paths.append(path)
            merged["allowedPaths"] = paths

        command_line = grant.get("commandLine")
        if command_line:
            commands = [str(x) for x in merged.get("allowedCommands") or []]
            if command_line not in commands:
                commands.append(command_line)
            merged["allowedCommands"] = commands

        return merged

    def _resolveSource(self, sessionId: str) -> tuple[str, int | None]:
        """通过 sessionId 反查请求来源：定时任务 / 巡检 / 手动会话。"""
        try:
            from gateway.dao.ScheduledTaskDaoOrm import ScheduledTaskDaoOrm

            run = ScheduledTaskDaoOrm().findRunBySessionId(sessionId)
            if run is not None and run.taskId is not None:
                return "scheduled", int(run.taskId)
        except Exception:
            _logger.exception("反查 session=%s 的定时任务失败", sessionId)
        try:
            from gateway.dao.InspectionReportDaoOrm import InspectionReportDaoOrm

            report = InspectionReportDaoOrm().findBySessionId(sessionId)
            if report is not None:
                return "inspection", None
        except Exception:
            _logger.exception("反查 session=%s 的巡检报告失败", sessionId)
        return AUTH_REQ_SOURCE_MANUAL, None

    # ── 查询 ──

    def listPending(self, limit: int = 100) -> list[dict[str, Any]]:
        from datetime import datetime

        rows = self.dao.listRequests(status="pending", limit=limit)
        now = datetime.now()
        # 惰性过期：超 TTL 的 pending 记录标记 expired（进程重启后同样适用）
        for row in rows:
            if row.createdAt is not None:
                age = (now - row.createdAt).total_seconds()
                if age > (row.ttlSeconds or 3600):
                    self.dao.updateStatus(row.code, "expired")
        rows = self.dao.listRequests(status="pending", limit=limit)
        return [self._toDict(r) for r in rows]

    def getRequestDetail(self, code: str) -> dict[str, Any] | None:
        """查询授权请求详情（CLI 审批展示用）。"""
        request = self.dao.findByCode(code)
        if request is None:
            return None
        data = self._toDict(request)
        data.update({
            "status": request.status,
            "createdAt": (
                request.createdAt.isoformat() if request.createdAt else None
            ),
            "approvedBy": request.approvedBy,
            "rejectReason": request.rejectReason,
        })
        return data

    def listApprovedGrants(
        self,
        sessionId: str | None = None,
        taskId: int | None = None,
        sourceType: str | None = None,
    ) -> list[dict[str, Any]]:
        """已批准的授权片段（运行时动态白名单，供 agent_loop 使用）。

        过滤维度见 ToolAuthorizationDaoOrm.listApproved；未传任何过滤条件时
        返回全部已批准授权（慎用）。
        """
        rows = self.dao.listApproved(
            sessionId=sessionId,
            taskId=taskId,
            sourceType=sourceType,
        )
        return [
            {
                "toolName": r.toolName,
                "paths": r.grant.get("paths") if isinstance(r.grant, dict) else None,
                "commandLine": r.grant.get("commandLine") if isinstance(r.grant, dict) else None,
            }
            for r in rows
            if r.grant is not None
        ]

    @staticmethod
    def _toDict(request) -> dict[str, Any]:
        return {
            "id": request.id,
            "code": request.code,
            "sessionId": request.sessionId,
            "sourceType": request.sourceType,
            "taskId": request.taskId,
            "toolName": request.toolName,
            "args": request.args,
            "paths": request.paths,
            "commandLine": request.commandLine,
            "reason": request.reason,
            "policyReason": request.policyReason,
            "riskLevel": request.riskLevel,
            "status": request.status,
            "ttlSeconds": request.ttlSeconds,
            "maxRuns": request.maxRuns,
            "createdAt": (
                request.createdAt.isoformat() if request.createdAt else None
            ),
        }
