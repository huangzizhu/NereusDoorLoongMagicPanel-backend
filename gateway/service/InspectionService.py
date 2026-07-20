from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Exception.InvalidParamException import InvalidParamException
from ProjectRoot import getProjectRootPath
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.InspectionReportDaoOrm import InspectionReportDaoOrm
from pojo.Common import ListResponse
from pojo.ScheduledTask import InspectionReportResponse


class InspectionService(Singleton):
    @singletonInit
    def __init__(self):
        self.dao = InspectionReportDaoOrm()

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
        return (
            "## 系统自动巡检\n\n"
            "请按照以下配置进行系统巡检，检查服务器状态、关键服务、日志异常、"
            "磁盘空间、网络与安全风险。\n\n"
            f"{content}\n\n"
            "请输出可读巡检报告，并尽量在结尾提供 JSON 对象，包含 summary 和 findings 数组。"
        )

    @staticmethod
    def inspectionDocPath() -> Path:
        return getProjectRootPath().joinpath("workspace", "inspection.md")

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
