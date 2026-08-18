"""运维经验包导入导出：zip 打包/解包 + schemaVersion 校验 + 附件 sha256 完整性校验。

zip 结构：
    ops-experience-pack-{title}.zip
    ├── manifest.json      ← 元数据 + stages/pitfalls/earlyWarnings + schemaVersion + 附件清单(sha256/arch/osType)
    ├── deployment.md      ← 正文文档
    └── attachments/       ← 脚本/二进制/模板

一期：官方包 Ed25519 签名验签为二期目标（见 plans/bootstrap-deploy-design.md）。
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile

from Exception.InvalidParamException import InvalidParamException

# manifest 结构版本：向后兼容（只接受 <= 当前版本；新版本导入旧版包允许）
SCHEMA_VERSION = 1

_MANIFEST_NAME = "manifest.json"
_DEPLOYMENT_DOC_NAME = "deployment.md"
_ATTACHMENT_DIR = "attachments"

# 单附件大小上限（50MB）：防 zip bomb 撑爆磁盘
MAX_ATTACHMENT_SIZE = 50 * 1024 * 1024


def _buildManifest(pack: dict, attachments: list[dict]) -> dict:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "pack": {
            "title": pack["title"],
            "category": pack["category"],
            "osType": pack["osType"],
            "tags": pack.get("tags") or [],
            "riskLevel": pack.get("riskLevel") or "medium",
            "status": pack.get("status") or "enabled",
            "source": pack.get("source") or "human",
            "version": pack.get("version") or 1,
            "stages": pack.get("stages") or [],
            "pitfalls": pack.get("pitfalls") or [],
            "earlyWarnings": pack.get("earlyWarnings") or [],
        },
        "attachments": [
            {
                "filename": att["filename"],
                "fileType": att["fileType"],
                "sha256": att["sha256"],
                "size": att["size"],
                "arch": att["arch"],
                "osType": att["osType"],
            }
            for att in attachments
        ],
    }


def sanitizeZipName(title: str) -> str:
    """把标题清洗为安全的 zip 文件名。"""
    cleaned = re.sub(r"[^\w\-.\u4e00-\u9fff]+", "-", title, flags=re.UNICODE).strip("-")
    return cleaned or "ops-experience-pack"


def exportPackZip(pack: dict, attachments: list[dict], attachmentRoot) -> io.BytesIO:
    """打包单个经验包为 zip（BytesIO），不落盘。attachmentRoot 为绝对根目录。"""
    buffer = io.BytesIO()
    manifest = _buildManifest(pack, attachments)
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            _MANIFEST_NAME,
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        zf.writestr(_DEPLOYMENT_DOC_NAME, pack.get("deploymentDoc") or "")
        for att in attachments:
            attPath = attachmentRoot.joinpath(att["storagePath"])
            if not attPath.is_file():
                raise InvalidParamException(
                    userMessage=f"附件文件缺失，无法导出: {att['filename']}"
                )
            zf.write(attPath, f"{_ATTACHMENT_DIR}/{att['filename']}")
    buffer.seek(0)
    return buffer


def _safeMemberName(name: str) -> str:
    """拒绝 zip 内路径穿越（.. / 绝对路径 / 反斜杠）。"""
    if not name or name.startswith("/") or "\\" in name or ".." in name:
        raise InvalidParamException(userMessage=f"zip 内含非法路径: {name!r}")
    return name


def _safeFilename(filename: str) -> str:
    """附件文件名必须是纯文件名（无路径分隔符），防止落盘时嵌套/穿越目录。"""
    if not filename or filename in {".", ".."}:
        raise InvalidParamException(userMessage=f"非法的附件文件名: {filename!r}")
    if "/" in filename or "\\" in filename or filename.startswith("/"):
        raise InvalidParamException(
            userMessage=f"附件文件名不允许包含路径分隔符: {filename!r}"
        )
    return filename


def parsePackZip(data: bytes) -> dict:
    """解析导入 zip：校验 schemaVersion + 逐附件 sha256 校验。

    Returns:
        {
            "manifest": dict,
            "deploymentDoc": str,
            "attachments": [{"filename", "fileType", "content", "sha256", "size", "arch", "osType"}, ...],
        }
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise InvalidParamException(userMessage=f"无效的 zip 文件: {exc}") from exc

    names = set(zf.namelist())
    if _MANIFEST_NAME not in names:
        raise InvalidParamException(userMessage="缺少 manifest.json，不是合法的经验包 zip")
    if _DEPLOYMENT_DOC_NAME not in names:
        raise InvalidParamException(userMessage="缺少 deployment.md，不是合法的经验包 zip")

    try:
        manifest = json.loads(zf.read(_MANIFEST_NAME).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidParamException(userMessage=f"manifest.json 解析失败: {exc}") from exc

    schemaVersion = manifest.get("schemaVersion")
    if not isinstance(schemaVersion, int) or schemaVersion > SCHEMA_VERSION:
        raise InvalidParamException(
            userMessage=(
                f"manifest schemaVersion={schemaVersion} 不兼容（当前支持最高 "
                f"{SCHEMA_VERSION}），请升级面板后再导入"
            )
        )

    packMeta = manifest.get("pack") or {}
    required = {"title", "category"}
    missing = required - set(packMeta.keys())
    if missing:
        raise InvalidParamException(userMessage=f"manifest.pack 缺少字段: {sorted(missing)}")

    deploymentDoc = zf.read(_DEPLOYMENT_DOC_NAME).decode("utf-8", errors="replace")

    attachments = []
    for attMeta in manifest.get("attachments") or []:
        filename = _safeFilename(attMeta.get("filename") or "")
        member = _safeMemberName(f"{_ATTACHMENT_DIR}/{filename}")
        if member not in names:
            raise InvalidParamException(userMessage=f"附件缺失: {filename}")
        content = zf.read(member)
        if len(content) > MAX_ATTACHMENT_SIZE:
            raise InvalidParamException(
                userMessage=(
                    f"附件超过大小上限（{MAX_ATTACHMENT_SIZE // (1024 * 1024)}MB）: "
                    f"{filename}（{len(content)} 字节）"
                )
            )
        actualSha256 = hashlib.sha256(content).hexdigest()
        declaredSha256 = attMeta.get("sha256")
        if declaredSha256 and declaredSha256 != actualSha256:
            raise InvalidParamException(
                userMessage=f"附件 sha256 校验失败，已拒绝入库: {filename}"
            )
        declaredSize = attMeta.get("size")
        if declaredSize is not None and int(declaredSize) != len(content):
            raise InvalidParamException(
                userMessage=f"附件 size 与内容不符，已拒绝入库: {filename}"
            )
        attachments.append(
            {
                "filename": filename,
                "fileType": attMeta.get("fileType") or "doc",
                "content": content,
                "sha256": actualSha256,
                "size": len(content),
                "arch": attMeta.get("arch") or "通用",
                "osType": attMeta.get("osType") or packMeta.get("osType") or "通用",
            }
        )

    return {
        "manifest": manifest,
        "deploymentDoc": deploymentDoc,
        "attachments": attachments,
    }


def packMetaToFields(packMeta: dict) -> dict:
    """把 manifest.pack 元数据映射为 createPack 字段（仅白名单键）。"""
    allowed = {
        "title", "category", "osType", "tags", "stages", "pitfalls",
        "earlyWarnings", "riskLevel", "status", "source", "version",
    }
    return {key: packMeta[key] for key in allowed if key in packMeta}
