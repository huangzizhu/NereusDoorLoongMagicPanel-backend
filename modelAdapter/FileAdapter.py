from pojo.File import FileItem
from ndlmpanel_agent.models.ops.filesystem.filesystem_models import FileType,FileInfo

class FileAdapter:
    fileTypeMap = {
        FileType.FILE: 0,
        FileType.DIRECTORY: 1,
        FileType.SYMLINK: 2,
        FileType.OTHER: 3,
    }
    @staticmethod
    def FileInfo2FileItem(fileInfo: FileInfo) -> FileItem:
        return FileItem(
            name=fileInfo.fileName,
            type=FileAdapter.fileTypeMap[fileInfo.fileType],
            path=fileInfo.absolutePath,
            size=fileInfo.sizeBytes,
            createdTime=fileInfo.modifiedTime,
            modifiedTime=fileInfo.modifiedTime,
            owner="测试阶段",
            permissions=fileInfo.permissions,
        )