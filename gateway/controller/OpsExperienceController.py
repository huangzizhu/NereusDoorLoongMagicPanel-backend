from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import Response

from Exception.TokenAuthException import TokenAuthException
from gateway.Response import Response as MyResponse
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.OpsExperienceService import OpsExperienceService
from pojo.OpsExperience import (
    OpsExperienceFeedbackRequest,
    OpsExperiencePackCreate,
    OpsExperiencePackUpdate,
)
from utils.JWTTokenTool import getUserId


class OpsExperienceController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/ops-experience", tags=["OpsExperience"])
        self.service = OpsExperienceService()
        super().__init__("opsExperienceController", self.router)
        self.routerSetup()

    @staticmethod
    def _getRequestUserId(request: Request) -> int:
        accessToken = request.cookies.get("accessToken")
        if not accessToken:
            raise TokenAuthException(userMessage="未携带accessToken")
        userId = getUserId(accessToken)
        if not userId:
            raise TokenAuthException(userMessage="Token非法")
        return int(userId)

    def routerSetup(self):
        @self.router.post("/packs")
        def createPack(body: OpsExperiencePackCreate):
            return MyResponse.success(
                self.service.createPack(body.model_dump(), source="human")
            )

        @self.router.get("/packs")
        def listPacks(
            page: int = Query(1, ge=1),
            pageSize: int = Query(20, ge=1, le=200),
            q: str | None = None,
            category: str | None = None,
            status: str | None = None,
        ):
            return MyResponse.success(
                self.service.listPacks(
                    page=page, pageSize=pageSize, q=q, category=category, status=status
                )
            )

        @self.router.get("/packs/{packId}")
        def getPack(packId: int):
            return MyResponse.success(self.service.getPack(packId))

        @self.router.put("/packs/{packId}")
        def updatePack(request: Request, packId: int, body: OpsExperiencePackUpdate):
            self._getRequestUserId(request)
            return MyResponse.success(
                self.service.updatePack(packId, body.model_dump(exclude_unset=True))
            )

        @self.router.delete("/packs/{packId}")
        def deletePack(request: Request, packId: int):
            self._getRequestUserId(request)
            self.service.deletePack(packId)
            return MyResponse.success(msg="删除成功")

        @self.router.post("/packs/{packId}/feedback")
        def feedback(packId: int, body: OpsExperienceFeedbackRequest):
            return MyResponse.success(self.service.feedback(packId, body.action))

        @self.router.post("/import")
        async def importPack(request: Request, file: UploadFile = File(...)):
            self._getRequestUserId(request)
            content = await file.read()
            return MyResponse.success(self.service.importPack(content))

        @self.router.get("/packs/{packId}/export")
        def exportPack(packId: int):
            zipBytes, filename = self.service.exportPack(packId)
            from urllib.parse import quote
            return Response(
                content=zipBytes,
                media_type="application/zip",
                headers={
                    "Content-Disposition": (
                        f"attachment; filename=\"pack.zip\"; "
                        f"filename*=UTF-8''{quote(filename)}"
                    )
                },
            )

        @self.router.get("/knowledge-summary")
        def knowledgeSummary(limit: int = Query(20, ge=1, le=50)):
            return MyResponse.success(self.service.knowledgeSummary(limit=limit))

        @self.router.post("/packs/{packId}/attachments")
        async def uploadAttachment(
            request: Request,
            packId: int,
            file: UploadFile = File(...),
            fileType: str = Form("doc"),
            arch: str = Form("通用"),
            osType: str = Form("通用"),
        ):
            self._getRequestUserId(request)
            content = await file.read()
            return MyResponse.success(
                self.service.uploadAttachment(
                    packId=packId,
                    filename=file.filename or "attachment",
                    content=content,
                    fileType=fileType,
                    arch=arch,
                    osType=osType,
                )
            )
