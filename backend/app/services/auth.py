"""
认证服务 - JWT 和 GitHub OAuth
"""
from datetime import datetime, timedelta

import httpx
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


async def exchange_github_code(code: str) -> str:
    """
    用 GitHub code 换取 access_token

    Args:
        code: GitHub OAuth 回调返回的 code

    Returns:
        GitHub access_token

    Raises:
        httpx.HTTPError: 请求失败时抛出
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]


async def get_github_user_info(access_token: str) -> dict:
    """
    获取 GitHub 用户信息

    Args:
        access_token: GitHub access_token

    Returns:
        包含 id, login, email, avatar_url 的字典

    Raises:
        httpx.HTTPError: 请求失败时抛出
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建 JWT access token

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm="HS256"
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    解码 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload，失败返回 None
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=["HS256"]
        )
        return payload
    except JWTError:
        return None
