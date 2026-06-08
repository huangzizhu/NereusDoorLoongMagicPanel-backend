from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class FileType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    OTHER = "other"


class FileInfo(BaseModel):
    fileName: str
    fileType: FileType
    sizeBytes: int
    permissions: str
    modifiedTime: datetime
    absolutePath: str
    createdTime: datetime | None = None
    owner: str | None = None
    group: str | None = None



class FileOperationResult(BaseModel):
    success: bool
    absolutePath: str | None = None
    errorMessage: str | None = None


class PermissionChangeResult(BaseModel):
    success: bool
    newPermissions: str | None = None
    errorMessage: str | None = None


class OwnerChangeResult(BaseModel):
    success: bool
    newOwner: str | None = None
    newGroup: str | None = None
    errorMessage: str | None = None


class GrepMatch(BaseModel):
    """Grep匹配结果的单条记录"""
    fileInfo: FileInfo
    lineNumber: int
    lineContent: str


class GrepResult(BaseModel):
    """Grep搜索结果的总体包装类"""
    success: bool
    pattern: str
    targetPath: str
    matches: list[GrepMatch]
    totalMatches: int
    errorMessage: str | None = None


class DirectoryTreeNode(BaseModel):
    """目录树中的单个节点"""
    fileName: str
    fileType: FileType
    absolutePath: str
    children: list["DirectoryTreeNode"] = []


class DirectoryTreeResult(BaseModel):
    """目录树查询结果"""
    success: bool
    rootPath: str
    maxDepth: int
    tree: DirectoryTreeNode | None = None
    errorMessage: str | None = None


class TextFileCheckResult(BaseModel):
    """文本文件判断结果"""
    isTextFile: bool
    targetPath: str
    detectedEncoding: str | None = None
    errorMessage: str | None = None


class CompressResult(BaseModel):
    """压缩操作结果"""
    success: bool
    sourcePath: str
    archivePath: str | None = None
    archiveSizeBytes: int | None = None
    errorMessage: str | None = None


class DecompressResult(BaseModel):
    """解压操作结果"""
    success: bool
    archivePath: str
    targetPath: str | None = None
    errorMessage: str | None = None


class TextFileReadResult(BaseModel):
    """文本文件读取结果"""
    success: bool
    targetPath: str
    content: str | None = None
    encoding: str | None = None
    sizeBytes: int | None = None
    errorMessage: str | None = None


class TextFileWriteResult(BaseModel):
    """文本文件写入结果"""
    success: bool
    targetPath: str
    sizeBytes: int | None = None
    errorMessage: str | None = None
