from fastapi import APIRouter

from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from service.FileService import FileService
from pojo.File import (ListDirectoryRequest, ListDirectoryResponse
, GetFolderTreeRequest, GetFolderTreeResponse, DeletePathRequest
, BatchDeletePathRequest, UpdatePermissionsRequest)
from pojo.Common import ListResponse
from ndlmpanel_agent.models.ops.filesystem.filesystem_models import PermissionChangeResult

class FileController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/file", tags=["文件管理"])
        self.fileService: FileService = FileService()
        super().__init__("fileController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.get("/list")
        def getFileList(listDirectoryRequest: ListDirectoryRequest) -> ResponseModel:
            list: ListDirectoryResponse = self.fileService.getFileList(listDirectoryRequest)
            return Response.success(data=list)

        @self.router.get("/tree")
        def getFileTree(treeRequest: GetFolderTreeRequest) -> ResponseModel:
            res: GetFolderTreeResponse = self.fileService.getFileTree(treeRequest)
            return Response.success(data=res)

        @self.router.delete("")
        def deletePath(deleteRequest: DeletePathRequest) -> ResponseModel:
            self.fileService.deletePath(deleteRequest.path)
            return Response.success()

        @self.router.delete("/batch")
        def batchDeletePath(batchDeleteRequest: BatchDeletePathRequest) -> ResponseModel:
            res: ListResponse = self.fileService.batchDeletePath(batchDeleteRequest)
            return Response.success(res)

        @self.router.put("/permissions")
        def updatePermissions(updateRequest: UpdatePermissionsRequest) -> ResponseModel:
            res: PermissionChangeResult = self.fileService.updatePermissions(updateRequest)
            return Response.success(res)



