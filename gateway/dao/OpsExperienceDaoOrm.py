import json
from typing import Any

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentLlmProfileOrm import AgentLlmProfileOrm  # noqa: F401
from gateway.orm.AgentSessionOrm import AgentSessionOrm  # noqa: F401
from gateway.orm.OpsExperienceOrm import (
    OpsExperienceAttachmentOrm,
    OpsExperiencePackOrm,
)
from gateway.orm.OrmEngine import OrmEngine


def _loadJson(raw: str | None) -> Any:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


class OpsExperienceDaoOrm(Singleton):
    """运维经验包 DAO：元数据/正文/结构化字段 + 附件指针的 CRUD 与统计。"""

    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    # ── 序列化 ────────────────────────────────────────────────────────────

    @staticmethod
    def _toObj(row: OpsExperiencePackOrm):
        return {
            "id": row.id,
            "title": row.title,
            "category": row.category,
            "osType": row.osType,
            "tags": _loadJson(row.tags),
            "deploymentDoc": row.deploymentDoc,
            "stages": _loadJson(row.stages),
            "pitfalls": _loadJson(row.pitfalls),
            "earlyWarnings": _loadJson(row.earlyWarnings),
            "riskLevel": row.riskLevel,
            "status": row.status,
            "source": row.source,
            "version": row.version,
            "sourceSessionId": row.sourceSessionId,
            "hitCount": row.hitCount,
            "usefulCount": row.usefulCount,
            "uselessCount": row.uselessCount,
            "qualityScore": row.qualityScore,
            "createdAt": row.createdAt,
            "updatedAt": row.updatedAt,
        }

    @staticmethod
    def _attachmentToObj(row: OpsExperienceAttachmentOrm):
        return {
            "id": row.id,
            "packId": row.packId,
            "filename": row.filename,
            "fileType": row.fileType,
            "storagePath": row.storagePath,
            "sha256": row.sha256,
            "size": row.size,
            "arch": row.arch,
            "osType": row.osType,
            "createdAt": row.createdAt,
        }

    # ── 经验包 CRUD ───────────────────────────────────────────────────────

    def createPack(
        self,
        title: str,
        category: str,
        deploymentDoc: str,
        osType: str = "通用",
        tags: list | None = None,
        stages: list | None = None,
        pitfalls: list | None = None,
        earlyWarnings: list | None = None,
        riskLevel: str = "medium",
        status: str = "enabled",
        source: str = "human",
        sourceSessionId: str | None = None,
        version: int = 1,
        qualityScore: int = 100,
    ) -> dict:
        session = self.SessionLocal()
        try:
            row = OpsExperiencePackOrm(
                title=title,
                category=category,
                osType=osType,
                tags=json.dumps(tags or [], ensure_ascii=False, default=str),
                deploymentDoc=deploymentDoc,
                stages=json.dumps(stages or [], ensure_ascii=False, default=str),
                pitfalls=json.dumps(pitfalls or [], ensure_ascii=False, default=str),
                earlyWarnings=json.dumps(earlyWarnings or [], ensure_ascii=False, default=str),
                riskLevel=riskLevel,
                status=status,
                source=source,
                sourceSessionId=sourceSessionId,
                version=version,
                qualityScore=qualityScore,
            )
            session.add(row)
            session.commit()
            result = self._toObj(row)
            session.expunge(row)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getPack(self, packId: int) -> dict | None:
        session = self.SessionLocal()
        try:
            row = session.query(OpsExperiencePackOrm).filter(
                OpsExperiencePackOrm.id == packId
            ).one_or_none()
            if row is None:
                return None
            result = self._toObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def listPacks(
        self,
        page: int,
        pageSize: int,
        q: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> tuple[int, list[dict]]:
        session = self.SessionLocal()
        try:
            query = session.query(OpsExperiencePackOrm)
            if q:
                # 多关键词分词 AND 匹配（"nginx 502" 可命中 "Nginx SSL 证书过期导致 502"）
                for token in [token for token in q.split() if token]:
                    like = f"%{token}%"
                    query = query.filter(
                        OpsExperiencePackOrm.title.like(like)
                        | OpsExperiencePackOrm.tags.like(like)
                        | OpsExperiencePackOrm.deploymentDoc.like(like)
                    )
            if category:
                query = query.filter(OpsExperiencePackOrm.category == category)
            if status:
                query = query.filter(OpsExperiencePackOrm.status == status)
            total = query.count()
            rows = query.order_by(
                OpsExperiencePackOrm.qualityScore.desc(),
                OpsExperiencePackOrm.id.desc(),
            ).offset(max(page - 1, 0) * pageSize).limit(pageSize).all()
            result = [self._toObj(row) for row in rows]
            for row in rows:
                session.expunge(row)
            return total, result
        finally:
            session.close()

    def searchPacks(
        self,
        query: str | None = None,
        category: str | None = None,
        limit: int = 10,
        includeNegative: bool = False,
    ) -> list[dict]:
        """检索启用中的经验包，按 qualityScore 降序。negative 默认过滤。"""
        session = self.SessionLocal()
        try:
            dbQuery = session.query(OpsExperiencePackOrm).filter(
                OpsExperiencePackOrm.status == "enabled"
            )
            if not includeNegative:
                dbQuery = dbQuery.filter(OpsExperiencePackOrm.category != "negative")
            elif category is None:
                dbQuery = dbQuery.filter(OpsExperiencePackOrm.category == "negative")
            if query:
                # 多关键词分词 AND 匹配（"nginx 502 证书" 可命中 "Nginx SSL 证书过期导致 502"）
                for token in [token for token in query.split() if token]:
                    like = f"%{token}%"
                    dbQuery = dbQuery.filter(
                        OpsExperiencePackOrm.title.like(like)
                        | OpsExperiencePackOrm.tags.like(like)
                        | OpsExperiencePackOrm.deploymentDoc.like(like)
                        | OpsExperiencePackOrm.pitfalls.like(like)
                    )
            if category and (includeNegative or category != "negative"):
                dbQuery = dbQuery.filter(OpsExperiencePackOrm.category == category)
            rows = dbQuery.order_by(
                OpsExperiencePackOrm.qualityScore.desc(),
                OpsExperiencePackOrm.id.desc(),
            ).limit(max(1, min(int(limit), 50))).all()
            result = [self._toObj(row) for row in rows]
            for row in rows:
                session.expunge(row)
            return result
        finally:
            session.close()

    def updatePack(self, packId: int, fields: dict) -> dict | None:
        """更新经验包（人工修改入口），version + 1。fields 为字段白名单字典。"""
        allowed = {
            "title", "category", "osType", "tags", "deploymentDoc",
            "stages", "pitfalls", "earlyWarnings", "riskLevel", "status",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return self.getPack(packId)
        session = self.SessionLocal()
        try:
            row = session.query(OpsExperiencePackOrm).filter(
                OpsExperiencePackOrm.id == packId
            ).one_or_none()
            if row is None:
                return None
            for key, value in updates.items():
                if key in {"tags", "stages", "pitfalls", "earlyWarnings"}:
                    setattr(row, key, json.dumps(value or [], ensure_ascii=False, default=str))
                else:
                    setattr(row, key, value)
            row.version = (row.version or 1) + 1
            session.commit()
            result = self._toObj(row)
            session.expunge(row)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deletePack(self, packId: int) -> bool:
        session = self.SessionLocal()
        try:
            row = session.query(OpsExperiencePackOrm).filter(
                OpsExperiencePackOrm.id == packId
            ).one_or_none()
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ── 反馈统计 ──────────────────────────────────────────────────────────

    @staticmethod
    def _recalcQualityScore(hitCount: int, usefulCount: int, uselessCount: int) -> int:
        # 建议公式：100 + useful*5 - useless*10 + hit*1，下限 0
        return max(0, 100 + usefulCount * 5 - uselessCount * 10 + hitCount * 1)

    def feedback(self, packId: int, action: str) -> dict | None:
        session = self.SessionLocal()
        try:
            row = session.query(OpsExperiencePackOrm).filter(
                OpsExperiencePackOrm.id == packId
            ).one_or_none()
            if row is None:
                return None
            if action == "hit":
                row.hitCount = (row.hitCount or 0) + 1
            elif action == "useful":
                row.usefulCount = (row.usefulCount or 0) + 1
            elif action == "useless":
                row.uselessCount = (row.uselessCount or 0) + 1
            else:
                raise ValueError(f"unknown feedback action: {action}")
            row.qualityScore = self._recalcQualityScore(
                row.hitCount, row.usefulCount, row.uselessCount
            )
            session.commit()
            result = self._toObj(row)
            session.expunge(row)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def incrementHit(self, packId: int) -> None:
        self.feedback(packId, "hit")

    def knowledgeSummaryRows(self, limit: int = 20) -> list[dict]:
        """启用中的经验包，按 qualityScore 降序取前 N 条（供 Prompt 摘要注入）。"""
        session = self.SessionLocal()
        try:
            rows = session.query(OpsExperiencePackOrm).filter(
                OpsExperiencePackOrm.status == "enabled"
            ).order_by(
                OpsExperiencePackOrm.qualityScore.desc(),
                OpsExperiencePackOrm.id.desc(),
            ).limit(max(1, min(int(limit), 50))).all()
            result = [self._toObj(row) for row in rows]
            for row in rows:
                session.expunge(row)
            return result
        finally:
            session.close()

    # ── 附件 ──────────────────────────────────────────────────────────────

    def createAttachment(
        self,
        packId: int,
        filename: str,
        fileType: str,
        storagePath: str,
        sha256: str,
        size: int,
        arch: str = "通用",
        osType: str = "通用",
    ) -> dict:
        session = self.SessionLocal()
        try:
            row = OpsExperienceAttachmentOrm(
                packId=packId,
                filename=filename,
                fileType=fileType,
                storagePath=storagePath,
                sha256=sha256,
                size=size,
                arch=arch,
                osType=osType,
            )
            session.add(row)
            session.commit()
            result = self._attachmentToObj(row)
            session.expunge(row)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def listAttachments(self, packId: int) -> list[dict]:
        session = self.SessionLocal()
        try:
            rows = session.query(OpsExperienceAttachmentOrm).filter(
                OpsExperienceAttachmentOrm.packId == packId
            ).order_by(OpsExperienceAttachmentOrm.id.asc()).all()
            result = [self._attachmentToObj(row) for row in rows]
            for row in rows:
                session.expunge(row)
            return result
        finally:
            session.close()

    def getAttachment(self, attachmentId: int) -> dict | None:
        session = self.SessionLocal()
        try:
            row = session.query(OpsExperienceAttachmentOrm).filter(
                OpsExperienceAttachmentOrm.id == attachmentId
            ).one_or_none()
            if row is None:
                return None
            result = self._attachmentToObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def findAttachmentBySha256(self, sha256: str) -> dict | None:
        """按内容哈希查附件（导入去重：同 sha256 的附件文件只落盘一次）。"""
        session = self.SessionLocal()
        try:
            row = session.query(OpsExperienceAttachmentOrm).filter(
                OpsExperienceAttachmentOrm.sha256 == sha256
            ).first()
            if row is None:
                return None
            result = self._attachmentToObj(row)
            session.expunge(row)
            return result
        finally:
            session.close()

    def deleteAttachmentsByPack(self, packId: int) -> list[dict]:
        """删除某包的全部附件记录，返回删除前的记录（供物理文件清理）。"""
        session = self.SessionLocal()
        try:
            rows = session.query(OpsExperienceAttachmentOrm).filter(
                OpsExperienceAttachmentOrm.packId == packId
            ).all()
            result = [self._attachmentToObj(row) for row in rows]
            for row in rows:
                session.delete(row)
            session.commit()
            return result
        finally:
            session.close()
