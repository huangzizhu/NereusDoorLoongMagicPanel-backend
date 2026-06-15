import json
from datetime import datetime
from types import SimpleNamespace
from typing import Optional

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentLlmProfileOrm import AgentLlmProfileOrm  # noqa: F401
from gateway.orm.AgentMessageOrm import AgentMessageOrm
from gateway.orm.AgentSessionOrm import AgentSessionOrm
from gateway.orm.AgentTokenUsageOrm import AgentTokenUsageOrm  # noqa: F401
from gateway.orm.OrmEngine import OrmEngine
from pojo.Agent import AgentSessionCreate


class AgentSessionDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    def createSession(self, sessionId: str, userId: int,
                      request: AgentSessionCreate) -> SimpleNamespace:
        """创建会话，返回 SimpleNamespace（支持属性访问 + Pydantic model_validate）。"""
        session = self.SessionLocal()
        try:
            data = request.model_dump(exclude_none=True)
            mcpServers = data.pop("mcpServers", None)
            orm = AgentSessionOrm(
                sessionId=sessionId,
                userId=userId,
                mcpServersJson=json.dumps(mcpServers, ensure_ascii=False) if mcpServers else None,
                **data,
            )
            session.add(orm)
            session.commit()
            result = SimpleNamespace(**self._sessionOrmToDict(orm))
            session.expunge(orm)
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _sessionOrmToDict(orm: AgentSessionOrm) -> dict:
        """在 session 活动期内提取 ORM 所有字段为普通 dict。

        Pydantic v2 的 model_validate(from_attributes=True) 在 ORM detached 后会
        触发 DetachedInstanceError，必须在 session close 前完成数据提取。
        """
        from sqlalchemy.orm import class_mapper
        d = {}
        for col in class_mapper(AgentSessionOrm).columns:
            d[col.key] = getattr(orm, col.key)
        # @property 字段
        d["mcpServers"] = orm.mcpServers
        return d

    def getSession(self, sessionId: str,
                   userId: int | None = None) -> Optional[dict]:
        """获取会话。

        Returns:
            SimpleNamespace — 支持属性访问 (session.sessionId) 和 Pydantic model_validate。
            避免返回 detached ORM 导致的 DetachedInstanceError。
        """
        session = self.SessionLocal()
        try:
            query = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId
            )
            if userId is not None:
                query = query.filter(AgentSessionOrm.userId == userId)
            orm = query.one_or_none()
            if orm is None:
                return None
            data = self._sessionOrmToDict(orm)
            session.expunge(orm)
            return SimpleNamespace(**data)
        finally:
            session.close()

    def listSessions(self, userId: int, page: int, pageSize: int,
                     status: str | None = None,
                     keyword: str | None = None) -> tuple[int, list[dict]]:
        session = self.SessionLocal()
        try:
            query = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.userId == userId
            )
            if status:
                query = query.filter(AgentSessionOrm.status == status)
            if keyword:
                query = query.filter(AgentSessionOrm.title.like(f"%{keyword}%"))
            total = query.count()
            rows = query.order_by(AgentSessionOrm.updatedAt.desc()).offset(
                max(page - 1, 0) * pageSize
            ).limit(pageSize).all()
            result = [SimpleNamespace(**self._sessionOrmToDict(r)) for r in rows]
            for row in rows:
                session.expunge(row)
            return total, result
        finally:
            session.close()

    def updateStatus(self, sessionId: str, status: str,
                     lastError: str | None = None,
                     finished: bool = False) -> int:
        session = self.SessionLocal()
        try:
            data = {"status": status, "updatedAt": datetime.now()}
            if lastError is not None:
                data["lastError"] = lastError
            if finished:
                data["finishedAt"] = datetime.now()
            rowCount = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId
            ).update(data)
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def updateMode(self, sessionId: str, mode: str) -> int:
        """更新会话的运行模式。"""
        from datetime import datetime
        session = self.SessionLocal()
        try:
            rowCount = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId,
            ).update({"mode": mode, "updatedAt": datetime.now()})
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getSessionStatus(self, sessionId: str) -> str | None:
        """获取会话当前状态。"""
        session = self.SessionLocal()
        try:
            row = session.query(AgentSessionOrm.status).filter(
                AgentSessionOrm.sessionId == sessionId
            ).first()
            return row[0] if row else None
        finally:
            session.close()

    def updatePendingApproval(self, sessionId: str,
                               approvalData: dict | None) -> int:
        """持久化最后一次 APPROVAL_REQUIRED 事件数据。

        Args:
            sessionId: 会话 ID
            approvalData: 完整的事件 payload，或 None 表示清除

        Returns:
            影响行数
        """
        session = self.SessionLocal()
        try:
            value = json.dumps(approvalData, ensure_ascii=False) if approvalData else None
            rowCount = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId
            ).update({
                "pendingApproval": value,
                "updatedAt": datetime.now(),
            })
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def clearPendingApproval(self, sessionId: str) -> int:
        """清除待审批事件记录。"""
        return self.updatePendingApproval(sessionId, None)

    def getPendingApproval(self, sessionId: str) -> dict | None:
        """读取持久化的待审批事件。"""
        session = self.SessionLocal()
        try:
            row = session.query(AgentSessionOrm.pendingApproval).filter(
                AgentSessionOrm.sessionId == sessionId
            ).first()
            if not row or not row[0]:
                return None
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return None
        finally:
            session.close()

    def updateSessionTitle(self, sessionId: str, title: str) -> int:
        """更新会话标题。"""
        session = self.SessionLocal()
        try:
            rowCount = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId
            ).update({"title": title, "updatedAt": datetime.now()})
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deleteSession(self, sessionId: str, userId: int) -> int:
        session = self.SessionLocal()
        try:
            target = session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId,
                AgentSessionOrm.userId == userId,
            ).one_or_none()
            if target is None:
                return 0
            # 级联删除消息、token用量、追踪日志
            session.query(AgentMessageOrm).filter(
                AgentMessageOrm.sessionId == sessionId
            ).delete()
            session.query(AgentTokenUsageOrm).filter(
                AgentTokenUsageOrm.sessionId == sessionId
            ).delete()
            session.delete(target)
            session.commit()
            return 1
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getNextRoundIndex(self, sessionId: str) -> int:
        session = self.SessionLocal()
        try:
            row = session.query(AgentMessageOrm.roundIndex).filter(
                AgentMessageOrm.sessionId == sessionId
            ).order_by(AgentMessageOrm.roundIndex.desc()).first()
            return (row[0] + 1) if row else 1
        finally:
            session.close()

    def addMessage(self, sessionId: str, role: str,
                   content: str | None = None,
                   traceId: str | None = None,
                   roundIndex: int = 0,
                   toolCallId: str | None = None,
                   metadata: dict | None = None) -> int:
        """添加一条消息，返回 messageId。

        Args:
            sessionId: 会话ID
            role: user / assistant / tool
            content: 消息内容（assistant 仅含 tool_calls 时可为 None）
            traceId: 追踪ID
            roundIndex: 轮次
            toolCallId: tool 角色时的 tool_call_id
            metadata: JSON 元数据（assistant 的 tool_calls 数组、tool 的 tool_name 等）

        Returns:
            messageId (int) — 不返回 ORM 对象以避免 detached lazy-load 问题
        """
        session = self.SessionLocal()
        try:
            orm = AgentMessageOrm(
                sessionId=sessionId,
                role=role,
                content=content,
                toolCallId=toolCallId,
                traceId=traceId,
                roundIndex=roundIndex,
                metadataJson=json.dumps(metadata, ensure_ascii=False) if metadata else None,
            )
            session.add(orm)
            session.query(AgentSessionOrm).filter(
                AgentSessionOrm.sessionId == sessionId
            ).update({"updatedAt": datetime.now()})
            session.commit()
            # 只返回 messageId，不返回 ORM 对象
            mid = orm.messageId
            session.expunge(orm)
            return mid
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def updateToolResponse(self, sessionId: str, toolCallId: str,
                            newContent: str) -> int:
        """更新指定 tool_call_id 的 tool 消息内容。
        
        用于 plan 审批后更新 tool 响应文本。
        """
        from datetime import datetime
        session = self.SessionLocal()
        try:
            rowCount = session.query(AgentMessageOrm).filter(
                AgentMessageOrm.sessionId == sessionId,
                AgentMessageOrm.role == "tool",
                AgentMessageOrm.toolCallId == toolCallId,
            ).update({
                "content": newContent,
                "metadataJson": None,
            })
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def updateMessageTrace(self, messageId: int, traceId: str) -> int:
        session = self.SessionLocal()
        try:
            rowCount = session.query(AgentMessageOrm).filter(
                AgentMessageOrm.messageId == messageId
            ).update({"traceId": traceId})
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def listMessages(self, sessionId: str) -> list[AgentMessageOrm]:
        session = self.SessionLocal()
        try:
            rows = session.query(AgentMessageOrm).filter(
                AgentMessageOrm.sessionId == sessionId
            ).order_by(AgentMessageOrm.roundIndex.asc(),
                       AgentMessageOrm.messageId.asc()).all()
            for row in rows:
                session.expunge(row)
            return rows
        finally:
            session.close()

    def getRecentConversationHistory(self, sessionId: str,
                                     limit: int = 0) -> list[dict]:
        """获取全部对话历史（OpenAI 消息格式，含工具调用链）。

        此方法返回 session 的全量消息（不再截断），
        由上游 compressHistory() 按 token 预算压缩。
        """
        session = self.SessionLocal()
        try:
            rows = session.query(AgentMessageOrm).filter(
                AgentMessageOrm.sessionId == sessionId,
            ).order_by(AgentMessageOrm.messageId.asc()).all()

            result: list[dict] = []
            for row in rows:
                msg: dict = {"role": row.role}

                if row.role == "assistant":
                    # 尝试从 metadata 中恢复 tool_calls
                    meta = self._parseMetadata(row.metadataJson)
                    toolCalls = meta.get("tool_calls") if isinstance(meta, dict) else None
                    if row.content:
                        msg["content"] = row.content
                        if toolCalls:
                            msg["tool_calls"] = toolCalls
                    elif toolCalls:
                        msg["content"] = None
                        msg["tool_calls"] = toolCalls
                    else:
                        msg["content"] = row.content or ""

                elif row.role == "tool":
                    msg["tool_call_id"] = row.toolCallId or ""
                    msg["content"] = row.content or ""

                else:
                    msg["content"] = row.content or ""

                result.append(msg)

            return result
        finally:
            session.close()

    @staticmethod
    def _parseMetadata(metadataJson: str | None) -> dict:
        if not metadataJson:
            return {}
        try:
            return json.loads(metadataJson)
        except (json.JSONDecodeError, TypeError):
            return {}
