from Exception.FileNotFoundException import FileNotFoundException
from Exception.GatewayAbstractException import GatewayAbstractException
from dao.FileDaoInterface import FileDaoInterface
from dao.FileDaoOrm import FileDaoOrm
from gateway.Singleton import Singleton,singletonInit
from pojo.File import (ListDirectoryResponse, ListDirectoryRequest
, GetFolderTreeRequest, GetFolderTreeResponse,
BatchDeletePathRequest, UpdatePermissionsRequest)
from pojo.File import FileItem
from pojo.Common import ListResponse
from ndlmpanel_agent.tools.ops.filesystem.filesystem_tools import (listDirectory
,deleteDirectory,deleteFile,changePermissions)
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
        p:Path = Path(path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在或不合法: {path}")
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
        p: Path = Path(updateRequest.path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在或不合法: {updateRequest.path}")
        try:
            return changePermissions(updateRequest.path,updateRequest.permissions,True)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"修改权限失败: {e.innerMessage}")
        except PermissionDeniedException as e:
            raise FilePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权修改该路径权限: {e.userMessage}")









