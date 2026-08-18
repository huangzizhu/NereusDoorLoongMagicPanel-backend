from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from gateway.orm.OrmEngine import OrmEngine


class OpsExperiencePackOrm(OrmEngine().getBase()):
    """运维经验包主表：元数据 + 正文（deploymentDoc）+ 结构化附件（stages/pitfalls/earlyWarnings）。

    表由 OrmEngine().ensureDbInit() 的 create_all 自动创建，无需手工建表。
    """

    __tablename__ = "ops_experience_packs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(32), nullable=False, default="deployment", index=True)
    osType = Column(String(64), nullable=False, default="通用")
    tags = Column(Text, nullable=True)          # JSON 数组
    deploymentDoc = Column(Text, nullable=False)  # Markdown 正文（主体）
    stages = Column(Text, nullable=True)        # JSON 数组
    pitfalls = Column(Text, nullable=True)      # JSON 数组
    earlyWarnings = Column(Text, nullable=True)  # JSON 数组
    riskLevel = Column(String(16), nullable=False, default="medium")
    status = Column(String(16), nullable=False, default="enabled", index=True)
    source = Column(String(16), nullable=False, default="human", index=True)
    version = Column(Integer, nullable=False, default=1)
    sourceSessionId = Column(String(64), nullable=True, index=True)
    hitCount = Column(Integer, nullable=False, default=0)
    usefulCount = Column(Integer, nullable=False, default=0)
    uselessCount = Column(Integer, nullable=False, default=0)
    qualityScore = Column(Integer, nullable=False, default=100, index=True)
    createdAt = Column(DateTime, default=datetime.now, index=True)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OpsExperienceAttachmentOrm(OrmEngine().getBase()):
    """经验包附件指针表：可执行附件落盘文件系统，数据库只存指针（存储/哈希/审计字段）。"""

    __tablename__ = "ops_experience_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    packId = Column(
        Integer,
        ForeignKey("ops_experience_packs.id"),
        nullable=False,
        index=True,
    )
    filename = Column(String(255), nullable=False)
    fileType = Column(String(16), nullable=False, default="doc")  # script | binary | doc | archive
    storagePath = Column(String(512), nullable=False)  # 相对路径 runtime/ops-experience/attachments/{packId}/{filename}
    sha256 = Column(String(64), nullable=False, index=True)  # 导入去重 + 完整性校验 + 审计溯源
    size = Column(Integer, nullable=False, default=0)
    arch = Column(String(32), nullable=False, default="通用")  # x86_64 | loongarch64 | 通用
    osType = Column(String(64), nullable=False, default="通用")
    createdAt = Column(DateTime, default=datetime.now)
