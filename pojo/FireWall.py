from typing import Optional, List, Generic
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# 允许通过字段别名映射
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,  # 允许通过字段名或别名填充
    json_schema_extra={"ignore": False}
)

# --- 1. 端口规则 模型 ---
class PortRuleBase(BaseModel):
    port: int = Field(..., ge=1, le=65535, description="端口号")
    protocol: int = Field(..., ge=0, le=1, description="协议类型：0=UDP, 1=TCP")
    sourceIp: str = Field(..., max_length=50, description="来源IP，支持CIDR")
    destinationIp: str = Field(..., max_length=50, description="目标IP，支持CIDR")
    priority: int = Field(100, ge=1, description="规则优先级，默认100")
    action: int = Field(..., ge=0, le=1, description="动作：0=拒绝, 1=允许")


class PortRuleCreate(PortRuleBase):
    pass


class PortRuleUpdate(BaseModel):
    # 更新时字段可选
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[int] = Field(None, ge=0, le=1)
    sourceIp: Optional[str] = Field(None, max_length=50)
    destinationIp: Optional[str] = Field(None, max_length=50)
    priority: Optional[int] = Field(None, ge=1)
    action: Optional[int] = Field(None, ge=0, le=1)


class PortRule(PortRuleBase):
    id: int
    createdTime: datetime
    updatedTime: datetime

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": {
        "id": 1, "port": 22, "protocol": 1, "sourceIp": "192.168.1.0/24",
        "destinationIp": "0.0.0.0/0", "priority": 1, "action": 1,
        "createdTime": "2026-04-12T10:00:00Z", "updatedTime": "2026-04-12T10:00:00Z"
    }})


# --- 2. SSH 配置 模型 ---
class SshConfigBase(BaseModel):
    port: int = Field(22, description="SSH监听端口")
    permitRootLogin: str = Field("no", description="root登录允许情况")
    passwordAuthentication: str = Field("yes", description="是否允许密码登录")
    allowUsers: Optional[List[str]] = Field(default=[], description="允许登录的用户列表")
    allowGroups: Optional[List[str]] = Field(default=[], description="允许登录的用户组列表")
    listenAddress: Optional[List[str]] = Field(default=["0.0.0.0"], description="监听地址")
    protocol: int = Field(2, description="SSH协议版本")
    loginGraceTime: int = Field(120, description="登录宽限时间(秒)")
    maxAuthTries: int = Field(6, description="最大认证尝试次数")


class SshConfigCreate(SshConfigBase):
    pass


class SshConfigUpdate(BaseModel):
    port: Optional[int] = None
    permitRootLogin: Optional[str] = None
    passwordAuthentication: Optional[str] = None
    allowUsers: Optional[List[str]] = None
    allowGroups: Optional[List[str]] = None
    listenAddress: Optional[List[str]] = None
    protocol: Optional[int] = None
    loginGraceTime: Optional[int] = None
    maxAuthTries: Optional[int] = None


class SshConfig(SshConfigBase):
    id: int
    createdTime: datetime
    updatedTime: datetime

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": {
        "id": 1, "port": 22, "permitRootLogin": "no", "passwordAuthentication": "yes",
        "allowUsers": ["user1", "user2"], "allowGroups": ["sshusers"],
        "listenAddress": ["0.0.0.0"], "protocol": 2, "loginGraceTime": 120, "maxAuthTries": 6,
        "createdTime": "2026-04-12T10:00:00Z", "updatedTime": "2026-04-12T10:00:00Z"
    }})


# --- 3. SSH 登录日志 模型 ---
class SshLogBase(BaseModel):
    timestamp: datetime = Field(..., description="登录时间")
    user: str = Field(..., max_length=50, description="登录用户名")
    sourceIp: str = Field(..., max_length=50, description="来源IP")
    port: int = Field(..., description="登录端口")
    status: str = Field(..., description="登录状态: SUCCESS / FAILURE")
    reason: Optional[str] = Field(None, max_length=200, description="失败原因")


class SshLogCreate(SshLogBase):
    pass


class SshLog(SshLogBase):
    id: int

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": {
        "id": 101, "timestamp": "2026-04-12T10:01:30Z", "user": "user1",
        "sourceIp": "192.168.1.100", "port": 22, "status": "FAILURE", "reason": "Invalid password"
    }})


# --- 4. 安全开关 模型 ---
class SecuritySwitchState(BaseModel):
    firewallEnabled: bool = Field(..., description="防火墙是否开启")
    sshServiceEnabled: bool = Field(..., description="SSH服务是否开启")


class SecuritySwitchUpdate(BaseModel):
    firewallEnabled: Optional[bool] = None
    sshServiceEnabled: Optional[bool] = None


