from gateway.Singleton import singletonInit
from gateway.dao.ConfigDaoInterface import ConfigDaoInterface
from gateway.orm.OrmEngine import OrmEngine
from pojo.ApiKey import ApiCredentialCreate, ApiCredentialOrm2pydantic, ApiCredentialUpdate
from gateway.orm.ApiKeyOrm import ApiCredentialOrm
from typing import List

class ConfigDaoOrm(ConfigDaoInterface):
    @singletonInit
    def __init__(self):
        super().__init__('ConfigDaoOrm')
        self.engine = OrmEngine()
        # 保存 Session 工厂
        self.SessionLocal = self.engine.createSessionFactory()

    def addApiKey(self, apiCredentialCreate: ApiCredentialCreate) -> int:
        session = self.SessionLocal()
        try:
            orm = ApiCredentialOrm(**apiCredentialCreate.model_dump(exclude_none=True, exclude_unset=True))
            session.add(orm)
            session.commit()
            return orm.credentialId
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getApiKeyById(self, id: int) -> ApiCredentialOrm2pydantic:
        session = self.SessionLocal()
        try:
            orm: ApiCredentialOrm = session.query(ApiCredentialOrm).filter(ApiCredentialOrm.credentialId == id).one_or_none()
            return ApiCredentialOrm2pydantic.model_validate(orm)
        except Exception:
            raise
        finally:
            session.close()

    def updateApiKey(self, apiCredentialUpdate: ApiCredentialUpdate) -> int:
        session = self.SessionLocal()
        try:
            rowCount: int = (session.query(ApiCredentialOrm)
                             .filter(ApiCredentialOrm.credentialId == apiCredentialUpdate.credentialId)
                             .update(apiCredentialUpdate.model_dump(exclude_none=True, exclude_unset=True)))
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def getAllApiKeys(self) -> List[ApiCredentialOrm2pydantic]:
        session = self.SessionLocal()
        try:
            orms: List[ApiCredentialOrm] = session.query(ApiCredentialOrm).all()
            return [ApiCredentialOrm2pydantic.model_validate(orm) for orm in orms]
        except Exception:
            raise
        finally:
            session.close()

    def deleteApiKey(self, credentialId: int)-> int:
        session = self.SessionLocal()
        try:
            rowCount: int = session.query(ApiCredentialOrm).filter(ApiCredentialOrm.credentialId == credentialId).delete()
            session.commit()
            return rowCount
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

