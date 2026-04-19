"""
认证相关的 Pydantic schemas
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """用户注册请求"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class LoginRequest(BaseModel):
    """用户登录请求"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token 响应"""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户响应"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str


class ErrorResponse(BaseModel):
    """错误响应"""

    detail: str
