from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator

# ==========================================
# 基础模型
# ==========================================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    role: str = Field(default="viewer", max_length=20, description="角色: admin/operator/viewer")
    status: bool = Field(default=True, description="账户状态: True启用, False禁用")

# ==========================================
# 请求模型
# ==========================================

class UserCreate(UserBase):
    """创建用户请求"""
    hashedPassword: str = Field(..., min_length=6, max_length=50, description="密码")

class UserUpdate(BaseModel):
    """更新用户请求（所有字段可选）"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, max_length=20)
    status: Optional[bool] = None
    hashedPassword: Optional[str] = Field(None, min_length=6, max_length=50, description="如需修改密码则传入")

class UserLoginRequest(BaseModel):
    """登录请求"""
    account: str = Field(..., min_length=3, max_length=100, description="用户名或邮箱")
    hashedPassword: str = Field(..., min_length=1, description="密码")

class TokenRefreshRequest(BaseModel):
    """刷新Token请求"""
    refreshToken: str = Field(..., description="刷新令牌")

# ==========================================
# 响应模型
# ==========================================

class UserResponse(UserBase):
    """用户响应模型"""
    userId: int = Field(..., description="用户ID")
    lastLoginAt: Optional[datetime] = Field(None, description="最后登录时间")
    createdAt: datetime = Field(..., description="创建时间")
    updatedAt: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    """Token响应模型"""
    accessToken: str = Field(..., description="访问令牌")
    refreshToken: str = Field(..., description="刷新令牌")