"""
用户服务 - 用户 CRUD 操作 (GitHub OAuth)
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create_github_user(
    session: AsyncSession,
    github_id: int,
    username: str,
    email: str | None,
    avatar_url: str | None,
) -> User:
    """
    获取或创建 GitHub 用户

    按 github_id 查找用户：
    - 存在：更新 username, email, avatar_url
    - 不存在：创建新用户

    Args:
        session: 数据库会话
        github_id: GitHub 用户 ID
        username: GitHub 用户名
        email: GitHub 邮箱（可能为空）
        avatar_url: GitHub 头像 URL（可能为空）

    Returns:
        用户实例
    """
    result = await session.execute(
        select(User).where(User.github_id == github_id)
    )
    user = result.scalar_one_or_none()

    if user:
        # 更新现有用户信息
        user.username = username
        user.email = email
        user.avatar_url = avatar_url
    else:
        # 创建新用户
        user = User(
            github_id=github_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(
    session: AsyncSession,
    user_id: str,
) -> User | None:
    """
    通过 ID 获取用户

    Args:
        session: 数据库会话
        user_id: 用户 UUID 字符串

    Returns:
        用户实例，不存在返回 None
    """
    result = await session.execute(
        select(User).where(User.id == UUID(user_id))
    )
    return result.scalar_one_or_none()
