import json
import time
import urllib.error
import urllib.request
from typing import Optional

from Exception.DataBaseException import DataBaseException
from Exception.InvalidParamException import InvalidParamException
from agent.config_envs.loader import loadConfig
from agent.llm_providers.factory import createProvider
from agent.llm_structured import callStructuredLLM, parseJsonObject
from agent.prompt_loader import loadPrompt
from agent.shared.types import AgentConfig
from gateway.Singleton import Singleton, singletonInit
from gateway.dao.AgentConfigDaoOrm import AgentConfigDaoOrm
from pojo.Agent import (
    AgentLlmCredentialModelsResponse,
    AgentLlmModelInfo,
    AgentLlmProfileBatchCreate,
    AgentLlmProfileCreate,
    AgentLlmProfileOrm2Pydantic,
    AgentLlmProfileResponse,
    AgentLlmProfileTestResponse,
    AgentLlmProfileUpdate,
)
from pojo.Common import ListResponse


def _parseConnectivityResponse(raw: str) -> str:
    """校验模型连通性测试的结构化响应，并返回兼容的 OK 文本。"""
    data = parseJsonObject(raw)
    if data.get("status") != "ok":
        raise ValueError("status 必须为 ok")
    return "OK"


class AgentLlmProfileService(Singleton):
    MAX_LLM_TOKENS = 393216
    MAX_CONTEXT_WINDOW = 10485760

    @singletonInit
    def __init__(self):
        self.dao = AgentConfigDaoOrm()

    def createProfile(self, request: AgentLlmProfileCreate) -> AgentLlmProfileResponse:
        try:
            profileId = self.dao.addProfile(request)
            profile = self.dao.getProfileById(profileId)
            if profile is None:
                raise DataBaseException(userMessage="新增 LLM Profile 失败")
            return self._toResponse(profile)
        except DataBaseException:
            raise
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def createProfilesBatch(self, request: AgentLlmProfileBatchCreate) -> ListResponse:
        try:
            credential = self.dao.getCredentialById(request.credentialId)
            if credential is None:
                raise InvalidParamException(userMessage=f"不存在 id 为 {request.credentialId} 的凭证")

            models = self._normalizeModels(request.models)
            if not models:
                raise InvalidParamException(userMessage="models 不能为空")

            items: list[AgentLlmProfileResponse] = []
            for index, model in enumerate(models):
                name = self._buildProfileName(request.namePrefix, model)
                create = AgentLlmProfileCreate(
                    name=name,
                    credentialId=request.credentialId,
                    model=model,
                    maxTokens=request.maxTokens,
                    contextWindow=request.contextWindow,
                    temperature=request.temperature,
                    retryCount=request.retryCount,
                    retryDelay=request.retryDelay,
                    isDefault=request.isDefaultFirst and index == 0,
                    isActive=request.isActive,
                    description=request.description,
                )
                items.append(self.createProfile(create))
            return ListResponse(total=len(items), items=items)
        except (DataBaseException, InvalidParamException):
            raise
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def updateProfile(self, profileId: int,
                      request: AgentLlmProfileUpdate) -> AgentLlmProfileResponse:
        try:
            rowCount = self.dao.updateProfile(profileId, request)
            if not rowCount:
                raise InvalidParamException(userMessage=f"不存在 id 为 {profileId} 的 LLM Profile")
            profile = self.dao.getProfileById(profileId)
            if profile is None:
                raise DataBaseException(userMessage="更新 LLM Profile 失败")
            return self._toResponse(profile)
        except (DataBaseException, InvalidParamException):
            raise
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def listProfiles(self) -> ListResponse:
        try:
            items = [self._toResponse(profile) for profile in self.dao.getProfiles()]
            return ListResponse(total=len(items), items=items)
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def getDefaultProfile(self) -> Optional[AgentLlmProfileResponse]:
        try:
            profile = self.dao.getDefaultProfile()
            return self._toResponse(profile) if profile is not None else None
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def setDefaultProfile(self, profileId: int) -> AgentLlmProfileResponse:
        try:
            rowCount = self.dao.setDefaultProfile(profileId)
            if not rowCount:
                raise InvalidParamException(userMessage=f"不存在可用的 id 为 {profileId} 的 LLM Profile")
            profile = self.dao.getProfileById(profileId)
            if profile is None:
                raise DataBaseException(userMessage="设置默认 LLM Profile 失败")
            return self._toResponse(profile)
        except (DataBaseException, InvalidParamException):
            raise
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def deleteProfile(self, profileId: int) -> None:
        try:
            rowCount = self.dao.deleteProfile(profileId)
            if not rowCount:
                raise InvalidParamException(userMessage=f"不存在 id 为 {profileId} 的 LLM Profile")
        except InvalidParamException:
            raise
        except Exception as exc:
            raise DataBaseException(innerMessage=str(exc), userMessage="数据库操作错误，请重试或联系管理员", cause=exc)

    def getCredentialModels(self, credentialId: int) -> AgentLlmCredentialModelsResponse:
        credential = self.dao.getCredentialById(credentialId)
        if credential is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {credentialId} 的凭证")
        if not credential.isActive:
            raise InvalidParamException(userMessage="凭证未启用，无法拉取模型列表")
        if not credential.baseUrl:
            raise InvalidParamException(userMessage="凭证 baseUrl 为空，无法拉取模型列表")

        errors: list[str] = []
        for url in self._candidateModelUrls(credential.baseUrl):
            try:
                models = self._fetchModels(url, credential.apiKey)
                return AgentLlmCredentialModelsResponse(
                    credentialId=credential.credentialId,
                    credentialName=credential.name,
                    credentialProvider=self._credentialProviderValue(credential.provider),
                    credentialBaseUrl=credential.baseUrl,
                    sourceUrl=url,
                    models=models,
                )
            except Exception as exc:
                errors.append(f"{url}: {exc}")

        raise InvalidParamException(
            userMessage="拉取模型列表失败，请检查凭证 baseUrl、API Key 或服务商是否支持 /models 接口",
            innerMessage="; ".join(errors),
        )

    async def testProfileModel(self, profileId: int) -> AgentLlmProfileTestResponse:
        profile = self.dao.getProfileById(profileId)
        if profile is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {profileId} 的 LLM Profile")
        if not profile.isActive:
            raise InvalidParamException(userMessage="LLM Profile 未启用")

        credential = self.dao.getCredentialById(profile.credentialId)
        if credential is None:
            raise InvalidParamException(userMessage=f"不存在 id 为 {profile.credentialId} 的凭证")
        if not credential.isActive:
            raise InvalidParamException(userMessage="凭证未启用")
        if not credential.baseUrl:
            raise InvalidParamException(userMessage="凭证 baseUrl 为空")

        config = AgentConfig(
            llm_provider=self._mapCredentialProvider(credential.provider),
            llm_endpoint=credential.baseUrl,
            llm_model=profile.model,
            llm_max_tokens=min(self._normalizeMaxTokens(profile.maxTokens), 32),
            llm_context_window=self._normalizeContextWindow(profile.contextWindow),
            llm_temperature=0.0,
            llm_retry_count=0,
            llm_retry_delay=0.0,
        )
        config.llm_api_key = credential.apiKey

        started = time.perf_counter()
        try:
            provider = createProvider(config)
            result = await callStructuredLLM(provider, [
                {
                    "role": "user",
                    "content": loadPrompt("auxiliary/connectivity_test.txt"),
                }
            ])
            if result is None:
                raise RuntimeError(
                    "模型连通性测试响应未通过结构化校验（已重试 5 次）"
                )
            latencyMs = (time.perf_counter() - started) * 1000
            return AgentLlmProfileTestResponse(
                profileId=profile.profileId,
                credentialId=profile.credentialId,
                model=profile.model,
                available=True,
                latencyMs=round(latencyMs, 2),
                content=result.value,
                finishReason=result.response.finish_reason,
                usage=result.response.usage,
            )
        except Exception as exc:
            latencyMs = (time.perf_counter() - started) * 1000
            return AgentLlmProfileTestResponse(
                profileId=profile.profileId,
                credentialId=profile.credentialId,
                model=profile.model,
                available=False,
                latencyMs=round(latencyMs, 2),
                error=str(exc),
            )

    def buildAgentConfig(self, profileId: int | None = None,
                         safetyPolicy: str = "default") -> AgentConfig:
        profile = self.dao.getProfileById(profileId) if profileId else self.dao.getDefaultProfile()
        if profile is None or not profile.isActive:
            return self._fallbackConfig(safetyPolicy)

        credential = self.dao.getCredentialById(profile.credentialId)
        if (
            credential is None
            or not credential.isActive
            or not credential.baseUrl
        ):
            return self._fallbackConfig(safetyPolicy)

        config = AgentConfig(
            llm_provider=self._mapCredentialProvider(credential.provider),
            llm_endpoint=credential.baseUrl,
            llm_model=profile.model,
            llm_max_tokens=self._normalizeMaxTokens(profile.maxTokens),
            llm_context_window=self._normalizeContextWindow(profile.contextWindow),
            llm_temperature=profile.temperature,
            llm_retry_count=profile.retryCount,
            llm_retry_delay=profile.retryDelay,
            safety_policy=safetyPolicy,
        )
        config.llm_api_key = credential.apiKey
        return config

    def _toResponse(self, profile) -> AgentLlmProfileResponse:
        data = AgentLlmProfileOrm2Pydantic.model_validate(profile).model_dump()
        credential = self.dao.getCredentialById(profile.credentialId)
        if credential is not None:
            data["credentialName"] = credential.name
            data["credentialProvider"] = self._credentialProviderValue(credential.provider)
            data["credentialBaseUrl"] = credential.baseUrl
        return AgentLlmProfileResponse.model_validate(data)

    @staticmethod
    def _credentialProviderValue(provider) -> str:
        return provider.value if hasattr(provider, "value") else str(provider)

    @classmethod
    def _mapCredentialProvider(cls, provider) -> str:
        providerValue = cls._credentialProviderValue(provider).lower()
        if providerValue in {"openai", "azure", "anthropic", "custom"}:
            return "openai_compat"
        return providerValue or "openai_compat"

    @staticmethod
    def _fallbackConfig(safetyPolicy: str) -> AgentConfig:
        try:
            config = loadConfig()
            config.safety_policy = safetyPolicy
            return config
        except Exception:
            return AgentConfig(
                llm_provider="mock",
                llm_endpoint="https://mock.local",
                llm_model="mock",
                safety_policy=safetyPolicy,
            )

    @staticmethod
    def _normalizeModels(models: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for model in models:
            value = model.strip()
            if value and value not in seen:
                normalized.append(value)
                seen.add(value)
        return normalized

    @staticmethod
    def _buildProfileName(prefix: str | None, model: str) -> str:
        if prefix:
            name = f"{prefix}-{model}"
        else:
            name = model
        return name[:100]

    @classmethod
    def _normalizeMaxTokens(cls, maxTokens: int | None) -> int:
        if maxTokens is None:
            return 4096
        return max(1, min(int(maxTokens), cls.MAX_LLM_TOKENS))

    @classmethod
    def _normalizeContextWindow(cls, contextWindow: int | None) -> int:
        if contextWindow is None:
            return 1048576
        return max(256, min(int(contextWindow), cls.MAX_CONTEXT_WINDOW))

    @staticmethod
    def _candidateModelUrls(baseUrl: str) -> list[str]:
        base = baseUrl.rstrip("/")
        candidates: list[str] = []

        def add(url: str) -> None:
            if url not in candidates:
                candidates.append(url)

        lowered = base.lower()
        if lowered.endswith("/anthropic"):
            add(base[: -len("/anthropic")] + "/models")
        if lowered.endswith("/chat/completions"):
            add(base[: -len("/chat/completions")] + "/models")
        if lowered.endswith("/messages"):
            add(base[: -len("/messages")] + "/models")
        add(base + "/models")
        return candidates

    @staticmethod
    def _fetchModels(url: str, apiKey: str) -> list[AgentLlmModelInfo]:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {apiKey}",
                "x-api-key": apiKey,
                "anthropic-version": "2023-06-01",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("响应不是合法 JSON") from exc

        rawModels = payload.get("data") if isinstance(payload, dict) else payload
        if rawModels is None and isinstance(payload, dict):
            rawModels = payload.get("models")
        if not isinstance(rawModels, list):
            raise RuntimeError("响应中未找到模型列表")

        models: list[AgentLlmModelInfo] = []
        for item in rawModels:
            if isinstance(item, str):
                models.append(AgentLlmModelInfo(id=item, name=item))
            elif isinstance(item, dict):
                modelId = str(item.get("id") or item.get("name") or item.get("model") or "")
                if not modelId:
                    continue
                models.append(AgentLlmModelInfo(
                    id=modelId,
                    name=item.get("display_name") or item.get("name") or modelId,
                    ownedBy=item.get("owned_by") or item.get("ownedBy"),
                    raw=item,
                ))
        return models
