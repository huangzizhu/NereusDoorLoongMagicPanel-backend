from datetime import datetime
from decimal import Decimal
from typing import Optional

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentTokenUsageOrm import AgentTokenUsageOrm
from gateway.orm.OrmEngine import OrmEngine

# ── 模型定价表（¥/百万 tokens） ──
# 计价公式：cost = tokens / 1_000_000 * price_per_million
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    "deepseek-chat": (0.5, 2.0),          # input ¥0.5/M, output ¥2.0/M
    "deepseek-v4-pro": (0.5, 2.0),
    "deepseek-v4-flash": (0.1, 0.4),
    "deepseek-reasoner": (0.5, 2.0),
    "qwen-plus": (0.8, 2.0),
    "qwen-max": (2.0, 6.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4o": (2.5, 10.0),
    "claude-3-haiku": (0.25, 1.25),
    "claude-3.5-sonnet": (3.0, 15.0),
}


def _getPrices(model: str) -> tuple[float, float]:
    """获取模型的 input/output 每百万 token 价格（¥）。"""
    for key, prices in _MODEL_PRICING.items():
        if key in model.lower():
            return prices
    return (1.0, 3.0)  # 默认


def _computeCost(model: str, inputTokens: int, outputTokens: int) -> tuple[float, float, float]:
    """计算费用。返回 (inputCost, outputCost, totalCost) 单位 ¥。"""
    inputPrice, outputPrice = _getPrices(model)
    inputCost = inputTokens / 1_000_000 * inputPrice
    outputCost = outputTokens / 1_000_000 * outputPrice
    totalCost = inputCost + outputCost
    return (round(inputCost, 6), round(outputCost, 6), round(totalCost, 6))


class AgentTokenUsageDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    def recordUsage(self, sessionId: str, model: str,
                    inputTokens: int, outputTokens: int,
                    traceId: str | None = None) -> AgentTokenUsageOrm:
        """记录一次 LLM 调用的 token 用量并自动计算费用。"""
        totalTokens = inputTokens + outputTokens
        inputCost, outputCost, totalCost = _computeCost(model, inputTokens, outputTokens)

        session = self.SessionLocal()
        try:
            orm = AgentTokenUsageOrm(
                sessionId=sessionId,
                traceId=traceId,
                model=model,
                inputTokens=inputTokens,
                outputTokens=outputTokens,
                totalTokens=totalTokens,
                inputCost=inputCost,
                outputCost=outputCost,
                totalCost=totalCost,
            )
            session.add(orm)
            session.commit()
            session.expunge(orm)
            return orm
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getSessionUsage(self, sessionId: str) -> list[AgentTokenUsageOrm]:
        """获取会话的 token 用量明细。"""
        session = self.SessionLocal()
        try:
            rows = session.query(AgentTokenUsageOrm).filter(
                AgentTokenUsageOrm.sessionId == sessionId
            ).order_by(AgentTokenUsageOrm.id.asc()).all()
            for row in rows:
                session.expunge(row)
            return rows
        finally:
            session.close()

    def getSessionBilling(self, sessionId: str) -> dict:
        """获取会话的汇总计费数据。"""
        session = self.SessionLocal()
        try:
            from sqlalchemy import func

            row = session.query(
                func.sum(AgentTokenUsageOrm.inputTokens).label("totalInputTokens"),
                func.sum(AgentTokenUsageOrm.outputTokens).label("totalOutputTokens"),
                func.sum(AgentTokenUsageOrm.totalTokens).label("totalTokens"),
                func.sum(AgentTokenUsageOrm.inputCost).label("totalInputCost"),
                func.sum(AgentTokenUsageOrm.outputCost).label("totalOutputCost"),
                func.sum(AgentTokenUsageOrm.totalCost).label("totalCost"),
                func.count(AgentTokenUsageOrm.id).label("callCount"),
            ).filter(
                AgentTokenUsageOrm.sessionId == sessionId
            ).first()

            if row is None or row.totalTokens is None:
                return {
                    "sessionId": sessionId,
                    "totalInputTokens": 0,
                    "totalOutputTokens": 0,
                    "totalTokens": 0,
                    "totalInputCost": 0.0,
                    "totalOutputCost": 0.0,
                    "totalCost": 0.0,
                    "callCount": 0,
                }

            return {
                "sessionId": sessionId,
                "totalInputTokens": int(row.totalInputTokens or 0),
                "totalOutputTokens": int(row.totalOutputTokens or 0),
                "totalTokens": int(row.totalTokens or 0),
                "totalInputCost": round(float(row.totalInputCost or 0), 6),
                "totalOutputCost": round(float(row.totalOutputCost or 0), 6),
                "totalCost": round(float(row.totalCost or 0), 6),
                "callCount": int(row.callCount or 0),
            }
        finally:
            session.close()
