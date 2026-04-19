"""
内容服务 - Content CRUD 操作
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentType, ContentSource, ContentStatus


async def create_content(
    session: AsyncSession,
    type: ContentType,
    title: str,
    description: str | None = None,
    file_path: str | None = None,
    source: ContentSource = ContentSource.PRIVATE,
    owner_id: UUID | None = None,
    tags: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> Content:
    """
    创建内容

    Args:
        session: 数据库会话
        type: 内容类型
        title: 标题
        description: 描述
        file_path: 文件路径
        source: 内容来源
        owner_id: 所有者 ID（私有内容）
        tags: 标签列表
        extra_metadata: 额外元数据

    Returns:
        创建的内容对象
    """
    content = Content(
        type=type,
        title=title,
        description=description,
        file_path=file_path,
        source=source,
        owner_id=owner_id,
        tags=tags,
        extra_metadata=extra_metadata,
    )
    session.add(content)
    await session.commit()
    await session.refresh(content)
    return content


async def get_content_by_id(
    session: AsyncSession, content_id: UUID
) -> Content | None:
    """
    通过 ID 获取内容

    Args:
        session: 数据库会话
        content_id: 内容 ID

    Returns:
        内容对象，不存在返回 None
    """
    result = await session.execute(
        select(Content).where(Content.id == content_id)
    )
    return result.scalar_one_or_none()


async def list_content(
    session: AsyncSession,
    owner_id: UUID | None = None,
    content_type: ContentType | None = None,
    source: ContentSource | None = None,
    status: ContentStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Content], int]:
    """
    列出内容

    Args:
        session: 数据库会话
        owner_id: 筛选所有者
        content_type: 筛选内容类型
        source: 筛选内容来源
        status: 筛选状态
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        (内容列表, 总数）
    """
    query = select(Content)

    # 应用筛选条件
    if owner_id is not None:
        query = query.where(Content.owner_id == owner_id)
    if content_type is not None:
        query = query.where(Content.type == content_type)
    if source is not None:
        query = query.where(Content.source == source)
    if status is not None:
        query = query.where(Content.status == status)

    # 获取总数
    from sqlalchemy import func
    total_result = await session.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar() or 0

    # 获取分页数据
    query = query.order_by(Content.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    content_list = list(result.scalars().all())

    return content_list, total


async def update_content(
    session: AsyncSession,
    content_id: UUID,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
) -> Content:
    """
    更新内容

    Args:
        session: 数据库会话
        content_id: 内容 ID
        title: 新标题
        description: 新描述
        tags: 新标签

    Returns:
        更新后的内容对象

    Raises:
        ValueError: 内容不存在
    """
    content = await get_content_by_id(session, content_id)
    if not content:
        raise ValueError("内容不存在")

    if title is not None:
        content.title = title
    if description is not None:
        content.description = description
    if tags is not None:
        content.tags = tags

    content.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(content)
    return content


async def delete_content(
    session: AsyncSession, content_id: UUID
) -> bool:
    """
    删除内容

    Args:
        session: 数据库会话
        content_id: 内容 ID

    Returns:
        是否成功

    Raises:
        ValueError: 内容不存在
    """
    content = await get_content_by_id(session, content_id)
    if not content:
        raise ValueError("内容不存在")

    # 删除关联的文件
    if content.file_path:
        from app.services.file import delete_file
        delete_file(content.file_path)

    # 删除数据库记录
    await session.delete(content)
    await session.commit()
    return True


async def get_content_by_owner(
    session: AsyncSession,
    owner_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Content], int]:
    """
    获取用户的内容

    Args:
        session: 数据库会话
        owner_id: 用户 ID
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        (内容列表, 总数）
    """
    return await list_content(
        session,
        owner_id=owner_id,
        limit=limit,
        offset=offset,
    )


async def get_public_content(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Content], int]:
    """
    获取公共内容

    Args:
        session: 数据库会话
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        (内容列表, 总数）
    """
    return await list_content(
        session,
        source=ContentSource.PUBLIC,
        limit=limit,
        offset=offset,
    )
