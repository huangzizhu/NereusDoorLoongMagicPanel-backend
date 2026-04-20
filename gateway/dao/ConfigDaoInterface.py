from abc import abstractmethod
from typing import List

from gateway.Singleton import Singleton
from pojo.ApiKey import ApiCredentialCreate, ApiCredentialOrm2pydantic, ApiCredentialUpdate


class ConfigDaoInterface(Singleton):
    def __init__(self,name: str):
        self.name = name

    @abstractmethod
    def addApiKey(self, apiCredentialCreate: ApiCredentialCreate) -> int:
        pass
    @abstractmethod
    def getApiKeyById(self, id: int) -> ApiCredentialOrm2pydantic:
        pass
    @abstractmethod
    def updateApiKey(self, apiCredentialUpdate: ApiCredentialUpdate) -> int:
        pass

    def getAllApiKeys(self)->  List[ApiCredentialOrm2pydantic]:
        pass

    def deleteApiKey(self, credentialId: int)-> int:
        pass
