from pydantic import BaseModel, Field
from typing import Optional


class CreateSiteRequest(BaseModel):
    domain: str = Field(..., min_length=1, max_length=255, description="域名")
    mode: str = Field(..., pattern="^(static|reverse_proxy)$", description="站点类型")
    listenPort: int = Field(80, ge=1, le=65535, description="监听端口")
    rootPath: Optional[str] = Field(None, max_length=1024, description="静态站点根目录")
    proxyPass: Optional[str] = Field(None, max_length=1024, description="反代目标地址")
    proxyPort: Optional[int] = Field(None, ge=1, le=65535, description="反代目标端口")
    proxyProtocol: str = Field("http", pattern="^(http|https)$", description="反代协议")


class DeleteSiteRequest(BaseModel):
    configName: str = Field(..., min_length=1, max_length=255, description="配置名称")


class SiteListQuery(BaseModel):
    pass


class ApplySslRequest(BaseModel):
    domain: str = Field(..., min_length=1, max_length=255, description="域名")
    email: str = Field(..., min_length=3, max_length=255, description="邮箱")


class ConfigSslRequest(BaseModel):
    domain: str = Field(..., min_length=1, max_length=255, description="域名")
    certPath: str = Field(..., min_length=1, max_length=1024, description="证书路径")
    keyPath: str = Field(..., min_length=1, max_length=1024, description="私钥路径")


class RenewSslRequest(BaseModel):
    domain: str = Field(..., min_length=1, max_length=255, description="域名")


class UpdateSiteConfigRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Nginx 配置原文（完整 server block）")



