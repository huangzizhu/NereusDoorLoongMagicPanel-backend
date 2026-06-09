from Exception.DataBaseException import DataBaseException
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.AgentTraceDaoOrm import AgentTraceDaoOrm
from pojo.Agent import AgentTraceLogResponse, AgentTraceSummary, AgentTraceTimelineItem
from pojo.Common import ListResponse


class AgentTraceService(Singleton):
    @singletonInit
    def __init__(self):
        self.dao = AgentTraceDaoOrm()

    def queryTraces(self, sessionId: str | None = None,
                    traceId: str | None = None,
                    eventType: str | None = None,
                    limit: int = 100) -> ListResponse:
        try:
            rows = self.dao.query(sessionId=sessionId, traceId=traceId,
                                  eventType=eventType, limit=limit)
            items = [AgentTraceLogResponse.model_validate(row) for row in rows]
            return ListResponse(total=len(items), items=items)
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def timeline(self, sessionId: str, limit: int = 200) -> ListResponse:
        try:
            rows = self.dao.timeline(sessionId, limit)
            items = [AgentTraceTimelineItem.model_validate(row) for row in rows]
            return ListResponse(total=len(items), items=items)
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def summary(self, sessionId: str) -> AgentTraceSummary:
        try:
            return AgentTraceSummary.model_validate(self.dao.summary(sessionId))
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)
