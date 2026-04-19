"""
认证路由 - 注册、登录、获取当前用户
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.deps.auth import CurrentUser
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import create_access_token
from app.services.user import (
    authenticate_user,
    create_user,
    get_user_by_email,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: Annotated[object, Depends(get_db)],
):
    """
    用户注册

    - **username**: 用户名 (3-50 字符)
    - **email**: 邮箱地址
    - **password**: 密码 (至少 8 位，包含大小写字母和数字)
    """
    try:
        user = await create_user(
            session,
            username=data.username,
            email=data.email,
            password=data.password,
        )
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: Annotated[object, Depends(get_db)],
):
    """
    用户登录

    - **email**: 邮箱地址
    - **password**: 密码

    返回 JWT access token
    """
    user = await authenticate_user(session, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)


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
    )
