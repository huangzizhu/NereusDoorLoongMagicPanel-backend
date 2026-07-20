from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Any

from gateway.Singleton import Singleton, singletonInit
from gateway.dao.ScheduledTaskDaoOrm import ScheduledTaskDaoOrm

_logger = logging.getLogger("ndlmpanel.scheduler")

TIMEZONE = "Asia/Shanghai"
INSPECTION_JOB_ID = "system_inspection"
TASK_JOB_PREFIX = "scheduled_task:"


class AgentScheduler(Singleton):
    @singletonInit
    def __init__(self):
        self._scheduler = None
        self._taskDao = ScheduledTaskDaoOrm()
        self._inspectionIntervalMinutes = 30
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
        except ModuleNotFoundError:
            _logger.error("APScheduler 未安装，定时任务调度器未启动")
            return

        self._scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        self._scheduler.start()
        self._started = True
        self._registerInspectionJob()
        self.reloadTasks()
        _logger.info("AgentScheduler started")

    async def shutdown(self) -> None:
        if self._scheduler is not None and self._started:
            self._scheduler.shutdown(wait=False)
        self._scheduler = None
        self._started = False
        _logger.info("AgentScheduler stopped")

    @property
    def inspectionIntervalMinutes(self) -> int:
        return self._inspectionIntervalMinutes

    def setInspectionInterval(self, minutes: int) -> None:
        self._inspectionIntervalMinutes = max(1, int(minutes))
        self._registerInspectionJob()

    def validateCronExpression(self, cronExpression: str) -> bool:
        try:
            self._buildCronTrigger(cronExpression)
            return True
        except Exception:
            return False

    def reloadTasks(self) -> None:
        if self._scheduler is None:
            return
        for task in self._taskDao.listActiveTasks():
            self.scheduleTask(task)

    def scheduleTask(self, task: Any) -> None:
        if self._scheduler is None:
            return
        jobId = self._taskJobId(task.id)
        try:
            trigger = self._buildCronTrigger(task.cronExpression)
            job = self._scheduler.add_job(
                self._runScheduledTask,
                trigger=trigger,
                id=jobId,
                name=f"定时任务: {task.name}",
                args=[task.id],
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            self._taskDao.setNextRunAt(task.id, job.next_run_time)
        except Exception:
            _logger.exception("注册定时任务失败: task=%s", task.id)

    def removeTask(self, taskId: int) -> None:
        if self._scheduler is None:
            return
        jobId = self._taskJobId(taskId)
        try:
            if self._scheduler.get_job(jobId):
                self._scheduler.remove_job(jobId)
        except Exception:
            _logger.exception("移除定时任务失败: task=%s", taskId)

    def refreshTask(self, task: Any) -> None:
        self.removeTask(task.id)
        if task.status == "active":
            self.scheduleTask(task)

    def getConfig(self) -> dict:
        from ProjectRoot import getProjectRootPath
        return {
            "inspectionIntervalMinutes": self._inspectionIntervalMinutes,
            "inspectionDocPath": str(
                getProjectRootPath().joinpath("workspace", "inspection.md")
            ),
            "timezone": TIMEZONE,
            "schedulerStarted": self._started,
        }

    def _registerInspectionJob(self) -> None:
        if self._scheduler is None:
            return
        try:
            from apscheduler.triggers.interval import IntervalTrigger
            self._scheduler.add_job(
                self._runInspection,
                trigger=IntervalTrigger(
                    minutes=self._inspectionIntervalMinutes,
                    timezone=TIMEZONE,
                ),
                id=INSPECTION_JOB_ID,
                name="系统自动巡检",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
        except Exception:
            _logger.exception("注册自动巡检任务失败")

    async def _runInspection(self) -> None:
        from gateway.service.InspectionService import InspectionService
        await InspectionService().triggerInspection(userId=0, triggeredBy="schedule")

    async def _runScheduledTask(self, taskId: int) -> None:
        from gateway.service.ScheduledTaskService import ScheduledTaskService
        await ScheduledTaskService().runTask(taskId)

    def _buildCronTrigger(self, cronExpression: str):
        fields = cronExpression.split()
        if len(fields) != 5:
            raise ValueError("cronExpression 必须是 5 段 crontab 表达式")
        try:
            from apscheduler.triggers.cron import CronTrigger
        except ModuleNotFoundError:
            self._fallbackValidateCron(fields)
            return _FallbackCronTrigger(cronExpression)
        return CronTrigger.from_crontab(cronExpression, timezone=TIMEZONE)

    @staticmethod
    def _fallbackValidateCron(fields: list[str]) -> None:
        allowed = re.compile(r"^[\d*/,\-]+$|^\*$")
        for field in fields:
            if not allowed.match(field):
                raise ValueError("cronExpression 包含不支持的字段")

    @staticmethod
    def _taskJobId(taskId: int) -> str:
        return f"{TASK_JOB_PREFIX}{taskId}"


class _FallbackCronTrigger:
    def __init__(self, expression: str):
        self.expression = expression

    def get_next_fire_time(self, previous_fire_time, now):
        return datetime.now()
