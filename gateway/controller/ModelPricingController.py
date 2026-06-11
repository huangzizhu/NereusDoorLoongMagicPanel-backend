from fastapi import APIRouter, Query

from Exception.InvalidParamException import InvalidParamException
from gateway.Response import Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.dao.AgentModelPricingDaoOrm import AgentModelPricingDaoOrm
from pojo.ModelPricing import ModelPricingCreate, ModelPricingResponse, ModelPricingUpdate
from pojo.Common import ListResponse


def _orm_to_dict(orm) -> dict:
    """安全地将 ORM 对象转为 dict，避免 Pydantic 直接验证 detached ORM 的懒加载问题。"""
    if orm is None:
        return None
    return {
        "pricingId": orm.pricingId,
        "model": orm.model,
        "inputPrice": orm.inputPrice,
        "cachedInputPrice": orm.cachedInputPrice,
        "outputPrice": orm.outputPrice,
        "multiplier": orm.multiplier,
        "credentialId": orm.credentialId,
        "isActive": orm.isActive,
        "createdAt": orm.createdAt.isoformat() if orm.createdAt else None,
        "updatedAt": orm.updatedAt.isoformat() if orm.updatedAt else None,
    }


class ModelPricingController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/agent/model-pricing", tags=["ModelPricing"])
        self.dao = AgentModelPricingDaoOrm()
        super().__init__("modelPricingController", self.router)
        self.routerSetup()

    def routerSetup(self):
        @self.router.post("")
        def createPricing(body: ModelPricingCreate):
            """新增一条模型定价（官方价或用户自定义价）。"""
            pricingId = self.dao.createPricing(body)
            orm = self.dao.getPricingById(pricingId)
            if orm is None:
                raise InvalidParamException(userMessage="新增定价失败")
            return Response.success(_orm_to_dict(orm))

        @self.router.get("")
        def listPricing(
            model: str | None = Query(None),
            credentialId: int | None = Query(None),
            isActive: int | None = Query(None),
        ):
            """查询模型定价列表。可筛选 model / credentialId / isActive。"""
            rows = self.dao.listPricing(model, credentialId, isActive)
            items = [_orm_to_dict(r) for r in rows]
            return Response.success(ListResponse(total=len(items), items=items))

        @self.router.get("/{pricingId}")
        def getPricing(pricingId: int):
            """获取单条模型定价。"""
            orm = self.dao.getPricingById(pricingId)
            if orm is None:
                raise InvalidParamException(userMessage=f"不存在 id 为 {pricingId} 的定价记录")
            return Response.success(_orm_to_dict(orm))

        @self.router.put("/{pricingId}")
        def updatePricing(pricingId: int, body: ModelPricingUpdate):
            """更新模型定价。"""
            rowCount = self.dao.updatePricing(pricingId, body)
            if not rowCount:
                raise InvalidParamException(userMessage=f"不存在 id 为 {pricingId} 的定价记录")
            orm = self.dao.getPricingById(pricingId)
            return Response.success(_orm_to_dict(orm))

        @self.router.delete("/{pricingId}")
        def deletePricing(pricingId: int):
            """删除模型定价。"""
            rowCount = self.dao.deletePricing(pricingId)
            if not rowCount:
                raise InvalidParamException(userMessage=f"不存在 id 为 {pricingId} 的定价记录")
            return Response.success()
