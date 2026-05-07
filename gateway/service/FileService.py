import os.path

from fastapi import UploadFile
from ndlmpanel_agent import createDirectory, listSingleFileOrDirectory, getDirectoryTree, grepFileOrDirectory, \
    compressPath
from fastapi.responses import FileResponse

from Exception.FileAlreadyExistException import FileAlreadyExistException
from Exception.FileNotFoundException import FileNotFoundException
from Exception.FileTypeException import FileTypeException
from Exception.GatewayAbstractException import GatewayAbstractException
from gateway.dao.FileDaoInterface import FileDaoInterface
from gateway.dao.FileDaoOrm import FileDaoOrm
from gateway.Singleton import Singleton,singletonInit
from pojo.File import (FileItem, ListDirectoryResponse, ListDirectoryRequest
, GetFolderTreeRequest, BatchDeletePathRequest, UpdatePermissionsRequest, RenameOrMoveFileRequest
, SearchFilesRequest, SearchFilesResponse, CopyFileRequest, ZipFileRequest, UnzipFileRequest, UpdateOwnerRequest,
                       WriteTextRequest)
from pojo.Common import ListResponse
from ndlmpanel_agent.tools.ops.filesystem.filesystem_tools import (listDirectory
, deleteDirectory, deleteFile, changePermissions, createFile, renameFileOrDirectory, copyFile, decompressArchive,
                                                                   changeOwner, isTextFile, readTextFile, writeTextFile)
from ndlmpanel_agent.models.ops.filesystem.filesystem_models import (FileInfo
, FileOperationResult, PermissionChangeResult, DirectoryTreeResult, GrepResult, CompressResult, DecompressResult,
                                                                     OwnerChangeResult, TextFileReadResult,
                                                                     TextFileCheckResult, TextFileWriteResult)
from ndlmpanel_agent.exceptions.tool_exceptions import (ToolExecutionException
, PermissionDeniedException,ResourceNotFoundException)
from typing import List
from modelAdapter.FileAdapter import FileAdapter
from Exception.ExecutePermissionDeniedException import ExecutePermissionDeniedException
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
            raise ExecutePermissionDeniedException(innerMessage=str(e), userMessage=f"无权访问路径: {path}")
        except Exception:
            raise FileNotFoundException(userMessage=f"路径不合法: {path}")

    def getFileList(self, listDirectoryRequest: ListDirectoryRequest)->  ListDirectoryResponse:
        try:
            fileList: List[FileItem] = [FileAdapter.FileInfo2FileItem(fileInfo) for fileInfo in listDirectory(listDirectoryRequest.path)]
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage="无权访问该目录")
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=e.innerMessage)
        except ResourceNotFoundException as e:
            raise FileNotFoundException(userMessage=e.innerMessage)

        if  listDirectoryRequest.page == 0 and listDirectoryRequest.pageSize == 0:
            return ListDirectoryResponse(items=fileList, total=len(fileList),page=1)

        #需要分页
        return ListDirectoryResponse(
            items=fileList[(listDirectoryRequest.page - 1) * listDirectoryRequest.pageSize: listDirectoryRequest.page * listDirectoryRequest.pageSize],
            total=len(fileList),
            page=listDirectoryRequest.page
        )

    def getFileTree(self, treeRequest: GetFolderTreeRequest) -> DirectoryTreeResult:
        p = self._validPath(treeRequest.rootPath)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {treeRequest.rootPath}")
        if not p.is_dir():
            raise FileTypeException(userMessage=f"目标路径不是目录: {treeRequest.rootPath}")
        try:
            return getDirectoryTree(treeRequest.rootPath,treeRequest.depth)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"获取目录树失败: {e.userMessage}")
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权访问该目录: {e.userMessage}")


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
                raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权删除该目录: {e.userMessage}")
            if not res.success:
                raise BuiltinToolExecutionException(innerMessage=res.errorMessage, userMessage=f"删除目录失败: {path}, 错误信息: {res.errorMessage}")
        elif p.is_file():
            try:
                res: FileOperationResult = deleteFile(path)
            except ToolExecutionException as e:
                raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"删除文件失败: {e.userMessage}")
            except PermissionDeniedException as e:
                raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权删除该文件: {e.userMessage}")
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
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权修改该路径权限: {e.userMessage}")

    def createFile(self, path: str) -> FileOperationResult:
        p: Path = self._validPath(path)
        if p.exists():
            raise FileAlreadyExistException(userMessage=f"文件已存在: {path}")
        try:
            return createFile(path)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"创建文件失败: {e.userMessage}")
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权创建该文件: {e.userMessage}")

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
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权重命名/移动该文件: {e.userMessage}")

    async def uploadFile(self, destinationPath: str, file: UploadFile) -> FileOperationResult:
        p: Path = self._validPath(destinationPath)
        if not file or not file.filename:
            raise FileNotFoundException(innerMessage="未提供文件或文件名", userMessage="未提供文件或文件名")
        #创建父目录
        try:
            createDirectory(destinationPath)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage,
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
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"创建目录失败: {e.userMessage}")

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

    def getFileInfo(self, filePath: str) -> FileItem:
        p: Path = self._validPath(filePath)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {filePath}")
        try:
            return FileAdapter.FileInfo2FileItem(listSingleFileOrDirectory(filePath))
        except Exception as e:
            raise BuiltinToolExecutionException(innerMessage=str(e), userMessage=f"文件信息获取失败: {str(e)}")


    def searchFiles(self, searchRequest: SearchFilesRequest) -> SearchFilesResponse:
        p: Path = self._validPath(searchRequest.path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {searchRequest.path}")
        if not p.is_dir():
            raise FileTypeException(userMessage=f"目标路径不是目录: {searchRequest.path}")
        try:
            grepResult: GrepResult = grepFileOrDirectory(targetPath=searchRequest.path,
                                                        regExpr=searchRequest.expression,
                                                        recursive=searchRequest.recursive,
                                                        ignoreCase=searchRequest.ignoreCase,
                                                        invertMatch=searchRequest.invertMatch,
                                                        searchFileNames=True)
            if not grepResult.success:
                raise BuiltinToolExecutionException(innerMessage=grepResult.errorMessage,userMessage="文件搜索失败")
            items: List[FileItem] = [FileAdapter.FileInfo2FileItem(match.fileInfo) for match in grepResult.matches]
            return SearchFilesResponse(items=items, total=grepResult.totalMatches)
        except Exception as e:
            raise BuiltinToolExecutionException(innerMessage=str(e), userMessage="文件搜索失败")


    def copyFile(self, copyRequest: CopyFileRequest) -> FileOperationResult:
        p: Path = self._validPath(copyRequest.sourcePath)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"文件不存在: {copyRequest.sourcePath}")
        if not p.is_file():
            raise FileTypeException(userMessage=f"目标路径不是文件: {copyRequest.sourcePath}")
        try:
            return copyFile(copyRequest.sourcePath, copyRequest.destinationPath)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权重复制该文件")
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=f"复制文件失败")

    def zipFile(self, zipRequest: ZipFileRequest) -> CompressResult:
        p: Path = self._validPath(zipRequest.path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {zipRequest.path}")
        try:
            return compressPath(zipRequest.path)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=f"无权压缩该路径: {zipRequest.path}")
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage="压缩失败")

    def unzipFile(self, unzipRequest: UnzipFileRequest) -> DecompressResult:
        zipPath: Path = self._validPath(unzipRequest.zipFilePath)
        if unzipRequest.dstPath:
            dstPath: Path = self._validPath(unzipRequest.dstPath)
            if dstPath.is_file():
                raise FileTypeException(userMessage=f"目标路径是文件: {unzipRequest.dstPath}")
        if not zipPath.exists():
            raise FileNotFoundException(userMessage=f"压缩文件不存在: {unzipRequest.zipFilePath}")
        try:
            return decompressArchive(unzipRequest.zipFilePath, unzipRequest.dstPath)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=e.innerMessage)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage="解压失败")

    def updateOwner(self, ownerRequest: UpdateOwnerRequest) -> OwnerChangeResult:
        p: Path = self._validPath(ownerRequest.targetPath)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {ownerRequest.targetPath}")
        try:
            return changeOwner(ownerRequest.targetPath, ownerRequest.owner, ownerRequest.group, ownerRequest.recursive)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=e.innerMessage)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=e.innerMessage)

    def readTextFile(self, path: str) -> TextFileReadResult:
        p: Path = self._validPath(path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {path}")
        if not p.is_file():
            raise FileTypeException(userMessage=f"目标路径不是文件: {path}")
        try:
            textFileCheckResult: TextFileCheckResult = isTextFile(path)
            if not textFileCheckResult.isTextFile:
                raise FileTypeException(userMessage=f"目标路径不是文本文件: {path}")
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=e.innerMessage)
        #大于10MB的文件不支持读取，报错
        if p.stat().st_size > 10 * 1024 * 1024:
            raise FileTypeException(userMessage=f"文件大小超过10MB: {path}")
        try:
            textFileReadResult: TextFileReadResult = readTextFile(path)
            if not textFileReadResult.success:
                raise BuiltinToolExecutionException(innerMessage=textFileReadResult.errorMessage, userMessage="读取文本文件失败")
            return textFileReadResult
        except BuiltinToolExecutionException:
            raise
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage=e.innerMessage)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=e.innerMessage)

    def writeTextFile(self, writeRequest: WriteTextRequest) -> TextFileWriteResult:
        p: Path = self._validPath(writeRequest.path)
        if not p.exists():
            raise FileNotFoundException(userMessage=f"路径不存在: {writeRequest.path}")
        if not p.is_file():
            raise FileTypeException(userMessage=f"目标路径不是文件: {writeRequest.path}")
        try:
            return writeTextFile(writeRequest.path, writeRequest.content)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(innerMessage=e.innerMessage, userMessage=e.innerMessage)
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(innerMessage=e.innerMessage, userMessage="写入文本文件失败")




















