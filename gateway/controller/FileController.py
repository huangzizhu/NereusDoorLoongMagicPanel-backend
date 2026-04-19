from fastapi import APIRouter,UploadFile, File, Form
from ndlmpanel_agent import FileOperationResult
from fastapi.responses import FileResponse

from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.FileService import FileService
from pojo.File import (ListDirectoryRequest, ListDirectoryResponse
, GetFolderTreeRequest, GetFolderTreeResponse, DeletePathRequest
, BatchDeletePathRequest, UpdatePermissionsRequest, GetPermissionsRequest
, CreateFileRequest, RenameOrMoveFileRequest, DownloadFileRequest)
from pojo.Common import ListResponse
from ndlmpanel_agent.models.ops.filesystem.filesystem_models import PermissionChangeResult,FileOperationResult

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

        @self.router.post("")
        def createFile(fileRequest: CreateFileRequest) -> ResponseModel:
            res: FileOperationResult = self.fileService.createFile(fileRequest.path)
            return Response.success(res)

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

        @self.router.get("/permissions")
        def getFilePermissions(permissionsRequest: GetPermissionsRequest) -> ResponseModel:
            res = self.fileService.getFilePermissions(permissionsRequest.path)
            return Response.success(res)

        @self.router.put("")
        def renameOrMoveFile(fileRequest: RenameOrMoveFileRequest) -> ResponseModel:
            res: FileOperationResult = self.fileService.renameOrMoveFile(fileRequest)
            return Response.success(res)

        @self.router.post("/dir")
        def createDir(fileRequest: CreateFileRequest) -> ResponseModel:
            res: FileOperationResult = self.fileService.createDir(fileRequest.path)
            return Response.success(res)

        @self.router.post("/upload")
        async def uploadFile(
                destinationPath: str = Form(...),  # 接收字符串参数
                file: UploadFile = File(...)  # 接收文件
        ) -> ResponseModel:
            res: FileOperationResult = await self.fileService.uploadFile(destinationPath, file)
            return Response.success(res)

        @self.router.get("/download")
        def downloadFile(request: DownloadFileRequest):
            fileResponse: FileResponse = self.fileService.downloadFile(request.filePath)
            return fileResponse



