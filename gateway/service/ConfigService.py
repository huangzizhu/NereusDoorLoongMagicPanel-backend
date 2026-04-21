from typing import List

from Exception.InvalidParamException import InvalidParamException
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.ConfigDaoInterface import ConfigDaoInterface
from gateway.dao.ConfigDaoOrm import ConfigDaoOrm
from pojo.ApiKey import ApiCredentialCreate, ApiCredentialResponse, ApiCredentialOrm2pydantic, ApiCredentialUpdate
from Exception.DataBaseException import DataBaseException
from pojo.Common import ListResponse


class ConfigService(Singleton):
    @singletonInit
    def __init__(self):
        self.configDaoOrm: ConfigDaoInterface = ConfigDaoOrm()
    def _maskString(self, string: str) -> str:
        # 如果字符串长度小于 6，则直接返回原字符串
        if len(string) < 6:
            return string

        # 保留前 3 个和后 3 个字符，中间部分替换成 *
        return string[:3] + '*' * (len(string) - 6) + string[-3:]



    def addApiKey(self, apiCredentialCreate: ApiCredentialCreate) -> ApiCredentialResponse:
        try:
            id: int = self.configDaoOrm.addApiKey(apiCredentialCreate)
            if not id:
                raise DataBaseException(userMessage="新增apiKey失败，请重试")
            apikey: ApiCredentialOrm2pydantic = self.configDaoOrm.getApiKeyById(id)
            if not apikey:
                raise DataBaseException(userMessage="新增apiKey失败，请重试")
            data = apikey.model_dump()
            data['maskedKey'] = self._maskString(data['apiKey'])
            data.pop('apiKey')
            return ApiCredentialResponse.model_validate(data)
        except DataBaseException:
            raise
        except Exception as e:
            raise DataBaseException(innerMessage=str(e),userMessage="数据库操作错误，请重试或联系管理员",cause=e)

    def updateApiKey(self, apiCredentialUpdate: ApiCredentialUpdate) -> ApiCredentialResponse:
        try:
            rowCount: int = self.configDaoOrm.updateApiKey(apiCredentialUpdate)
            if not rowCount:
                raise InvalidParamException(userMessage=f"更新失败，不存在id为{apiCredentialUpdate.credentialId}的apikey项")
            apikey: ApiCredentialOrm2pydantic = self.configDaoOrm.getApiKeyById(apiCredentialUpdate.credentialId)
            if not apikey:
                raise DataBaseException(userMessage="修改apiKey失败，请重试")
            data = apikey.model_dump()
            data['maskedKey'] = self._maskString(data['apiKey'])
            data.pop('apiKey')
            return ApiCredentialResponse.model_validate(data)
        except DataBaseException:
            raise
        except InvalidParamException:
            raise
        except Exception as e:
            raise DataBaseException(innerMessage=str(e), userMessage="数据库操作错误，请重试或联系管理员", cause=e)

    def getAllApiKeys(self) -> ListResponse:
        try:
            apikeys: List[ApiCredentialOrm2pydantic] = self.configDaoOrm.getAllApiKeys()
            res: List[ApiCredentialResponse] = []
            for apikey in apikeys:
                data = apikey.model_dump()
                data['maskedKey'] = self._maskString(data['apiKey'])
                data.pop('apiKey')
                res.append(ApiCredentialResponse.model_validate(data))
            return ListResponse(total=len(res), items=res)
        except Exception as e:
            raise DataBaseException(innerMessage=str(e), userMessage="数据库操作错误，请重试或联系管理员", cause=e)

    def deleteApiKey(self, credentialId: int):
        try:
            rowCount: int = self.configDaoOrm.deleteApiKey(credentialId)
            if not rowCount:
                raise InvalidParamException(userMessage=f"删除失败，不存在id为{credentialId}的apikey项")
        except InvalidParamException:
            raise
        except Exception as e:
            raise DataBaseException(innerMessage=str(e), userMessage="数据库操作错误，请重试或联系管理员", cause=e)






