"""OpsExperienceService — 运维经验包业务层（Singleton）。

MCP 工具与管理 API 共用：
- 人工录入/更新/删除（source=human，version+1）
- AI 主动沉淀（source=ai，sourceSessionId 溯源）
- 诊断检索（qualityScore 排序，negative 默认过滤，命中 +1）
- Prompt 摘要注入（knowledgeSummary，会话固定一次）
- 附件落盘（runtime/ops-experience/attachments/{packId}/，DB 只存指针）
- 导入导出（zip + schemaVersion + sha256 去重）
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from Exception.InvalidParamException import InvalidParamException
from ProjectRoot import getProjectRootPath
from agent.prompt_loader import loadPrompt
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.OpsExperienceDaoOrm import OpsExperienceDaoOrm
from gateway.service import OpsExperiencePackExporter as Exporter

_logger = logging.getLogger("ndlmpanel.ops_experience")

_NEGATIVE_CATEGORY = "negative"
_SUMMARY_LINE_LIMIT = 60  # 每条摘要 deploymentDoc 首行截断字数（约）
_KNOWN_CATEGORIES = {"deployment", "fault", "optimization", "security", "negative"}
_KNOWN_RISK_LEVELS = {"low", "medium", "high"}


class OpsExperienceService(Singleton):
    @singletonInit
    def __init__(self):
        self.dao = OpsExperienceDaoOrm()
        self.attachmentRoot: Path = getProjectRootPath().joinpath(
            "runtime", "ops-experience", "attachments"
        )

    # ── 工具方法 ──────────────────────────────────────────────────────────

    def _validateCategory(self, category: str) -> str:
        category = (category or "").strip().lower()
        if category not in _KNOWN_CATEGORIES:
            raise InvalidParamException(
                userMessage=f"category 必须是 {'/'.join(sorted(_KNOWN_CATEGORIES))} 之一"
            )
        return category

    def _validateRiskLevel(self, riskLevel: str) -> str:
        riskLevel = (riskLevel or "").strip().lower()
        if riskLevel not in _KNOWN_RISK_LEVELS:
            raise InvalidParamException(
                userMessage=f"riskLevel 必须是 {'/'.join(sorted(_KNOWN_RISK_LEVELS))} 之一"
            )
        return riskLevel

    def _packDir(self, packId: int) -> Path:
        return self.attachmentRoot.joinpath(str(packId))

    @staticmethod
    def _docSummary(deploymentDoc: str, limit: int = _SUMMARY_LINE_LIMIT) -> str:
        """deploymentDoc 首行摘要：去掉 Markdown 符号后截断。"""
        firstLine = ""
        for line in (deploymentDoc or "").splitlines():
            stripped = line.strip()
            if stripped:
                firstLine = stripped
                break
        firstLine = firstLine.lstrip("#-*> \t")
        if len(firstLine) <= limit:
            return firstLine
        return firstLine[: limit - 3] + "..."

    def _enrichPack(self, pack: dict) -> dict:
        pack = dict(pack)
        pack["attachments"] = self.dao.listAttachments(pack["id"])
        return pack

    # ── 管理 API ──────────────────────────────────────────────────────────

    def createPack(
        self,
        payload: dict,
        source: str = "human",
        sourceSessionId: str | None = None,
    ) -> dict:
        return self.dao.createPack(
            title=str(payload["title"]).strip(),
            category=self._validateCategory(payload.get("category") or "deployment"),
            osType=str(payload.get("osType") or "通用").strip() or "通用",
            tags=list(payload.get("tags") or []),
            deploymentDoc=str(payload["deploymentDoc"]),
            stages=list(payload.get("stages") or []),
            pitfalls=list(payload.get("pitfalls") or []),
            earlyWarnings=list(payload.get("earlyWarnings") or []),
            riskLevel=self._validateRiskLevel(payload.get("riskLevel") or "medium"),
            status=str(payload.get("status") or "enabled"),
            source=source,
            sourceSessionId=sourceSessionId,
        )

    def getPack(self, packId: int) -> dict | None:
        pack = self.dao.getPack(packId)
        if pack is None:
            return None
        return self._enrichPack(pack)

    def listPacks(
        self,
        page: int = 1,
        pageSize: int = 20,
        q: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> dict:
        total, rows = self.dao.listPacks(
            page=page, pageSize=pageSize, q=q, category=category, status=status
        )
        return {"total": total, "items": rows}

    def updatePack(self, packId: int, payload: dict) -> dict:
        pack = self.dao.getPack(packId)
        if pack is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {packId} 的经验包")
        if "category" in payload and payload["category"] is not None:
            payload["category"] = self._validateCategory(payload["category"])
        if "riskLevel" in payload and payload["riskLevel"] is not None:
            payload["riskLevel"] = self._validateRiskLevel(payload["riskLevel"])
        updated = self.dao.updatePack(packId, payload)
        return self._enrichPack(updated)

    def deletePack(self, packId: int) -> None:
        pack = self.dao.getPack(packId)
        if pack is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {packId} 的经验包")
        # 删除包前清理本包独占的附件文件（共享文件由其它包持有，不物理删除）
        records = self.dao.deleteAttachmentsByPack(packId)
        packDir = self._packDir(packId)
        for record in records:
            storagePath = Path(record["storagePath"])
            if storagePath.parts and str(storagePath.parts[0]) == str(packId):
                target = self.attachmentRoot.joinpath(record["storagePath"])
                try:
                    target.unlink(missing_ok=True)
                except OSError:
                    _logger.warning("附件物理删除失败: %s", target)
        if packDir.exists():
            try:
                packDir.rmdir()  # 仅删除空目录
            except OSError:
                pass
        self.dao.deletePack(packId)

    def feedback(self, packId: int, action: str) -> dict:
        if action not in {"useful", "useless", "hit"}:
            raise InvalidParamException(userMessage="action 必须是 useful|useless|hit")
        pack = self.dao.feedback(packId, action)
        if pack is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {packId} 的经验包")
        return pack

    # ── Prompt 摘要注入（session 构造时调用，必须 try/except 兜底）────────

    # 空库冷启动引导：无包列表，但必须让 AI 知道沉淀机制，
    # 否则第一个经验包永远不会由 AI 生成（"组织记忆"无从起步）。
    _EMPTY_LIBRARY_GUIDANCE = loadPrompt("knowledge/empty_library.txt")

    def knowledgeSummary(self, limit: int = 20) -> str:
        """返回启用中经验包的紧凑摘要文本（供 system 消息注入）。

        库为空时返回空态使用指引（保证 AI 从第一个会话起就知道沉淀机制）；
        查询异常时返回空字符串（会话不注入该段，不阻塞会话创建）。
        """
        try:
            rows = self.dao.knowledgeSummaryRows(limit=limit)
        except Exception:
            _logger.exception("knowledgeSummary 查询失败，返回空摘要")
            return ""
        if not rows:
            return self._EMPTY_LIBRARY_GUIDANCE
        lines = []
        for row in rows:
            tags = ",".join(row.get("tags") or [])
            line = (
                f"[{row['category']}] {row['title']}"
                f"{' | ' + tags if tags else ''}"
                f" | {self._docSummary(row.get('deploymentDoc') or '')}"
            )
            lines.append(line)
        lines.append(loadPrompt("knowledge/usage_guidance.txt"))
        return "\n".join(lines)

    # ── MCP 工具 ──────────────────────────────────────────────────────────

    def searchPacks(
        self,
        query: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """按症状/关键词检索启用中的经验包（negative 默认过滤）。

        命中即 +1 hitCount（反馈统计）。返回条目标题+分类+标签+摘要+置信度。
        """
        includeNegative = category == _NEGATIVE_CATEGORY
        rows = self.dao.searchPacks(
            query=query,
            category=category,
            limit=limit,
            includeNegative=includeNegative,
        )
        items = []
        for row in rows:
            items.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "osType": row["osType"],
                    "tags": row.get("tags") or [],
                    "riskLevel": row.get("riskLevel") or "medium",
                    "qualityScore": row.get("qualityScore") or 0,
                    "hitCount": row.get("hitCount") or 0,
                    "summary": self._docSummary(row.get("deploymentDoc") or ""),
                    # negative 包仅提示，不实现复杂方案相似度匹配（二期）
                    "negativeOf": row.get("title") if row["category"] == _NEGATIVE_CATEGORY else None,
                }
            )
        # 命中即 +1（qualityScore 同步重算）
        for row in rows:
            try:
                self.dao.incrementHit(row["id"])
            except Exception:
                _logger.warning("hitCount 更新失败 packId=%s", row["id"])
        return items

    def getPackDetail(self, packId: int) -> dict:
        pack = self.dao.getPack(packId)
        if pack is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {packId} 的经验包")
        attachments = self.dao.listAttachments(packId)
        for att in attachments:
            # 给 Agent 完整绝对路径，便于 readTextFile 等工具读取附件内容（只读参考）
            att["absolutePath"] = str(self.attachmentRoot.joinpath(att["storagePath"]))
        pack["attachments"] = attachments
        return pack

    def submitPack(self, payload: dict, sourceSessionId: str | None = None) -> dict:
        """AI 主动沉淀（source=ai）：处置成功后由 Agent 调用。"""
        return self.dao.createPack(
            title=str(payload["title"]).strip(),
            category=self._validateCategory(payload.get("category") or "deployment"),
            osType=str(payload.get("osType") or "通用").strip() or "通用",
            tags=list(payload.get("tags") or []),
            deploymentDoc=str(payload["deploymentDoc"]),
            stages=list(payload.get("stages") or []),
            pitfalls=list(payload.get("pitfalls") or []),
            earlyWarnings=list(payload.get("earlyWarnings") or []),
            riskLevel=self._validateRiskLevel(payload.get("riskLevel") or "medium"),
            status="enabled",
            source="ai",
            sourceSessionId=sourceSessionId,
        )

    # ── 导入导出 ──────────────────────────────────────────────────────────

    def exportPack(self, packId: int) -> tuple[bytes, str]:
        pack = self.dao.getPack(packId)
        if pack is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {packId} 的经验包")
        attachments = self.dao.listAttachments(packId)
        buffer = Exporter.exportPackZip(pack, attachments, self.attachmentRoot)
        filename = f"ops-experience-pack-{Exporter.sanitizeZipName(pack['title'])}.zip"
        return buffer.getvalue(), filename

    def importPack(self, zipBytes: bytes) -> dict:
        """导入 zip 经验包：schemaVersion 校验 → 逐附件 sha256 校验 + 去重 → 落库 + 落盘。

        去重语义（对齐计划文档）：**附件按 sha256 去重** —— 已存在同哈希的附件
        文件不重复落盘（复用指针）；同一 zip 重复导入会创建新包记录，但附件文件
        只保留一份。整包级去重不实现（避免阻断"改附件后重新导入"场景）。
        """
        parsed = Exporter.parsePackZip(zipBytes)
        packMeta = parsed["manifest"].get("pack") or {}

        pack = self.dao.createPack(
            title=str(packMeta["title"]).strip(),
            category=self._validateCategory(packMeta["category"]),
            osType=str(packMeta.get("osType") or "通用").strip() or "通用",
            tags=list(packMeta.get("tags") or []),
            deploymentDoc=parsed["deploymentDoc"],
            stages=list(packMeta.get("stages") or []),
            pitfalls=list(packMeta.get("pitfalls") or []),
            earlyWarnings=list(packMeta.get("earlyWarnings") or []),
            riskLevel=self._validateRiskLevel(packMeta.get("riskLevel") or "medium"),
            status=str(packMeta.get("status") or "enabled"),
            source=str(packMeta.get("source") or "human"),
            version=int(packMeta.get("version") or 1),
        )
        pack["attachments"] = self._storeAttachments(pack["id"], parsed["attachments"])
        return pack

    def _storeAttachments(self, packId: int, attachments: list[dict]) -> list[dict]:
        """附件落盘 + 指针入库。按 sha256 全局去重：已存在的文件不重复落盘。"""
        stored: list[dict] = []
        packDir = self._packDir(packId)
        packDir.mkdir(parents=True, exist_ok=True)
        for att in attachments:
            existing = self.dao.findAttachmentBySha256(att["sha256"])
            if existing is not None:
                # 去重：复用已落盘文件（只读共享，删除包时不物理删除共享文件）
                record = self.dao.createAttachment(
                    packId=packId,
                    filename=att["filename"],
                    fileType=att["fileType"],
                    storagePath=existing["storagePath"],
                    sha256=att["sha256"],
                    size=att["size"],
                    arch=att.get("arch") or "通用",
                    osType=att.get("osType") or "通用",
                )
                stored.append(record)
                continue
            target = packDir.joinpath(att["filename"])
            target.write_bytes(att["content"])
            record = self.dao.createAttachment(
                packId=packId,
                filename=att["filename"],
                fileType=att["fileType"],
                storagePath=f"{packId}/{att['filename']}",
                sha256=att["sha256"],
                size=len(att["content"]),
                arch=att.get("arch") or "通用",
                osType=att.get("osType") or "通用",
            )
            stored.append(record)
        return stored

    # ── 附件上传（人工附加到已有包）───────────────────────────────────────

    def uploadAttachment(
        self,
        packId: int,
        filename: str,
        content: bytes,
        fileType: str = "doc",
        arch: str = "通用",
        osType: str = "通用",
    ) -> dict:
        pack = self.dao.getPack(packId)
        if pack is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {packId} 的经验包")
        if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
            raise InvalidParamException(userMessage=f"非法的附件文件名: {filename!r}")
        if fileType not in {"script", "binary", "doc", "archive"}:
            raise InvalidParamException(
                userMessage="fileType 必须是 script|binary|doc|archive"
            )
        sha256 = hashlib.sha256(content).hexdigest()
        existingSameName = [
            att for att in self.dao.listAttachments(packId)
            if att["filename"] == filename
        ]
        if existingSameName:
            if existingSameName[0]["sha256"] == sha256:
                return existingSameName[0]  # 幂等：同名同内容直接返回已有记录
            raise InvalidParamException(
                userMessage=f"同名附件已存在且内容不同: {filename}（请换名或先删除旧附件）"
            )
        existing = self.dao.findAttachmentBySha256(sha256)
        if existing is not None:
            return self.dao.createAttachment(
                packId=packId,
                filename=filename,
                fileType=fileType,
                storagePath=existing["storagePath"],
                sha256=sha256,
                size=len(content),
                arch=arch,
                osType=osType,
            )
        packDir = self._packDir(packId)
        packDir.mkdir(parents=True, exist_ok=True)
        target = packDir.joinpath(filename)
        target.write_bytes(content)
        return self.dao.createAttachment(
            packId=packId,
            filename=filename,
            fileType=fileType,
            storagePath=f"{packId}/{filename}",
            sha256=sha256,
            size=len(content),
            arch=arch,
            osType=osType,
        )

    def listAttachments(self, packId: int) -> list[dict]:
        return self.dao.listAttachments(packId)

    def getAttachment(self, attachmentId: int) -> dict | None:
        return self.dao.getAttachment(attachmentId)
