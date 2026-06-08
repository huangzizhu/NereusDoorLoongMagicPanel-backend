"""
文件系统操作工具 — 纯 stdlib (pathlib/os/shutil)，零外部依赖。

合并原 filesystem/filesystem_tools.py 全部函数，
去掉 pydantic / _command_runner。
"""
from __future__ import annotations
import grp
import os
import pwd
import re
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

from ndlmpanel_agent.shared.ops_types import (
    FileInfo, FileOperationResult, GrepMatch, GrepResult, TextFileReadResult,
)
from ndlmpanel_agent.shared.types import ToolRiskLevel

TOOLS = {
    # read_only
    "listDirectory": ToolRiskLevel.READ_ONLY,
    "listSingleFileOrDirectory": ToolRiskLevel.READ_ONLY,
    "grepFileOrDirectory": ToolRiskLevel.READ_ONLY,
    "getDirectoryTree": ToolRiskLevel.READ_ONLY,
    "isTextFile": ToolRiskLevel.READ_ONLY,
    "readTextFile": ToolRiskLevel.READ_ONLY,
    # write
    "createFile": ToolRiskLevel.WRITE,
    "createDirectory": ToolRiskLevel.WRITE,
    "renameFileOrDirectory": ToolRiskLevel.WRITE,
    "changePermissions": ToolRiskLevel.WRITE,
    "changeOwner": ToolRiskLevel.WRITE,
    "copyFile": ToolRiskLevel.WRITE,
    "compressPath": ToolRiskLevel.WRITE,
    "decompressArchive": ToolRiskLevel.WRITE,
    "writeTextFile": ToolRiskLevel.WRITE,
    # dangerous
    "deleteFile": ToolRiskLevel.DANGEROUS,
    "deleteDirectory": ToolRiskLevel.DANGEROUS,
}


def _run(argv: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"超时: {' '.join(argv)}") from None
    except FileNotFoundError:
        raise RuntimeError(f"命令不存在: {argv[0]}") from None


def _fmtPerms(mode: int) -> str:
    r = ""
    for shift in (6, 3, 0):
        bits = (stat.S_IMODE(mode) >> shift) & 0o7
        r += "r" if bits & 4 else "-"
        r += "w" if bits & 2 else "-"
        r += "x" if bits & 1 else "-"
    return r


def _resolvePath(path: str) -> Path:
    return Path(path).expanduser().resolve()


def _ownerName(uid: int) -> str | None:
    try:
        return pwd.getpwuid(uid).pw_name
    except (KeyError, AttributeError):
        return None


def _groupName(gid: int) -> str | None:
    try:
        return grp.getgrgid(gid).gr_name
    except (KeyError, AttributeError):
        return None


def _buildFileInfo(path: Path) -> FileInfo:
    st = path.lstat()
    return FileInfo(
        name=path.name, path=str(path), sizeBytes=st.st_size,
        isDirectory=path.is_dir(), permissions=_fmtPerms(st.st_mode),
        modifiedTime=st.st_mtime, owner=_ownerName(st.st_uid),
        group=_groupName(st.st_gid),
    )


# ── 列出 ──

def listDirectory(targetPath: str) -> list[FileInfo]:
    path = _resolvePath(targetPath)
    if not path.is_dir():
        return []
    results = []
    for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        try:
            results.append(_buildFileInfo(entry))
        except OSError:
            continue
    return results


def listSingleFileOrDirectory(targetPath: str) -> dict:
    path = _resolvePath(targetPath)
    if not path.exists():
        return {"error": f"路径不存在: {targetPath}"}
    try:
        fi = _buildFileInfo(path)
        import dataclasses
        return dataclasses.asdict(fi)
    except OSError as exc:
        return {"error": str(exc)}


# ── Grep ──

def grepFileOrDirectory(targetPath: str, regExpr: str,
                        recursive: bool = True, ignoreCase: bool = False,
                        searchFileNames: bool = False) -> GrepResult:
    """搜索文件名或文件内容。searchFileNames=True 时搜文件名（用 find），
    否则搜内容（用 grep）。"""
    path = _resolvePath(targetPath)
    if not path.exists():
        return GrepResult(success=False, pattern=regExpr,
                          matches=[], totalMatches=0)
    try:
        if searchFileNames:
            return _grepFileNames(path, regExpr, recursive, ignoreCase)
        return _grepContent(path, regExpr, recursive, ignoreCase)
    except RuntimeError:
        return GrepResult(success=False, pattern=regExpr,
                          matches=[], totalMatches=0)


def _grepFileNames(path: Path, pattern: str, recursive: bool,
                   ignoreCase: bool) -> GrepResult:
    cmd = ["find", str(path)]
    if not recursive:
        cmd += ["-maxdepth", "1"]
    cmd.append("-iregex" if ignoreCase else "-regex")
    cmd.append(f".*{pattern}.*")
    r = _run(cmd)
    matches = []
    for filePath in r.stdout.strip().split("\n"):
        if not filePath:
            continue
        try:
            fi = _buildFileInfo(Path(filePath))
            matches.append(GrepMatch(fileName=fi.name, lineNumber=0, lineContent=filePath))
        except OSError:
            continue
    return GrepResult(success=True, pattern=pattern, matches=matches, totalMatches=len(matches))


def _grepContent(path: Path, pattern: str, recursive: bool,
                 ignoreCase: bool) -> GrepResult:
    cmd = ["grep", "-n"]
    if ignoreCase:
        cmd.append("-i")
    if recursive and path.is_dir():
        cmd.append("-r")
    cmd += [pattern, str(path)]
    r = _run(cmd)
    matches = []
    cache: dict[str, FileInfo] = {}
    for line in r.stdout.strip().split("\n"):
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        fp, ln, content = parts[0], parts[1], parts[2]
        if fp not in cache:
            try:
                cache[fp] = _buildFileInfo(Path(fp))
            except OSError:
                continue
        matches.append(GrepMatch(fileName=cache[fp].name, lineNumber=int(ln),
                                  lineContent=content))
    return GrepResult(success=True, pattern=pattern, matches=matches, totalMatches=len(matches))


# ── 目录树 ──

def getDirectoryTree(targetPath: str, maxDepth: int = 1) -> dict:
    path = _resolvePath(targetPath)
    if not path.is_dir():
        return {"error": f"不是目录: {targetPath}"}

    def _buildTree(p: Path, depth: int) -> dict:
        node = {"name": p.name, "path": str(p), "isDir": p.is_dir(), "children": []}
        if depth >= maxDepth or not p.is_dir():
            return node
        try:
            for child in sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                try:
                    node["children"].append(_buildTree(child, depth + 1))
                except OSError:
                    pass
        except PermissionError:
            pass
        return node

    try:
        return {"success": True, "root": str(path), "tree": _buildTree(path, 0)}
    except OSError as exc:
        return {"error": str(exc)}


# ── CRUD ──

def createFile(targetPath: str) -> FileOperationResult:
    path = _resolvePath(targetPath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=False)
        return FileOperationResult(success=True, path=str(path), message="文件创建成功")
    except FileExistsError:
        return FileOperationResult(success=False, path=str(path), message="文件已存在")
    except PermissionError:
        return FileOperationResult(success=False, path=str(path), message="权限不足")


def createDirectory(targetPath: str) -> FileOperationResult:
    path = _resolvePath(targetPath)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return FileOperationResult(success=True, path=str(path), message="目录创建成功")
    except PermissionError:
        return FileOperationResult(success=False, path=str(path), message="权限不足")


def deleteFile(targetPath: str) -> FileOperationResult:
    path = _resolvePath(targetPath)
    if not path.exists():
        return FileOperationResult(success=False, path=str(path), message="文件不存在")
    if not path.is_file() and not path.is_symlink():
        return FileOperationResult(success=False, path=str(path), message="目标不是文件")
    try:
        path.unlink()
        return FileOperationResult(success=True, path=str(path), message="文件删除成功")
    except PermissionError:
        return FileOperationResult(success=False, path=str(path), message="权限不足")


def deleteDirectory(targetPath: str, force: bool = False) -> FileOperationResult:
    path = _resolvePath(targetPath)
    if not path.exists():
        return FileOperationResult(success=False, path=str(path), message="目录不存在")
    if not path.is_dir():
        return FileOperationResult(success=False, path=str(path), message="不是目录")
    try:
        if force:
            shutil.rmtree(path)
        else:
            path.rmdir()
        return FileOperationResult(success=True, path=str(path), message="目录删除成功")
    except OSError as exc:
        if "not empty" in str(exc).lower():
            return FileOperationResult(success=False, path=str(path),
                                       message="目录非空，请设 force=True")
        return FileOperationResult(success=False, path=str(path), message=str(exc))


def renameFileOrDirectory(sourcePath: str, destinationPath: str) -> FileOperationResult:
    src = _resolvePath(sourcePath)
    dst = _resolvePath(destinationPath)
    if not src.exists():
        return FileOperationResult(success=False, path=str(src), message="源路径不存在")
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return FileOperationResult(success=True, path=str(dst), message="重命名成功")
    except OSError as exc:
        return FileOperationResult(success=False, path=str(src), message=str(exc))


def copyFile(sourcePath: str, destinationPath: str) -> FileOperationResult:
    src = _resolvePath(sourcePath)
    dst = _resolvePath(destinationPath)
    if not src.is_file():
        return FileOperationResult(success=False, path=str(src), message="源不是文件")
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return FileOperationResult(success=True, path=str(dst), message="拷贝成功")
    except OSError as exc:
        return FileOperationResult(success=False, path=str(src), message=str(exc))


# ── 权限 / 属主 ──

def changePermissions(targetPath: str, permissionMode: str,
                      recursive: bool = False) -> dict:
    path = _resolvePath(targetPath)
    if not path.exists():
        return {"success": False, "message": "路径不存在"}
    try:
        mode = int(permissionMode, 8)
    except ValueError:
        return {"success": False, "message": f"权限格式错误(需八进制): {permissionMode}"}
    try:
        if recursive and path.is_dir():
            for root, dirs, files in os.walk(str(path)):
                os.chmod(root, mode)
                for f in files:
                    os.chmod(os.path.join(root, f), mode)
        else:
            os.chmod(str(path), mode)
        newMode = oct(stat.S_IMODE(path.stat().st_mode))[2:]
        return {"success": True, "newPermissions": newMode}
    except PermissionError:
        return {"success": False, "message": "权限不足，通常需要 root"}


def changeOwner(targetPath: str, owner: str, group: str,
                recursive: bool = False) -> dict:
    path = _resolvePath(targetPath)
    if not path.exists():
        return {"success": False, "message": "路径不存在"}
    try:
        uid = pwd.getpwnam(owner).pw_uid
    except (KeyError, AttributeError):
        return {"success": False, "message": f"用户不存在: {owner}"}
    try:
        gid = grp.getgrnam(group).gr_gid
    except (KeyError, AttributeError):
        return {"success": False, "message": f"用户组不存在: {group}"}
    try:
        if recursive and path.is_dir():
            for root, dirs, files in os.walk(str(path)):
                os.chown(root, uid, gid)
                for f in files:
                    os.chown(os.path.join(root, f), uid, gid)
        else:
            os.chown(str(path), uid, gid)
        return {"success": True, "newOwner": owner, "newGroup": group}
    except PermissionError:
        return {"success": False, "message": "权限不足，通常需要 root"}


# ── 压缩 ──

def compressPath(targetPath: str) -> dict:
    path = _resolvePath(targetPath)
    if not path.exists():
        return {"success": False, "message": "路径不存在"}
    stem = path.stem if path.is_file() else path.name
    archive = path.parent / (stem + ".tar.gz")
    try:
        if path.is_dir():
            shutil.make_archive(str(path.parent / stem), "gztar",
                                root_dir=str(path.parent), base_dir=path.name)
        else:
            with tarfile.open(str(archive), "w:gz") as tar:
                tar.add(str(path), arcname=path.name)
        return {"success": True, "archivePath": str(archive),
                "sizeBytes": archive.stat().st_size}
    except OSError as exc:
        return {"success": False, "message": str(exc)}


def decompressArchive(archivePath: str, targetPath: str | None = None) -> dict:
    path = _resolvePath(archivePath)
    if not path.is_file():
        return {"success": False, "message": "压缩文件不存在"}
    suffixes = path.suffixes
    isZip = suffixes[-1] == ".zip" if suffixes else False
    isTarGz = len(suffixes) >= 2 and suffixes[-2] == ".tar" and suffixes[-1] == ".gz"
    isTar = suffixes[-1] == ".tar" if suffixes else False
    if not (isZip or isTarGz or isTar):
        return {"success": False, "message": "仅支持 .tar.gz / .tar / .zip"}
    dest = _resolvePath(targetPath) if targetPath else path.parent
    try:
        dest.mkdir(parents=True, exist_ok=True)
        fmt = "zip" if isZip else "gztar" if isTarGz else "tar"
        shutil.unpack_archive(str(path), str(dest), format=fmt)
        return {"success": True, "targetPath": str(dest)}
    except OSError as exc:
        return {"success": False, "message": str(exc)}


# ── 文本 ──

def isTextFile(targetPath: str) -> dict:
    path = _resolvePath(targetPath)
    if not path.is_file():
        return {"isTextFile": False, "targetPath": targetPath, "encoding": None}
    try:
        chunk = path.read_bytes()
    except OSError:
        return {"isTextFile": False, "targetPath": targetPath, "encoding": None}
    if b"\x00" in chunk:
        return {"isTextFile": False, "targetPath": targetPath, "encoding": None}
    for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            chunk.decode(enc)
            return {"isTextFile": True, "targetPath": targetPath, "encoding": enc}
        except (UnicodeDecodeError, LookupError):
            continue
    return {"isTextFile": False, "targetPath": targetPath, "encoding": None}


def readTextFile(targetPath: str) -> TextFileReadResult:
    path = _resolvePath(targetPath)
    check = isTextFile(targetPath)
    if not check["isTextFile"]:
        return TextFileReadResult(success=False, targetPath=targetPath,
                                   content="", encoding=None)
    try:
        content = path.read_text(encoding=check["encoding"] or "utf-8")
        return TextFileReadResult(success=True, targetPath=targetPath,
                                   content=content, encoding=check["encoding"],
                                   sizeBytes=path.stat().st_size)
    except OSError as exc:
        return TextFileReadResult(success=False, targetPath=targetPath,
                                   content="", encoding=None)


def writeTextFile(targetPath: str, content: str) -> FileOperationResult:
    path = _resolvePath(targetPath)
    if not path.is_file():
        return FileOperationResult(success=False, path=str(path), message="目标文件不存在")
    try:
        path.write_text(content, encoding="utf-8")
        return FileOperationResult(success=True, path=str(path),
                                   message=f"写入成功({len(content)}字符)")
    except OSError as exc:
        return FileOperationResult(success=False, path=str(path), message=str(exc))
