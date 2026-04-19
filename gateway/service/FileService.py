import os.path

from fastapi import UploadFile
from ndlmpanel_agent import createDirectory
from fastapi.responses import FileResponse

from Exception.FileAlreadyExistException import FileAlreadyExistException
from Exception.FileNotFoundException import FileNotFoundException
from Exception.FileTypeException import FileTypeException
from Exception.GatewayAbstractException import GatewayAbstractException
from gateway.dao.FileDaoInterface import FileDaoInterface
from gateway.dao.FileDaoOrm import FileDaoOrm
from gateway.Singleton import Singleton,singletonInit
from pojo.File import (FileItem,ListDirectoryResponse, ListDirectoryRequest
, GetFolderTreeRequest, GetFolderTreeResponse,
BatchDeletePathRequest, UpdatePermissionsRequest,RenameOrMoveFileRequest)
from pojo.Common import ListResponse
from ndlmpanel_agent.tools.ops.filesystem.filesystem_tools import (listDirectory
,deleteDirectory,deleteFile,changePermissions,createFile,renameFileOrDirectory)
from ndlmpanel_agent.models.ops.filesystem.filesystem_models import (FileInfo
,FileOperationResult,PermissionChangeResult)
from ndlmpanel_agent.exceptions.tool_exceptions import (ToolExecutionException
, PermissionDeniedException)
from typing import List
from modelAdapter.FileAdapter import FileAdapter
from Exception.FilePermissionDeniedException import FilePermissionDeniedException
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from pathlib import Path

class FileService(Singleton):
    @singletonInit
    def __init__(self):
        self.fileDao: FileDaoInterface = FileDaoOrm()

    def _validPath(self, path: str) -> Path:
        try:
            p: Path = Path(path)
            p.absolute()
            p.exists()#这个函数会访问磁盘，如果权限不足，会报错
            return p
        except PermissionError as e:
            raise FilePermissionDeniedException(innerMessage=str(e), userMessage=f"无权访问路径: {path}")
        except Exception:
            raise FileNotFoundException(userMessage=f"路径不合法: {path}")

    def getFileList(self, listDirectoryRequest: ListDirectoryRequest)->  ListDirectoryResponse:
        try:
            fileList: List[FileItem] = [FileAdapter.FileInfo2FileItem(fileInfo) for fileInfo in listDirectory(listDirectoryRequest.path)]
        except PermissionDeniedException as e:
            raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage="无权访问该目录")
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=e.userMessage)

        if  listDirectoryRequest.page == 0 and listDirectoryRequest.pageSize == 0:
            return ListDirectoryResponse(items=fileList, total=len(fileList),page=1)

        #需要分页
        return ListDirectoryResponse(
            items=fileList[(listDirectoryRequest.page - 1) * listDirectoryRequest.pageSize: listDirectoryRequest.page * listDirectoryRequest.pageSize],
            total=len(fileList),
            page=listDirectoryRequest.page
        )

    def getFileTree(self, treeRequest: GetFolderTreeRequest) -> GetFolderTreeResponse:
        pass

    def deletePath(self, path: str) -> FileOperationResult:
        p = self._validPath(path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {path}")
        if p.is_dir():
            try:
                res: FileOperationResult = deleteDirectory(path,force=True)
            except ToolExecutionException as e:
                raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"删除目录失败: {e.userMessage}")
            except PermissionDeniedException as e:
                raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权删除该目录: {e.userMessage}")
            if not res.success:
                raise BuiltinToolExecutionException(innerMessage=res.errorMessage, userMessage=f"删除目录失败: {path}, 错误信息: {res.errorMessage}")
        elif p.is_file():
            try:
                res: FileOperationResult = deleteFile(path)
            except ToolExecutionException as e:
                raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"删除文件失败: {e.userMessage}")
            except PermissionDeniedException as e:
                raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权删除该文件: {e.userMessage}")
            if not res.success:
                raise BuiltinToolExecutionException(innerMessage=res.errorMessage, userMessage=f"删除文件失败: {path}, 错误信息: {res.errorMessage}")
        else:
            raise FileNotFoundException(userMessage=f"跳过删除：路径是未知类型（非文件/非文件夹） {path}")
        return res

    def batchDeletePath(self, batchDeleteRequest: BatchDeletePathRequest) -> ListResponse:
        res = ListResponse(total=0,items=[])
        for path in batchDeleteRequest.paths:
            try:
                fileRes: FileOperationResult = self.deletePath(path)
                res.items.append(fileRes)
                res.total += 1
            except GatewayAbstractException as e:
                fileRes = FileOperationResult(success=False, errorMessage=e.userMessage, absolutePath=path)
                res.items.append(fileRes)
                res.total += 1
                continue

        return res

    def updatePermissions(self, updateRequest: UpdatePermissionsRequest) -> PermissionChangeResult:
        p: Path = self._validPath(updateRequest.path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在或不合法: {updateRequest.path}")
        try:
            return changePermissions(updateRequest.path,updateRequest.permissions,True)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"修改权限失败: {e.innerMessage}")
        except PermissionDeniedException as e:
            raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权修改该路径权限: {e.userMessage}")

    def getFilePermissions(self, path):
        pass

    def createFile(self, path: str) -> FileOperationResult:
        p: Path = self._validPath(path)
        if p.exists():
            raise FileAlreadyExistException(userMessage=f"文件已存在: {path}")
        try:
            return createFile(path)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"创建文件失败: {e.userMessage}")
        except PermissionDeniedException as e:
            raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权创建该文件: {e.userMessage}")

    def renameOrMoveFile(self, fileRequest: RenameOrMoveFileRequest) -> FileOperationResult:
        srcPath: Path = self._validPath(fileRequest.sourcePath)
        dstPath: Path = self._validPath(fileRequest.destinationPath)
        if not srcPath.exists():
            raise FileNotFoundException(userMessage=f"源路径不存在: {fileRequest.sourcePath}")
        if dstPath.exists():
            raise FileAlreadyExistException(userMessage=f"目标路径已存在: {fileRequest.destinationPath}")
        try:
            return renameFileOrDirectory(fileRequest.sourcePath, fileRequest.destinationPath)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"重命名/移动失败: {e.userMessage}")
        except PermissionDeniedException as e:
            raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权重命名/移动该文件: {e.userMessage}")

    async def uploadFile(self, destinationPath: str, file: UploadFile) -> FileOperationResult:
        p: Path = self._validPath(destinationPath)
        if not file or not file.filename:
            raise FileNotFoundException(innerMessage="未提供文件或文件名", userMessage="未提供文件或文件名")
        #创建父目录
        try:
            createDirectory(destinationPath)
        except PermissionDeniedException as e:
            raise FilePermissionDeniedException(innerMessage=e.innerMessage,
                                                userMessage=f"创建目录失败: {e.userMessage}")
        filepath = Path(destinationPath,file.filename)
        try:
            with open(filepath.absolute(), "wb") as f:
                while contents := await file.read(1024 * 1024):  # 每次读1MB
                    f.write(contents)
            return FileOperationResult(success=True, absolutePath=str(filepath.absolute()))
        except Exception as e:
            raise BuiltinToolExecutionException(innerMessage=str(e), userMessage=f"文件上传失败: {str(e)}")


    def createDir(self, path:str) -> FileOperationResult:
        p:Path = self._validPath(path)
        if p.exists():
            raise FileAlreadyExistException(userMessage=f"目录已存在: {path}")

        try:
            return createDirectory(path)
        except PermissionDeniedException as e:
            raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"创建目录失败: {e.userMessage}")

    def downloadFile(self, filePath: str) -> FileResponse:
        p: Path = self._validPath(filePath)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"文件不存在: {filePath}")
        if not p.is_file():
            raise FileTypeException(userMessage=f"目标路径不是文件: {filePath}")
        try:
            return FileResponse(path=str(p.absolute()), filename=p.name, media_type="application/octet-stream")
        except Exception as e:
            raise BuiltinToolExecutionException(innerMessage=str(e), userMessage=f"文件下载失败: {str(e)}")












