"""
认证相关的 Pydantic schemas
"""
from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    """Token 响应"""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户响应"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str | None
    avatar_url: str | None
