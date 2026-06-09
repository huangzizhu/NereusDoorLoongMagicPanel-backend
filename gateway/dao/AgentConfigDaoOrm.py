from datetime import datetime
from typing import Optional

from gateway.Singleton import Singleton, singletonInit
from gateway.orm.AgentLlmProfileOrm import AgentLlmProfileOrm
from gateway.orm.ApiKeyOrm import ApiCredentialOrm
from gateway.orm.OrmEngine import OrmEngine
from pojo.Agent import AgentLlmProfileCreate, AgentLlmProfileUpdate


class AgentConfigDaoOrm(Singleton):
    @singletonInit
    def __init__(self):
        self.engine = OrmEngine()
        self.SessionLocal = self.engine.createSessionFactory()
        self.engine.getBase().metadata.create_all(self.engine.engine)

    def addProfile(self, profile: AgentLlmProfileCreate) -> int:
        session = self.SessionLocal()
        try:
            data = profile.model_dump(exclude_none=True)
            if data.get("isDefault"):
                session.query(AgentLlmProfileOrm).update({"isDefault": False})
            orm = AgentLlmProfileOrm(**data)
            session.add(orm)
            session.commit()
            return orm.profileId
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def updateProfile(self, profileId: int, update: AgentLlmProfileUpdate) -> int:
        session = self.SessionLocal()
        try:
            data = update.model_dump(exclude_unset=True, exclude_none=True)
            if not data:
                return 0
            data["updateTime"] = datetime.now()
            if data.get("isDefault"):
                session.query(AgentLlmProfileOrm).filter(
                    AgentLlmProfileOrm.profileId != profileId
                ).update({"isDefault": False})
            rowCount = session.query(AgentLlmProfileOrm).filter(
                AgentLlmProfileOrm.profileId == profileId
            ).update(data)
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def setDefaultProfile(self, profileId: int) -> int:
        session = self.SessionLocal()
        try:
            target = session.query(AgentLlmProfileOrm).filter(
                AgentLlmProfileOrm.profileId == profileId,
                AgentLlmProfileOrm.isActive == True,  # noqa: E712
            ).one_or_none()
            if target is None:
                return 0
            session.query(AgentLlmProfileOrm).update({"isDefault": False})
            target.isDefault = True
            target.updateTime = datetime.now()
            session.commit()
            return 1
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deleteProfile(self, profileId: int) -> int:
        session = self.SessionLocal()
        try:
            rowCount = session.query(AgentLlmProfileOrm).filter(
                AgentLlmProfileOrm.profileId == profileId
            ).delete()
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getProfileById(self, profileId: int) -> Optional[AgentLlmProfileOrm]:
        session = self.SessionLocal()
        try:
            orm = session.query(AgentLlmProfileOrm).filter(
                AgentLlmProfileOrm.profileId == profileId
            ).one_or_none()
            if orm is None:
                return None
            session.expunge(orm)
            return orm
        finally:
            session.close()

    def getDefaultProfile(self) -> Optional[AgentLlmProfileOrm]:
        session = self.SessionLocal()
        try:
            orm = session.query(AgentLlmProfileOrm).filter(
                AgentLlmProfileOrm.isDefault == True,  # noqa: E712
                AgentLlmProfileOrm.isActive == True,  # noqa: E712
            ).order_by(AgentLlmProfileOrm.profileId.desc()).first()
            if orm is None:
                return None
            session.expunge(orm)
            return orm
        finally:
            session.close()

    def getProfiles(self) -> list[AgentLlmProfileOrm]:
        session = self.SessionLocal()
        try:
            orms = session.query(AgentLlmProfileOrm).order_by(
                AgentLlmProfileOrm.isDefault.desc(),
                AgentLlmProfileOrm.profileId.desc(),
            ).all()
            for orm in orms:
                session.expunge(orm)
            return orms
        finally:
            session.close()

    def getCredentialById(self, credentialId: int) -> Optional[ApiCredentialOrm]:
        session = self.SessionLocal()
        try:
            orm = session.query(ApiCredentialOrm).filter(
                ApiCredentialOrm.credentialId == credentialId
            ).one_or_none()
            if orm is None:
                return None
            session.expunge(orm)
            return orm
        finally:
            session.close()

    def getCredentialName(self, credentialId: int | None) -> str | None:
        if credentialId is None:
            return None
        session = self.SessionLocal()
        try:
            row = session.query(ApiCredentialOrm.name).filter(
                ApiCredentialOrm.credentialId == credentialId
            ).one_or_none()
            return row[0] if row else None
        finally:
            session.close()
