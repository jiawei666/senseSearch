"""
用户相关依赖
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user import get_user_by_id


async def get_current_user_by_id(
    session: AsyncSession,
    user_id: str,
) -> User | None:
    """通过 ID 获取用户（内部使用）"""
    return await get_user_by_id(session, user_id)
