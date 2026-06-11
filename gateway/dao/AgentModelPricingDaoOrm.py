from __future__ import annotations

from typing import Optional

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentModelPricingOrm import AgentModelPricingOrm
from gateway.orm.OrmEngine import OrmEngine
from pojo.ModelPricing import ModelPricingCreate, ModelPricingUpdate

# ── 代码默认价格（当数据库无匹配记录时的兜底）──
_DEFAULT_PRICES = (1.0, 0.1, 3.0, 1.0)  # inputPrice, cachedInputPrice, outputPrice, multiplier


class AgentModelPricingDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    # ── 价格查询（核心逻辑）──

    def getPrice(self, model: str, credentialId: int | None = None
                 ) -> tuple[float, float, float, float]:
        """查询模型价格，返回 (inputPrice, cachedInputPrice, outputPrice, multiplier)。

        优先级：
          1. model 完全匹配 + credentialId 完全匹配（用户自定义价）
          2. model 完全匹配 + credentialId IS NULL（官方全局价）
          3. model 模糊匹配（子串匹配）+ credentialId IS NULL
          4. 代码默认值
        """
        session = self.SessionLocal()
        try:
            # 1. 精确匹配 model + credentialId
            if credentialId is not None:
                row = session.query(AgentModelPricingOrm).filter(
                    AgentModelPricingOrm.model == model,
                    AgentModelPricingOrm.credentialId == credentialId,
                    AgentModelPricingOrm.isActive == 1,
                ).first()
                if row is not None:
                    return (row.inputPrice, row.cachedInputPrice,
                            row.outputPrice, row.multiplier)

            # 2. 精确匹配 model + 全局价
            row = session.query(AgentModelPricingOrm).filter(
                AgentModelPricingOrm.model == model,
                AgentModelPricingOrm.credentialId.is_(None),
                AgentModelPricingOrm.isActive == 1,
            ).first()
            if row is not None:
                return (row.inputPrice, row.cachedInputPrice,
                        row.outputPrice, row.multiplier)

            # 3. 子串模糊匹配 + 全局价（兼容 "deepseek-chat" 匹配不到 "deepseek-v4-flash" 的情况）
            all_global = session.query(AgentModelPricingOrm).filter(
                AgentModelPricingOrm.credentialId.is_(None),
                AgentModelPricingOrm.isActive == 1,
            ).all()
            for row in all_global:
                if row.model.lower() in model.lower() or model.lower() in row.model.lower():
                    return (row.inputPrice, row.cachedInputPrice,
                            row.outputPrice, row.multiplier)

            return _DEFAULT_PRICES
        finally:
            session.close()

    # ── CRUD ──

    def createPricing(self, request: ModelPricingCreate) -> int:
        """创建定价并返回 pricingId。

        若 (model, credentialId) 组合已存在，则直接更新现有记录（upsert 语义）。
        """
        session = self.SessionLocal()
        try:
            # 检查是否已存在
            existing = session.query(AgentModelPricingOrm).filter(
                AgentModelPricingOrm.model == request.model,
                AgentModelPricingOrm.credentialId == request.credentialId,
            ).first()
            if existing is not None:
                from datetime import datetime
                existing.inputPrice = request.inputPrice
                existing.cachedInputPrice = request.cachedInputPrice
                existing.outputPrice = request.outputPrice
                existing.multiplier = request.multiplier
                existing.updatedAt = datetime.now()
                session.commit()
                pricing_id = existing.pricingId
                session.expunge(existing)
                return pricing_id

            orm = AgentModelPricingOrm(
                model=request.model,
                inputPrice=request.inputPrice,
                cachedInputPrice=request.cachedInputPrice,
                outputPrice=request.outputPrice,
                multiplier=request.multiplier,
                credentialId=request.credentialId,
            )
            session.add(orm)
            session.flush()
            pricing_id = orm.pricingId
            session.commit()
            return pricing_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getPricingById(self, pricingId: int) -> Optional[AgentModelPricingOrm]:
        session = self.SessionLocal()
        try:
            orm = session.query(AgentModelPricingOrm).filter(
                AgentModelPricingOrm.pricingId == pricingId
            ).one_or_none()
            if orm is None:
                return None
            session.expunge(orm)
            return orm
        finally:
            session.close()

    def listPricing(self, model: str | None = None,
                    credentialId: int | None = None,
                    isActive: int | None = None) -> list[AgentModelPricingOrm]:
        session = self.SessionLocal()
        try:
            query = session.query(AgentModelPricingOrm)
            if model is not None:
                query = query.filter(AgentModelPricingOrm.model.like(f"%{model}%"))
            if credentialId is not None:
                query = query.filter(AgentModelPricingOrm.credentialId == credentialId)
            if isActive is not None:
                query = query.filter(AgentModelPricingOrm.isActive == isActive)
            rows = query.order_by(
                AgentModelPricingOrm.credentialId.nullslast(),
                AgentModelPricingOrm.model.asc(),
            ).all()
            for row in rows:
                session.expunge(row)
            return rows
        finally:
            session.close()

    def updatePricing(self, pricingId: int,
                      request: ModelPricingUpdate) -> int:
        session = self.SessionLocal()
        try:
            data = request.model_dump(exclude_unset=True, exclude_none=True)
            if not data:
                return 0
            from datetime import datetime
            data["updatedAt"] = datetime.now()
            rowCount = session.query(AgentModelPricingOrm).filter(
                AgentModelPricingOrm.pricingId == pricingId
            ).update(data)
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deletePricing(self, pricingId: int) -> int:
        session = self.SessionLocal()
        try:
            rowCount = session.query(AgentModelPricingOrm).filter(
                AgentModelPricingOrm.pricingId == pricingId
            ).delete()
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def seedDefaultPrices(self) -> int:
        """插入官方全局种子价格（如果不存在）。"""
        session = self.SessionLocal()
        try:
            from datetime import datetime
            now = datetime.now()
            seeds = [
                ("deepseek-v4-flash", 1.0, 0.02, 2.0),
                ("deepseek-v4-pro", 3.0, 0.025, 6.0),
                ("deepseek-chat", 1.0, 0.02, 2.0),
                ("deepseek-reasoner", 3.0, 0.025, 6.0),
                ("qwen-plus", 0.8, 0.08, 2.0),
                ("qwen-max", 2.0, 0.2, 6.0),
                ("gpt-4o-mini", 0.15, 0.03, 0.6),
                ("gpt-4o", 2.5, 0.5, 10.0),
                ("claude-3-haiku", 0.25, 0.025, 1.25),
                ("claude-3.5-sonnet", 3.0, 0.3, 15.0),
            ]
            count = 0
            for model, inp, cached, out in seeds:
                exists = session.query(AgentModelPricingOrm).filter(
                    AgentModelPricingOrm.model == model,
                    AgentModelPricingOrm.credentialId.is_(None),
                ).first()
                if exists is None:
                    session.add(AgentModelPricingOrm(
                        model=model, inputPrice=inp,
                        cachedInputPrice=cached, outputPrice=out,
                        multiplier=1.0, credentialId=None,
                    ))
                    count += 1
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
