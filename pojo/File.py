from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from pojo.Common import PageSearchRequest,ListResponse
# ==========================================
# 1. 通用实体模型
# ==========================================

class FileItem(BaseModel):
    """文件条目模型"""
    name: str = Field(..., description="文件名")
    path: str = Field(..., description="文件路径")
    type: int = Field(..., ge=0, le=3, description="类型: 0=文件夹, 1=文本文件, 2=二进制文件, 3其他")
    size: int = Field(default=0, ge=0, description="文件大小")
    createdTime: datetime = Field(..., description="创建时间")
    modifiedTime: datetime = Field(..., description="修改时间")
    owner: str = Field(..., max_length=64, description="所有者")
    group: str = Field(..., max_length=64, description="组")
    permissions: str = Field(..., max_length=10, description="权限标识")
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_file_info(cls, file_info) -> "FileItem":
        """从 FileInfo 模型转换为 FileItem（避免 pojo 层引入 toolFunction 的运行时依赖）"""
        # FileType(str, Enum) → int 映射，与 FileItem.type 字段兼容
        _type_map = {
            "file": 0,
            "directory": 1,
            "symlink": 2,
            "other": 3,
        }
        return cls(
            name=file_info.fileName,
            type=_type_map.get(file_info.fileType, 3),
            path=file_info.absolutePath,
            size=file_info.sizeBytes,
            createdTime=file_info.modifiedTime,
            modifiedTime=file_info.modifiedTime,
            owner=file_info.owner or "",
            permissions=file_info.permissions,
            group=file_info.group or "",
        )


class FolderNode(BaseModel):
    """文件夹树节点模型 (递归结构)"""
    name: str = Field(..., description="文件夹名称")
    path: str = Field(..., description="文件夹路径")
    children: Optional[List['FolderNode']] = Field(default=None, description="子文件夹列表")

    model_config = ConfigDict(from_attributes=True)

# 解决递归引用问题
FolderNode.model_rebuild()


# ==========================================
# 2. 操作日志模型 - 用于接口返回展示
# ==========================================

class FileOperationLogBase(BaseModel):
    """日志基类"""
    userId: int = Field(..., description="操作用户ID")
    operationType: int = Field(..., description="操作类型: 1=上传, 2=删除, 3=批量删除, 4=修改权限")
    targetPath: str = Field(..., max_length=1024, description="目标路径")
    detail: Optional[str] = Field(None, max_length=500, description="详细信息")
    result: str = Field(..., description="操作结果描述")
    ipAddress: Optional[str] = Field(None, max_length=50, description="IP地址")

class FileOperationLog(FileOperationLogBase):
    """日志完整模型"""
    id: int
    operateTime: datetime = Field(default_factory=datetime.now, description="操作时间")
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. 请求模型
# ==========================================

class ListDirectoryRequest(PageSearchRequest):
    path: str = Field(..., description="目标路径")


class GetFolderTreeRequest(BaseModel):
    rootPath: str = Field(..., description="根路径")
    depth: int = Field(default=1, ge=1, description="递归深度")


class DeletePathRequest(BaseModel):
    path: str = Field(..., description="要删除的路径")

class BatchDeletePathRequest(BaseModel):
    paths: List[str] = Field(..., description="要删除的路径列表")

class GetPermissionsRequest(BaseModel):
    path: str = Field(..., description="文件路径")

class UpdatePermissionsRequest(BaseModel):
    path: str = Field(..., description="文件路径")
    permissions: str = Field(..., max_length=10, description="新权限值")

class SearchFilesRequest(BaseModel):
    path: str = Field(..., description="搜索起始路径")
    expression: str = Field(..., description="搜索表达式/关键字")
    recursive: bool = Field(default=False, description="是否递归搜索子目录")
    ignoreCase: bool = Field(default=False, description="是否忽略大小写")
    invertMatch: bool = Field(default=False, description="是否取反匹配")

class CreateFileRequest(BaseModel):
    path: str = Field(..., description="文件路径")

class ZipFileRequest(BaseModel):
    path: str = Field(..., description="文件路径")

class UnzipFileRequest(BaseModel):
    dstPath: str = Field(..., description="解压目标路径")
    zipFilePath: Optional[str] = Field(None, description="压缩文件路径")

class RenameOrMoveFileRequest(BaseModel):
    sourcePath: str = Field(..., description="原文件路径")
    destinationPath: str = Field(..., description="新文件路径")

class CopyFileRequest(BaseModel):
    sourcePath: str = Field(..., description="原文件路径")
    destinationPath: str = Field(..., description="新文件路径")

class UpdateOwnerRequest(BaseModel):
    targetPath: str = Field(..., description="路径")
    owner: str = Field(..., max_length=64, description="新所有者")
    group: str = Field(..., max_length=64, description="新组")
    recursive: bool = Field(default=False, description="是否递归更新子目录")

class WriteTextRequest(BaseModel):
    path: str = Field(..., description="文件路径")
    content: str = Field(..., description="要写入的内容")

# ==========================================
# 4. 响应模型
# ==========================================

class ListDirectoryResponse(ListResponse):
    page: int = Field(..., description="当前页")


class GetFolderTreeResponse(BaseModel):
    folderTree: List[FolderNode] = Field(default_factory=list, description="文件夹树")

class GetPermissionsResponse(BaseModel):
    path: str
    permissions: str
    owner: str
    group: str

class SearchFilesResponse(ListResponse):
    pass