from fastapi import APIRouter

from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from pojo.Common import ListResponse
from gateway.service.ConfigService import ConfigService
from pojo.ApiKey import ApiCredentialCreate, ApiCredentialResponse, ApiCredentialUpdate
from gateway.Response import ResponseModel,Response

class ConfigController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/config", tags=["设置管理"])
        self.configService: ConfigService = ConfigService()
        super().__init__("configController", self.router)
        self.routerSetup()

    def routerSetup(self):

        @self.router.post("/apikey")
        def addApiKey(apiCredentialCreate:ApiCredentialCreate):
            apikey: ApiCredentialResponse = self.configService.addApiKey(apiCredentialCreate)
            return Response.success(apikey)

        @self.router.put("/apikey")
        def updateApiKey(apiCredentialUpdate:ApiCredentialUpdate):
            apiKey: ApiCredentialResponse = self.configService.updateApiKey(apiCredentialUpdate)
            return Response.success(apiKey)

        @self.router.get("/apikey")
        def getAllApiKeys():
            apiKeys: ListResponse =  self.configService.getAllApiKeys()
            return Response.success(apiKeys)

        @self.router.delete("/apikey/{credentialId}")
        def deleteApiKey(credentialId: int):
            self.configService.deleteApiKey(credentialId)
            return Response.success()
        