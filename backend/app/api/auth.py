"""
认证路由 - GitHub OAuth
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.database import get_db
from app.deps.auth import CurrentUser
from app.schemas.auth import TokenResponse, UserResponse
from app.services.auth import (
    create_access_token,
    exchange_github_code,
    get_github_user_info,
)
from app.services.user import get_or_create_github_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


@router.get("/github", status_code=status.HTTP_302_FOUND)
async def github_auth():
    """
    GitHub OAuth 授权入口

    重定向到 GitHub 授权页面
    """
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=user:email"
    )
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/github/callback", status_code=status.HTTP_302_FOUND)
async def github_callback(
    code: Annotated[str, Query(description="GitHub OAuth code")],
    session: Annotated[object, Depends(get_db)],
):
    """
    GitHub OAuth 回调处理

    1. 用 code 换取 access_token
    2. 获取 GitHub 用户信息
    3. 创建或查找本地用户
    4. 签发 JWT 并重定向到前端
    """
    frontend_url = "http://localhost:3000/auth/callback"

    try:
        # 1. 换取 GitHub access_token
        github_token = await exchange_github_code(code)

        # 2. 获取 GitHub 用户信息
        github_user = await get_github_user_info(github_token)

        # 3. 创建或查找本地用户
        user = await get_or_create_github_user(
            session,
            github_id=github_user["id"],
            username=github_user["login"],
            email=github_user.get("email"),
            avatar_url=github_user.get("avatar_url"),
        )

        # 4. 签发 JWT
        jwt_token = create_access_token(data={"sub": str(user.id)})

        # 5. 重定向到前端，携带 token
        return RedirectResponse(
            url=f"{frontend_url}?token={jwt_token}",
            status_code=302,
        )

    except Exception as e:
        # 错误时重定向到前端，携带错误信息
        return RedirectResponse(
            url=f"{frontend_url}?error=oauth_failed",
            status_code=302,
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: CurrentUser,
):
    """
    获取当前登录用户信息

    需要有效的 JWT token
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
    )
