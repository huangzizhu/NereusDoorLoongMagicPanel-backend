from typing import Optional

from gateway.Singleton import Singleton, singletonInit
from gateway.dao.AgentModelPricingDaoOrm import AgentModelPricingDaoOrm
from gateway.orm.AgentTokenUsageOrm import AgentTokenUsageOrm
from gateway.orm.OrmEngine import OrmEngine


def _computeCost(inputPrice: float, cachedInputPrice: float,
                  outputPrice: float, multiplier: float,
                  nonCachedInputTokens: int, cachedInputTokens: int,
                  outputTokens: int) -> tuple[float, float, float, float, float]:
    """根据价格和 token 数计算费用。返回 (nonCachedInputCost, cachedInputCost, inputCost, outputCost, totalCost)。"""
    nonCachedInputCost = nonCachedInputTokens / 1_000_000 * inputPrice * multiplier
    cachedInputCost = cachedInputTokens / 1_000_000 * cachedInputPrice * multiplier
    outputCost = outputTokens / 1_000_000 * outputPrice * multiplier
    inputCost = nonCachedInputCost + cachedInputCost
    totalCost = inputCost + outputCost
    return (
        round(nonCachedInputCost, 6),
        round(cachedInputCost, 6),
        round(inputCost, 6),
        round(outputCost, 6),
        round(totalCost, 6),
    )


class AgentTokenUsageDaoOrm(Singleton):
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)
        self._pricingDao = AgentModelPricingDaoOrm()

        # 启动时确保有种子价格数据
        self._pricingDao.seedDefaultPrices()

    def recordUsage(self, sessionId: str, model: str,
                    inputTokens: int, outputTokens: int,
                    cachedInputTokens: int = 0,
                    traceId: str | None = None) -> AgentTokenUsageOrm:
        """记录一次 LLM 调用的 token 用量（仅存原始数据，不计费）。"""
        totalTokens = inputTokens + outputTokens
        nonCachedInputTokens = inputTokens - cachedInputTokens

        session = self.SessionLocal()
        try:
            orm = AgentTokenUsageOrm(
                sessionId=sessionId,
                traceId=traceId,
                model=model,
                inputTokens=inputTokens,
                cachedInputTokens=cachedInputTokens,
                nonCachedInputTokens=nonCachedInputTokens,
                outputTokens=outputTokens,
                totalTokens=totalTokens,
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

    def getSessionUsage(self, sessionId: str,
                        credentialId: int | None = None) -> list[dict]:
        """获取会话的 token 用量明细（含动态计算的费用）。"""
        session = self.SessionLocal()
        try:
            rows = session.query(AgentTokenUsageOrm).filter(
                AgentTokenUsageOrm.sessionId == sessionId
            ).order_by(AgentTokenUsageOrm.id.asc()).all()

            result = []
            for row in rows:
                inp, cInp, out, mul = self._pricingDao.getPrice(row.model, credentialId)
                (ncc, cc, ic, oc, tc) = _computeCost(
                    inp, cInp, out, mul,
                    row.nonCachedInputTokens, row.cachedInputTokens, row.outputTokens,
                )
                result.append({
                    "id": row.id,
                    "sessionId": row.sessionId,
                    "traceId": row.traceId,
                    "model": row.model,
                    "inputTokens": row.inputTokens,
                    "cachedInputTokens": row.cachedInputTokens,
                    "nonCachedInputTokens": row.nonCachedInputTokens,
                    "outputTokens": row.outputTokens,
                    "totalTokens": row.totalTokens,
                    "cachedInputCost": cc,
                    "nonCachedInputCost": ncc,
                    "inputCost": ic,
                    "outputCost": oc,
                    "totalCost": tc,
                    "createdAt": row.createdAt.isoformat() if row.createdAt else None,
                })
            return result
        finally:
            session.close()

    def getSessionBilling(self, sessionId: str,
                          credentialId: int | None = None) -> dict:
        """获取会话的汇总计费数据（含动态计算的费用）。"""
        session = self.SessionLocal()
        try:
            from sqlalchemy import func

            row = session.query(
                func.sum(AgentTokenUsageOrm.inputTokens).label("totalInputTokens"),
                func.sum(AgentTokenUsageOrm.cachedInputTokens).label("totalCachedInputTokens"),
                func.sum(AgentTokenUsageOrm.nonCachedInputTokens).label("totalNonCachedInputTokens"),
                func.sum(AgentTokenUsageOrm.outputTokens).label("totalOutputTokens"),
                func.sum(AgentTokenUsageOrm.totalTokens).label("totalTokens"),
                func.count(AgentTokenUsageOrm.id).label("callCount"),
            ).filter(
                AgentTokenUsageOrm.sessionId == sessionId
            ).first()

            if row is None or row.totalTokens is None:
                return {
                    "sessionId": sessionId,
                    "totalInputTokens": 0,
                    "totalCachedInputTokens": 0,
                    "totalNonCachedInputTokens": 0,
                    "totalOutputTokens": 0,
                    "totalTokens": 0,
                    "totalCachedInputCost": 0.0,
                    "totalNonCachedInputCost": 0.0,
                    "totalInputCost": 0.0,
                    "totalOutputCost": 0.0,
                    "totalCost": 0.0,
                    "callCount": 0,
                }

            totalInput = int(row.totalInputTokens or 0)
            totalCached = int(row.totalCachedInputTokens or 0)
            totalNonCached = int(row.totalNonCachedInputTokens or 0)
            totalOutput = int(row.totalOutputTokens or 0)

            # 需要按 model 分组查价格再汇总，这里简化：用第一条记录的价格做整体估算
            # 因为不同 model 可能混合在同一会话中
            # 更精确的做法是按 model 分组
            model_rows = session.query(
                AgentTokenUsageOrm.model,
                func.sum(AgentTokenUsageOrm.inputTokens).label("totalInput"),
                func.sum(AgentTokenUsageOrm.cachedInputTokens).label("totalCached"),
                func.sum(AgentTokenUsageOrm.nonCachedInputTokens).label("totalNonCached"),
                func.sum(AgentTokenUsageOrm.outputTokens).label("totalOutput"),
            ).filter(
                AgentTokenUsageOrm.sessionId == sessionId
            ).group_by(AgentTokenUsageOrm.model).all()

            totalNcc = totalCc = totalIc = totalOc = totalTc = 0.0
            for mr in model_rows:
                inp, cInp, out, mul = self._pricingDao.getPrice(mr.model, credentialId)
                (ncc, cc, ic, oc, tc) = _computeCost(
                    inp, cInp, out, mul,
                    int(mr.totalNonCached or 0),
                    int(mr.totalCached or 0),
                    int(mr.totalOutput or 0),
                )
                totalNcc += ncc
                totalCc += cc
                totalIc += ic
                totalOc += oc
                totalTc += tc

            return {
                "sessionId": sessionId,
                "totalInputTokens": totalInput,
                "totalCachedInputTokens": totalCached,
                "totalNonCachedInputTokens": totalNonCached,
                "totalOutputTokens": totalOutput,
                "totalTokens": int(row.totalTokens or 0),
                "totalCachedInputCost": round(totalCc, 6),
                "totalNonCachedInputCost": round(totalNcc, 6),
                "totalInputCost": round(totalIc, 6),
                "totalOutputCost": round(totalOc, 6),
                "totalCost": round(totalTc, 6),
                "callCount": int(row.callCount or 0),
            }
        finally:
            session.close()
