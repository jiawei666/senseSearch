"""搜索 API 端点 - 多模态向量搜索"""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps.auth import CurrentUser
from app.schemas.content import ContentResponse
from app.services.search import (
    enrich_search_results,
    hybrid_search,
    search_by_image,
    search_by_text,
    search_by_video,
)
from app.services.embedding import embed_image, embed_text

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("/text")
async def search_text(
    session: Annotated[AsyncSession, Depends(get_db)],
    query: str = Form(),
    limit: int = 20,
):
    """文本搜索"""
    limit = min(max(1, limit), 100)
    search_result = await search_by_text(query, limit=limit)
    results = await enrich_search_results(search_result["results"], session)
    return {"results": results, "total": search_result["total"], "limit": limit}


@router.post("/image")
async def search_image(
    session: Annotated[AsyncSession, Depends(get_db)],
    file: Any = Form(),
    limit: int = 20,
):
    """图片搜索"""
    import base64

    # 将文件内容转为 base64
    image_data = await file.read()
    if not image_data:
        raise HTTPException(400, "图片文件不能为空")

    limit = min(max(1, limit), 100)
    image_source = f"data:{file.content_type};base64,{base64.b64encode(image_data).decode()}"

    search_result = await search_by_image(image_source, limit=limit)
    results = await enrich_search_results(search_result["results"], session)
    return {"results": results, "total": search_result["total"], "limit": limit}


@router.post("/video")
async def search_video(
    session: Annotated[AsyncSession, Depends(get_db)],
    file: Any = Form(),
    limit: int = 20,
):
    """视频搜索"""
    import base64

    video_data = await file.read()
    if not video_data:
        raise HTTPException(400, "视频文件不能为空")

    limit = min(max(1, limit), 100)
    video_source = f"data:{file.content_type};base64,{base64.b64encode(video_data).decode()}"

    search_result = await search_by_video(video_source, limit=limit)
    results = await enrich_search_results(search_result["results"], session)
    return {"results": results, "total": search_result["total"], "limit": limit}


@router.post("/hybrid")
async def hybrid_search(
    session: Annotated[AsyncSession, Depends(get_db)],
    query: str | None = Form(None),
    file: Any = Form(None),
    video: Any = Form(None),
    limit: int = 20,
):
    """混合搜索"""
    if not any([query, file, video]):
        raise HTTPException(400, "至少提供一种查询方式（文本、图片或视频）")

    limit = min(max(1, limit), 100)

    query_text = query if query and query.strip() else None
    image_source = None
    video_source = None

    if file:
        image_data = await file.read()
        import base64
        image_source = f"data:{file.content_type};base64,{base64.b64encode(image_data).decode()}"

    if video:
        video_data = await video.read()
        import base64
        video_source = f"data:{video.content_type};base64,{base64.b64encode(video_data).decode()}"

    search_result = await hybrid_search(
        query_text=query_text,
        image_source=image_source,
        video_source=video_source,
        limit=limit,
    )

    results = await enrich_search_results(search_result["results"], session)
    return {"results": results, "total": search_result["total"], "limit": limit}


@router.get("/history")
async def search_history(
    session: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[str | None, Depends(CurrentUser)] = None,
    limit: int = 20,
):
    """搜索历史（暂未实现）"""
    return {"results": [], "total": 0, "limit": limit}
