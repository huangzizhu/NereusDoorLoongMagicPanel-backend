from gateway.dao.FileDaoInterface import FileDaoInterface
from gateway.dao.FileDaoOrm import FileDaoOrm
from gateway.Singleton import Singleton,singletonInit
from pojo.File import ListDirectoryResponse, ListDirectoryRequest
from pojo.File import FileItem
from ndlmpanel_agent.tools.ops.filesystem.filesystem_tools import listDirectory
from ndlmpanel_agent.models.ops.filesystem.filesystem_models import FileInfo
from ndlmpanel_agent.exceptions.tool_exceptions import ToolExecutionException , PermissionDeniedException
from typing import List
from modelAdapter.FileAdapter import FileAdapter
from Exception.FilePermissionDeniedException import FilePermissionDeniedException
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException


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








