"""
文件上传和内容管理 API
"""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import get_settings
from app.core.database import get_db
from app.deps.auth import CurrentUser
from app.models.content import Content, ContentType, ContentSource, ContentStatus
from app.schemas.content import ContentCreateRequest, ContentResponse, IndexStatusResponse
from app.services.content import (
    create_content,
    delete_content,
    get_content_by_id,
    get_content_by_owner,
    get_public_content,
    list_content,
    update_content,
)
from app.services.file import (
    delete_file,
    generate_thumbnail,
    generate_video_thumbnail,
    get_file_size,
    generate_unique_filename,
    save_uploaded_file,
    validate_file_type,
)
from app.services.index import index_content

settings = get_settings()
router = APIRouter(prefix="/api/v1/content", tags=["content"])


@router.post("/upload", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[object | None, Depends(CurrentUser)] = None,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    source: ContentSource = Form(ContentSource.PRIVATE),
    tags: str | None = Form(None),
):
    """
    上传文件（图片或视频）

    - **file**: 文件（最多 100MB）
    - **title**: 标题
    - **description**: 描述
    - **source**: 来源（public/private）
    - **tags**: 标签（逗号分隔）

    公共内容不需要登录，私有内容需要登录。
    """
    # 验证文件大小
    file_size = 0
    for chunk in file.file:
        file_size += len(chunk)
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件过大，最大支持 {settings.max_file_size / 1024 / 1024:.0f}MB",
            )
    file.file.seek(0)  # 重置文件指针

    # 验证文件类型
    file_type = validate_file_type(file.filename)
    content_type = ContentType.IMAGE if file_type == "image" else ContentType.VIDEO

    # 私有内容需要登录
    if source == ContentSource.PRIVATE and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="私有内容需要登录",
        )

    # 保存文件
    file_path = save_uploaded_file(
        file_data=await file.read(),
        filename=file.filename,
        subfolder="images/" if file_type == "image" else "videos/",
    )

    # 生成缩略图
    thumbnail_path = None
    if file_type == "image":
        thumbnail_path = generate_thumbnail(file_path)
    else:
        thumbnail_path = generate_video_thumbnail(file_path)

    # 解析标签
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 创建内容记录
    owner_id = None
    if source == ContentSource.PRIVATE and current_user:
        owner_id = current_user.id

    content = await create_content(
        session,
        type=content_type,
        title=title,
        description=description,
        file_path=file_path,
        source=source,
        owner_id=owner_id,
        tags=tag_list,
        extra_metadata={
            "original_filename": file.filename,
            "file_size": get_file_size(file_path),
            "thumbnail_path": thumbnail_path,
        } if thumbnail_path else {
            "original_filename": file.filename,
            "file_size": get_file_size(file_path),
        },
    )

    # 异步触发索引（后台任务，这里简化为直接调用）
    # 在生产环境中应该使用 Celery 或类似的任务队列
    index_result = await index_content(session, str(content.id))

    return ContentResponse(
        id=str(content.id),
        type=content_type.value,
        title=content.title,
        description=content.description,
        file_path=content.file_path,
        source=str(content.source),
        owner_id=str(content.owner_id) if content.owner_id else None,
        tags=content.tags,
        status=str(content.status),
        extra_metadata=content.extra_metadata,
        created_at=content.created_at.isoformat(),
        updated_at=content.updated_at.isoformat(),
    )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    获取内容详情
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的内容 ID",
        )

    content = await get_content_by_id(session, content_uuid)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在",
        )

    # 检查权限
    if content.source == ContentSource.PRIVATE:
        # TODO: 验证当前用户是否有权限访问
        pass

    return ContentResponse(
        id=str(content.id),
        type=str(content.type),
        title=content.title,
        description=content.description,
        file_path=content.file_path,
        source=str(content.source),
        owner_id=str(content.owner_id) if content.owner_id else None,
        tags=content.tags,
        status=str(content.status),
        extra_metadata=content.extra_metadata,
        created_at=content.created_at.isoformat(),
        updated_at=content.updated_at.isoformat(),
    )


@router.get("", response_model=dict[str, Any])
async def list_contents(
    session: Annotated[AsyncSession, Depends(get_db)],
    owner: str | None = None,
    content_type: ContentType | None = None,
    source: ContentSource | None = None,
    status: ContentStatus | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    列出内容

    - **owner**: 筛选所有者（用户 ID）
    - **content_type**: 筛选内容类型
    - **source**: 筛选内容来源
    - **status**: 筛选状态
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    owner_id = UUID(owner) if owner else None
    if owner and source and source == "public":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="公共内容不能按所有者筛选",
        )

    content_list, total = await list_content(
        session,
        owner_id=owner_id,
        content_type=content_type,
        source=source,
        status=status,
        limit=min(limit, 100),  # 最大 100
        offset=offset,
    )

    return {
        "items": [
            ContentResponse(
                id=str(c.id),
                type=str(c.type),
                title=c.title,
                description=c.description,
                file_path=c.file_path,
                source=str(c.source),
                owner_id=str(c.owner_id) if c.owner_id else None,
                tags=c.tags,
                status=str(c.status),
                extra_metadata=c.extra_metadata,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in content_list
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content_endpoint(
    content_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[object, Depends(CurrentUser)] = None,
    title: str | None = None,
    description: str | None = None,
    tags: str | None = None,
):
    """
    更新内容

    需要登录且是内容所有者。
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的内容 ID",
        )

    content = await get_content_by_id(session, content_uuid)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在",
        )

    # 验证权限
    if content.source == ContentSource.PRIVATE:
        if content.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限修改此内容",
            )

    # 解析标签
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    updated = await update_content(
        session,
        content_uuid,
        title=title,
        description=description,
        tags=tag_list,
    )

    return ContentResponse(
        id=str(updated.id),
        type=updated.type.value,
        title=updated.title,
        description=updated.description,
        file_path=updated.file_path,
        source=updated.source.value,
        owner_id=str(updated.owner_id) if updated.owner_id else None,
        tags=updated.tags,
        status=updated.status.value,
        extra_metadata=updated.extra_metadata,
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat(),
    )


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_endpoint(
    content_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[object, Depends(CurrentUser)] = None,
):
    """
    删除内容

    需要登录且是内容所有者。
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的内容 ID",
        )

    content = await get_content_by_id(session, content_uuid)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在",
        )

    # 验证权限
    if content.source == ContentSource.PRIVATE:
        if content.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限删除此内容",
            )

    await delete_content(session, content_uuid)


@router.post("/{content_id}/index", response_model=IndexStatusResponse)
async def trigger_index(
    content_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[object, Depends(CurrentUser)] = None,
):
    """
    触发内容索引

    需要登录且是内容所有者。
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的内容 ID",
        )

    content = await get_content_by_id(session, content_uuid)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在",
        )

    # 验证权限
    if content.source == ContentSource.PRIVATE:
        if content.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限索引此内容",
            )

    # 触发索引
    result = await index_content(session, str(content.id))

    return IndexStatusResponse(
        content_id=str(content.id),
        status=result["status"],
        indexed_at=result.get("indexed_at"),
        error_message=result.get("error_message"),
    )
