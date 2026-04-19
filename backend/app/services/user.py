"""
用户服务 - 用户 CRUD 操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.services.auth import get_password_hash, verify_password


async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
) -> User:
    """创建新用户"""
    password_hash = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
    )
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise ValueError("用户名或邮箱已存在")


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """通过邮箱获取用户"""
    from sqlalchemy import select

    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    user_id: str,
) -> User | None:
    """通过 ID 获取用户"""
    from sqlalchemy import select
    from uuid import UUID

    result = await session.execute(
        select(User).where(User.id == UUID(user_id))
    )
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """验证用户凭据"""
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
