from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from typing import Any

from Exception.InvalidParamException import InvalidParamException
from ProjectRoot import getProjectRootPath
from agent.prompt_loader import loadPrompt, renderPrompt
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.InspectionReportDaoOrm import InspectionReportDaoOrm
from pojo.Common import ListResponse
from pojo.ScheduledTask import InspectionReportResponse


# 巡检默认预授权基线：只读工具由 RuleEngine 自动放行，这里只约束
# 命令执行类工具（runCommand / runShellCommand）必须命中 allowedCommands。
DEFAULT_INSPECTION_POLICY: dict[str, Any] = {
    "allowedTools": ["runCommand", "runShellCommand"],
    # 命令前缀白名单：实际命令以这些前缀开头即放行（df -h 可匹配 df -h /）
    "allowedCommands": [
        "uname -a", "hostname", "uptime", "date",
        "cat /proc/loadavg", "cat /proc/meminfo", "cat /proc/cpuinfo",
        "df -h", "df -T", "free -h", "du -sh",
        "top -bn1", "ps aux", "ps -ef",
        "systemctl status", "systemctl is-active", "systemctl is-enabled",
        "systemctl list-units", "systemctl list-timers",
        "docker ps", "docker images", "docker stats --no-stream",
        "docker inspect", "docker logs --tail",
        "nginx -t", "nginx -v",
        "journalctl -n", "journalctl --since", "journalctl -u",
        "ss -tlnp", "ss -ulnp", "netstat -tlnp", "ip addr", "ip route",
        "ufw status", "iptables -L", "iptables -S", "lsblk", "blkid",
        "crontab -l", "who", "w", "last", "lastb",
    ],
    "allowedPaths": [],
    "deniedPaths": [],
    "allowedPrivilegedCommands": [],
    # 无人值守场景默认 7 小时（管理员可能 24h 后才登录审批）
    "ttlSeconds": 25200,
    "maxRuns": 100,
}


# 巡检无人值守机制提示词：注入巡检 agent（管理员不在线，只读诊断为主）。
INSPECTION_RUN_GUIDANCE: str = loadPrompt(
    "automation/inspection_guidance.txt"
)


class InspectionService(Singleton):
    @singletonInit
    def __init__(self):
        self.dao = InspectionReportDaoOrm()
        # 策略文件 load→merge→save 需要原子化（并发审批写回时避免丢更新）
        self._policy_lock = threading.Lock()

    async def triggerInspection(
        self,
        userId: int = 0,
        triggeredBy: str = "manual",
    ) -> InspectionReportResponse:
        prompt = self.buildInspectionPrompt()
        from gateway.service.AgentGatewayService import AgentGatewayService
        result = await AgentGatewayService().createEphemeralRun(
            userId=userId,
            title="自动巡检",
            message=prompt,
            includeCoreTools=True,
            scheduledApprovalPolicy=self.loadInspectionPolicy(),
            source="inspection",
            autoRunGuidance=INSPECTION_RUN_GUIDANCE,
        )
        findings = self._extractFindings(result["fullReport"])
        report = self.dao.createReport(
            sessionId=result["sessionId"],
            status=result["status"],
            summary=result["summary"],
            findings=findings,
            fullReport=result["fullReport"],
            durationMs=result["durationMs"],
            errorMessage=result["errorMessage"],
        )
        return InspectionReportResponse.model_validate(report)

    def listReports(self, page: int, pageSize: int) -> ListResponse:
        total, rows = self.dao.listReports(page, pageSize)
        items = [InspectionReportResponse.model_validate(row) for row in rows]
        return ListResponse(total=total, items=items)

    def latestReport(self) -> InspectionReportResponse | None:
        row = self.dao.latestReport()
        return InspectionReportResponse.model_validate(row) if row else None

    def getReport(self, reportId: int) -> InspectionReportResponse:
        row = self.dao.getReport(reportId)
        if row is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {reportId} 的巡检报告")
        return InspectionReportResponse.model_validate(row)

    def buildInspectionPrompt(self) -> str:
        docPath = self.inspectionDocPath()
        if docPath.exists():
            content = docPath.read_text(encoding="utf-8", errors="ignore")
        else:
            content = "# 巡检配置\n\n暂无配置，请检查系统基础状态。"
        return renderPrompt(
            "automation/inspection_prompt.txt", {"CONFIG": content}
        )

    @staticmethod
    def inspectionDocPath() -> Path:
        return getProjectRootPath().joinpath("workspace", "inspection.md")

    @staticmethod
    def inspectionPolicyPath() -> Path:
        return getProjectRootPath().joinpath("workspace", "inspection_policy.json")

    def loadInspectionPolicy(self) -> dict[str, Any]:
        """加载巡检预授权策略；文件不存在或损坏时使用默认基线。"""
        path = self.inspectionPolicyPath()
        if path.exists():
            try:
                policy = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(policy, dict) and policy:
                    return policy
            except (json.JSONDecodeError, OSError):
                pass
        return copy.deepcopy(DEFAULT_INSPECTION_POLICY)

    def saveInspectionPolicy(self, policy: dict[str, Any]) -> dict[str, Any]:
        path = self.inspectionPolicyPath()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(policy, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return policy

    @staticmethod
    def _extractFindings(fullReport: str) -> Any:
        if not fullReport:
            return []
        start = fullReport.rfind("{")
        end = fullReport.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return []
        try:
            payload = json.loads(fullReport[start:end + 1])
        except json.JSONDecodeError:
            return []
        findings = payload.get("findings") if isinstance(payload, dict) else None
        return findings if isinstance(findings, list) else []
