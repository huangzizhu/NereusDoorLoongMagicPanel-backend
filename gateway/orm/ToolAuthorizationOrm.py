from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from gateway.orm.OrmEngine import OrmEngine

# 工具授权请求状态
AUTH_REQ_STATUS_PENDING = "pending"
AUTH_REQ_STATUS_APPROVED = "approved"
AUTH_REQ_STATUS_REJECTED = "rejected"
AUTH_REQ_STATUS_EXPIRED = "expired"

# 授权请求来源类型
AUTH_REQ_SOURCE_SCHEDULED = "scheduled"
AUTH_REQ_SOURCE_INSPECTION = "inspection"
AUTH_REQ_SOURCE_MANUAL = "manual"


class ToolAuthorizationRequestOrm(OrmEngine().getBase()):
    """定时任务 / 自动巡检运行中，Agent 提出的工具授权请求。

    生命周期：
      - agent 在预授权未覆盖时提交请求（pending，绑定一次性审批码）
      - 管理员通过 `sudo nereus approve <CODE>`（或 /admin/elevation/approve）审批
      - 批准后：签发 JIT token（本次有效），并把授权片段写回来源策略
        （定时任务 approvalPolicy / 巡检策略），后续运行自动放行
    """

    __tablename__ = "tool_authorization_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), nullable=False, unique=True, index=True)
    sessionId = Column(String(64), nullable=False, index=True)
    sourceType = Column(String(32), nullable=False, default=AUTH_REQ_SOURCE_MANUAL, index=True)
    taskId = Column(Integer, nullable=True, index=True)
    toolName = Column(String(128), nullable=False)
    argsJson = Column(Text, nullable=True)
    pathsJson = Column(Text, nullable=True)
    commandLine = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    policyReason = Column(Text, nullable=True)
    riskLevel = Column(String(32), nullable=True)
    status = Column(String(16), nullable=False, default=AUTH_REQ_STATUS_PENDING, index=True)
    ttlSeconds = Column(Integer, nullable=False, default=3600)
    maxRuns = Column(Integer, nullable=False, default=100)
    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    approvedAt = Column(DateTime, nullable=True)
    approvedBy = Column(String(128), nullable=True)
    rejectReason = Column(Text, nullable=True)
    tokenId = Column(String(64), nullable=True)
    grantJson = Column(Text, nullable=True)
