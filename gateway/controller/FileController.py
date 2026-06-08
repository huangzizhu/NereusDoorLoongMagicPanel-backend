from fastapi import APIRouter,UploadFile, File, Form
from fastapi.responses import FileResponse
from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from gateway.service.FileService import FileService
from pojo.File import (ListDirectoryRequest, ListDirectoryResponse
, GetFolderTreeRequest, DeletePathRequest, BatchDeletePathRequest, UpdatePermissionsRequest
, CreateFileRequest, RenameOrMoveFileRequest, CopyFileRequest, FileItem, SearchFilesRequest,
SearchFilesResponse, ZipFileRequest, UnzipFileRequest, UpdateOwnerRequest, WriteTextRequest)
from pojo.Common import ListResponse
from utils.toolFunction.models.ops.filesystem.filesystem_models import (PermissionChangeResult
, FileOperationResult, DecompressResult, CompressResult, OwnerChangeResult, TextFileReadResult, TextFileWriteResult)


class FileController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/file", tags=["文件管理"])
        self.fileService: FileService = FileService()
        super().__init__("fileController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.post("/list")
        def getFileList(listDirectoryRequest: ListDirectoryRequest) -> ResponseModel:
            list: ListDirectoryResponse = self.fileService.getFileList(listDirectoryRequest)
            return Response.success(data=list)

        @self.router.post("/tree")
        def getFileTree(treeRequest: GetFolderTreeRequest) -> ResponseModel:
            res = self.fileService.getFileTree(treeRequest)
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

        @self.router.get("/download/{filePath:path}")
        def downloadFile(filePath: str) -> FileResponse:
            fileResponse: FileResponse = self.fileService.downloadFile(filePath)
            return fileResponse

        @self.router.get("/info/{filePath:path}")
        def getFileInfo(filePath: str) -> ResponseModel:
            fileInfo: FileItem = self.fileService.getFileInfo(filePath)
            return Response.success(data=fileInfo)

        @self.router.post("/search")
        def searchFiles(searchRequest: SearchFilesRequest) -> ResponseModel:
            res: SearchFilesResponse = self.fileService.searchFiles(searchRequest)
            return Response.success(data=res)

        @self.router.post("/copy")
        def copyFile(copyRequest: CopyFileRequest) -> ResponseModel:
            res: FileOperationResult = self.fileService.copyFile(copyRequest)
            return Response.success(res)

        @self.router.post("/zip")
        def zipFile(zipRequest: ZipFileRequest) -> ResponseModel:
            res: CompressResult = self.fileService.zipFile(zipRequest)
            return Response.success(res)

        @self.router.post("/unzip")
        def unzipFile(unzipRequest: UnzipFileRequest) -> ResponseModel:
            res: DecompressResult = self.fileService.unzipFile(unzipRequest)
            return Response.success(res)

        @self.router.put("/owner")
        def updateOwner(ownerRequest: UpdateOwnerRequest) -> ResponseModel:
            res: OwnerChangeResult = self.fileService.updateOwner(ownerRequest)
            return Response.success(res)

        @self.router.get("/read/{path:path}")
        def readTextFile(path: str) -> ResponseModel:
            text: TextFileReadResult = self.fileService.readTextFile(path)
            return Response.success(data=text)

        @self.router.post("/write")
        def writeTextFile(writeRequest: WriteTextRequest) -> ResponseModel:
            res: TextFileWriteResult = self.fileService.writeTextFile(writeRequest)
            return Response.success(res)






