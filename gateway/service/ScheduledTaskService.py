from __future__ import annotations

from datetime import datetime

from Exception.DataBaseException import DataBaseException
from Exception.InvalidParamException import InvalidParamException
from agent.prompt_loader import loadPrompt
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.ScheduledTaskDaoOrm import ScheduledTaskDaoOrm
from pojo.Common import ListResponse
from pojo.ScheduledTask import (
    ScheduledTaskCreate,
    ScheduledTaskResponse,
    ScheduledTaskRunResponse,
    ScheduledTaskUpdate,
)


# 无人值守机制提示词：注入定时任务 agent，约束其行为（管理员不在线）。
UNATTENDED_TASK_GUIDANCE: str = loadPrompt(
    "automation/scheduled_task_guidance.txt"
)


TASK_STATUS_ACTIVE = "active"
TASK_STATUS_PAUSED = "paused"
TASK_STATUS_DELETED = "deleted"
TASK_STATUS_PENDING_APPROVAL = "pending_approval"

APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_REJECTED = "rejected"


class ScheduledTaskService(Singleton):
    @singletonInit
    def __init__(self):
        self.dao = ScheduledTaskDaoOrm()

    def createTask(self, userId: int, body: ScheduledTaskCreate) -> ScheduledTaskResponse:
        self._validateCron(body.cronExpression)
        try:
            requires_approval = body.approvalPolicy is not None
            task = self.dao.createTask(
                userId,
                body,
                status=TASK_STATUS_PENDING_APPROVAL if requires_approval else TASK_STATUS_ACTIVE,
                approvalStatus=APPROVAL_STATUS_PENDING if requires_approval else None,
            )
            if requires_approval:
                task = self._issueApprovalCode(task.id, userId)
            else:
                self._refreshScheduler(task)
            return ScheduledTaskResponse.model_validate(task)
        except Exception as exc:
            raise DataBaseException(userMessage="创建定时任务失败", innerMessage=str(exc), cause=exc)

    def updateTask(
        self, taskId: int, userId: int | None, body: ScheduledTaskUpdate
    ) -> ScheduledTaskResponse:
        data = body.model_dump(exclude_none=True)
        if "cronExpression" in data:
            self._validateCron(data["cronExpression"])
        requires_approval_reissue = "approvalPolicy" in data and data["approvalPolicy"] is not None
        if requires_approval_reissue:
            data.update({
                "status": TASK_STATUS_PENDING_APPROVAL,
                "nextRunAt": None,
                "approvalStatus": APPROVAL_STATUS_PENDING,
                "approvalApprovedAt": None,
                "approvalApprovedBy": None,
                "approvalTokenId": None,
                "approvalRejectedReason": None,
            })
        if not data:
            task = self._getTaskOrRaise(taskId, userId)
            return ScheduledTaskResponse.model_validate(task)
        count = self.dao.updateTask(taskId, data, userId=userId)
        if not count:
            raise InvalidParamException(userMessage=f"不存在 id 为 {taskId} 的定时任务")
        task = self._getTaskOrRaise(taskId, userId)
        if requires_approval_reissue:
            self._removeSchedulerJob(taskId)
            task = self._issueApprovalCode(taskId, task.createdBy)
        else:
            self._refreshScheduler(task)
        return ScheduledTaskResponse.model_validate(task)

    def listTasks(
        self,
        userId: int | None,
        status: str | None = None,
        includeDeleted: bool = False,
    ) -> ListResponse:
        rows = self.dao.listTasks(
            userId=userId,
            status=status,
            includeDeleted=includeDeleted,
        )
        items = [ScheduledTaskResponse.model_validate(row) for row in rows]
        return ListResponse(total=len(items), items=items)

    def getTask(self, taskId: int, userId: int | None) -> ScheduledTaskResponse:
        return ScheduledTaskResponse.model_validate(self._getTaskOrRaise(taskId, userId))

    def pauseTask(self, taskId: int, userId: int | None = None) -> ScheduledTaskResponse:
        task = self._getTaskOrRaise(taskId, userId)
        self.dao.updateTask(task.id, {"status": "paused", "nextRunAt": None}, userId=userId)
        updated = self._getTaskOrRaise(taskId, userId)
        self._removeSchedulerJob(taskId)
        return ScheduledTaskResponse.model_validate(updated)

    def resumeTask(self, taskId: int, userId: int | None = None) -> ScheduledTaskResponse:
        task = self._getTaskOrRaise(taskId, userId)
        self.dao.updateTask(task.id, {"status": "active"}, userId=userId)
        updated = self._getTaskOrRaise(taskId, userId)
        self._refreshScheduler(updated)
        return ScheduledTaskResponse.model_validate(updated)

    def deleteTask(self, taskId: int, userId: int | None = None) -> None:
        task = self._getTaskOrRaise(taskId, userId)
        self.dao.updateTask(task.id, {"status": TASK_STATUS_DELETED, "nextRunAt": None}, userId=userId)
        self._removeSchedulerJob(taskId)

    async def triggerTask(self, taskId: int, userId: int | None) -> ScheduledTaskRunResponse:
        self._getTaskOrRaise(taskId, userId)
        run = await self.runTask(taskId)
        return ScheduledTaskRunResponse.model_validate(run)

    async def runTask(self, taskId: int):
        task = self._getTaskOrRaise(taskId, None)
        if task.status == TASK_STATUS_DELETED:
            raise InvalidParamException(userMessage=f"定时任务 {taskId} 已删除")
        if task.status == TASK_STATUS_PENDING_APPROVAL:
            raise InvalidParamException(userMessage=f"定时任务 {taskId} 正在等待 CLI 审批")
        run = self.dao.createRun(task.id)
        try:
            from gateway.service.AgentGatewayService import AgentGatewayService
            result = await AgentGatewayService().createEphemeralRun(
                userId=task.createdBy,
                title=f"定时任务: {task.name}",
                message=task.taskDescription,
                scheduledApprovalPolicy=task.approvalPolicy,
                includeCoreTools=True,
                source="scheduled",
                autoRunTaskId=task.id,
                autoRunGuidance=UNATTENDED_TASK_GUIDANCE,
            )
            self.dao.finishRun(
                run.id,
                result["sessionId"],
                result["status"],
                result["summary"],
                result["errorMessage"],
                result["tokenUsage"],
            )
            self.dao.markLastRun(task.id)
            return self.dao.getRun(run.id)
        except Exception as exc:
            self.dao.finishRun(
                run.id, None, "error", None, str(exc), None,
            )
            raise

    def listRuns(self, taskId: int, userId: int | None, limit: int = 50) -> ListResponse:
        self._getTaskOrRaise(taskId, userId)
        rows = self.dao.listRuns(taskId, limit)
        items = [ScheduledTaskRunResponse.model_validate(row) for row in rows]
        return ListResponse(total=len(items), items=items)

    def getRun(self, runId: int) -> ScheduledTaskRunResponse:
        run = self.dao.getRun(runId)
        if run is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {runId} 的执行记录")
        return ScheduledTaskRunResponse.model_validate(run)

    def _getTaskOrRaise(self, taskId: int, userId: int | None):
        task = self.dao.getTask(taskId, userId=userId)
        if task is None or task.status == TASK_STATUS_DELETED:
            raise InvalidParamException(userMessage=f"不存在 id 为 {taskId} 的定时任务")
        return task

    def listPendingApprovalTasks(self) -> ListResponse:
        return self.listTasks(None, status=TASK_STATUS_PENDING_APPROVAL, includeDeleted=True)

    def getApproval(self, taskId: int) -> dict:
        task = self._getTaskOrRaise(taskId, None)
        return {
            "taskId": task.id,
            "status": task.status,
            "approvalPolicy": task.approvalPolicy,
            "approvalCode": task.approvalCode,
            "approvalStatus": task.approvalStatus,
            "approvalApprovedAt": task.approvalApprovedAt,
            "approvalApprovedBy": task.approvalApprovedBy,
            "approvalTokenId": task.approvalTokenId,
            "approvalRejectedReason": task.approvalRejectedReason,
        }

    def reissueApproval(self, taskId: int) -> ScheduledTaskResponse:
        task = self._getTaskOrRaise(taskId, None)
        if task.status != TASK_STATUS_PENDING_APPROVAL:
            raise InvalidParamException(userMessage="只有 pending_approval 状态的任务可以重新触发审批")
        if not task.approvalPolicy:
            raise InvalidParamException(userMessage="该任务没有 approvalPolicy，无法触发审批")
        updated = self._issueApprovalCode(taskId, task.createdBy)
        return ScheduledTaskResponse.model_validate(updated)

    def approveScheduledTaskPolicy(
        self,
        taskId: int,
        approvedBy: str,
        tokenId: str,
    ) -> bool:
        task = self.dao.getTask(taskId, userId=None)
        if task is None or task.status != TASK_STATUS_PENDING_APPROVAL:
            return False
        self.dao.updateTask(taskId, {
            "status": TASK_STATUS_ACTIVE,
            "approvalStatus": APPROVAL_STATUS_APPROVED,
            "approvalApprovedAt": datetime.now(),
            "approvalApprovedBy": approvedBy,
            "approvalTokenId": tokenId,
            "approvalRejectedReason": None,
        })
        updated = self._getTaskOrRaise(taskId, None)
        self._refreshScheduler(updated)
        return True

    def rejectScheduledTaskPolicy(self, taskId: int, reason: str) -> bool:
        task = self.dao.getTask(taskId, userId=None)
        if task is None or task.status != TASK_STATUS_PENDING_APPROVAL:
            return False
        self.dao.updateTask(taskId, {
            "approvalStatus": APPROVAL_STATUS_REJECTED,
            "approvalRejectedReason": reason,
        })
        self._removeSchedulerJob(taskId)
        return True

    def _issueApprovalCode(self, taskId: int, userId: int) -> object:
        task = self._getTaskOrRaise(taskId, None)
        from gateway.service.elevation_service import ElevationService

        policy = task.approvalPolicy or {}
        ttl_seconds = int(policy.get("ttlSeconds") or 3600)
        max_runs = int(policy.get("maxRuns") or 100)
        entry = ElevationService().generate_code(
            session_id=f"scheduled_task:{taskId}",
            commands=[],
            reason=f"定时任务预授权: {task.name}",
            ttl_seconds=ttl_seconds,
            max_ops=max_runs,
            request_type="scheduled_task_policy",
            task_id=taskId,
            approval_policy=policy,
        )
        self.dao.updateTask(taskId, {
            "approvalCode": entry.code,
            "approvalStatus": APPROVAL_STATUS_PENDING,
            "approvalRejectedReason": None,
        })
        return self._getTaskOrRaise(taskId, None)

    @staticmethod
    def _validateCron(cronExpression: str) -> None:
        from gateway.scheduler.scheduler import AgentScheduler
        if not AgentScheduler().validateCronExpression(cronExpression):
            raise InvalidParamException(userMessage="cronExpression 格式不正确，请使用 5 段 crontab 表达式")

    @staticmethod
    def _refreshScheduler(task) -> None:
        from gateway.scheduler.scheduler import AgentScheduler
        AgentScheduler().refreshTask(task)

    @staticmethod
    def _removeSchedulerJob(taskId: int) -> None:
        from gateway.scheduler.scheduler import AgentScheduler
        AgentScheduler().removeTask(taskId)
