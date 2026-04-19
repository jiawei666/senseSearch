"""
搜索服务 - Milvus 向量搜索
"""
from typing import Any

from app.core.config import get_settings
from app.core.milvus import get_milvus_client
from app.models.content import Content, ContentType
from app.services.content import get_content_by_id
from app.services.embedding import embed_image, embed_text

settings = get_settings()
COLLECTION_NAME = settings.milvus_collection_name
EMBEDDING_DIM = 512
TOP_K = 20  # 返回最多 20 个结果


async def search_by_text(
    query_text: str,
    limit: int = TOP_K,
) -> dict[str, Any]:
    """
    文本搜索

    Args:
        query_text: 查询文本
        limit: 返回数量限制

    Returns:
        搜索结果: {"results": [...], "total": int}
    """
    # 生成查询向量
    query_vector = await embed_text(query_text)

    return await _search_milvus(
        embedding=query_vector,
        modality="text",
        limit=limit,
    )


async def search_by_image(
    image_source: str,
    limit: int = TOP_K,
) -> dict[str, Any]:
    """
    图片搜索

    Args:
        image_source: 图片路径或 URL
        limit: 返回数量限制

    Returns:
        搜索结果: {"results": [...], "total": int}
    """
    # 生成查询向量
    query_vector = await embed_image(image_source)

    return await _search_milvus(
        embedding=query_vector,
        modality="image",
        limit=limit,
    )


async def search_by_video(
    video_source: str,
    frame_limit: int = 10,
    limit: int = TOP_K,
) -> dict[str, Any]:
    """
    视频搜索

    Args:
        video_source: 视频路径或 URL
        frame_limit: 最多抽取多少帧
        limit: 返回数量限制

    Returns:
        搜索结果: {"results": [...], "total": int}
    """
    from app.services.video import extract_video_frames

    # 抽取视频帧
    frames = await extract_video_frames(video_source, interval_seconds=3)

    if not frames:
        # 空视频，降级到文本搜索
        # 在实际实现中应该获取视频的标题/描述
        query_vector = await embed_text("视频")
        return await _search_milvus(
            embedding=query_vector,
            modality="text",
            limit=limit,
        )

    # 逐帧嵌入并搜索
    all_results = []
    for i, frame in enumerate(frames[:frame_limit]):
        try:
            frame_vector = await embed_image(frame)
            result = await _search_milvus(
                embedding=frame_vector,
                modality="video_frame",
                limit=limit,
            )
            all_results.extend(result["results"])
        except Exception as e:
            print(f"嵌入帧 {i} 失败: {e}")
            continue

    # 去重并排序
    unique_results = _deduplicate_results(all_results)

    return {
        "results": unique_results[:limit],
        "total": len(unique_results),
    }


async def hybrid_search(
    query_text: str | None = None,
    image_source: str | None = None,
    video_source: str | None = None,
    limit: int = TOP_K,
) -> dict[str, Any]:
    """
    混合搜索（支持文本、图片、视频组合）

    Args:
        query_text: 文本查询
        image_source: 图片查询
        video_source: 视频查询
        limit: 返回数量限制

    Returns:
        搜索结果: {"results": [...], "total": int}
    """
    all_results = []

    # 文本搜索
    if query_text:
        text_result = await search_by_text(query_text, limit=limit)
        all_results.extend(text_result["results"])

    # 图片搜索
    if image_source:
        image_result = await search_by_image(image_source, limit=limit)
        all_results.extend(image_result["results"])

    # 视频搜索
    if video_source:
        video_result = await search_by_video(video_source, limit=limit)
        all_results.extend(video_result["results"])

    # 去重
    unique_results = _deduplicate_results(all_results)

    return {
        "results": unique_results[:limit],
        "total": len(unique_results),
    }


async def _search_milvus(
    embedding: list[float],
    modality: str,
    limit: int = TOP_K,
) -> dict[str, Any]:
    """
    在 Milvus 中搜索

    Args:
        embedding: 查询向量
        modality: 模态类型
        limit: 返回数量限制

    Returns:
        搜索结果: {"results": [...], "total": int}
    """
    from app.core.milvus import _get_thread_pool, get_milvus_client
    import asyncio

    loop = asyncio.get_event_loop()
    client = await loop.run_in_executor(_get_thread_pool(), get_milvus_client)

    # 构造搜索表达式
    expr = f'embedding in [{",".join(map(str, embedding))}]]'

    try:
        # 搜索向量
        search_result = await loop.run_in_executor(
            _get_thread_pool(),
            lambda: client.search(
                collection_name=COLLECTION_NAME,
                data=[embedding],
                anns_field="embedding",
                param={"metric_type": "COSINE"},
                limit=limit,
                expr=expr,
            )
        )

        # 提取结果
        results = []
        if search_result and len(search_result) > 0:
            for hit in search_result[:limit]:
                results.append({
                    "content_id": hit.get("entity", {}).get("content_id"),
                    "score": hit.get("distance", 1.0),
                })

        return {
            "results": results,
            "total": len(results),
        }

    except Exception as e:
        print(f"Milvus 搜索失败: {e}")
        return {
            "results": [],
            "total": 0,
        }


def _deduplicate_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    去重搜索结果（按 content_id）
    """
    seen = set()
    unique = []

    for result in results:
        content_id = result.get("content_id")
        if content_id and content_id not in seen:
            seen.add(content_id)
            unique.append(result)

    return unique


async def enrich_search_results(
    results: list[dict[str, Any]],
    session: Any,
) -> list[dict[str, Any]]:
    """
    为搜索结果关联内容元数据

    Args:
        results: 搜索结果列表
        session: 数据库会话

    Returns:
        带元数据的搜索结果列表
    """
    from uuid import UUID

    enriched = []
    for result in results:
        content_id = result.get("content_id")
        if not content_id:
            continue

        try:
            content = await get_content_by_id(session, UUID(content_id))
            if content:
                enriched.append({
                    **result,
                    "content": {
                        "id": str(content.id),
                        "type": str(content.type),
                        "title": content.title,
                        "description": content.description,
                        "file_path": content.file_path,
                        "source": str(content.source),
                        "owner_id": str(content.owner_id) if content.owner_id else None,
                        "tags": content.tags,
                        "status": str(content.status),
                        "extra_metadata": content.extra_metadata,
                        "created_at": content.created_at.isoformat(),
                    },
                    })
        except Exception as e:
            print(f"获取内容 {content_id} 失败: {e}")
            enriched.append({
                **result,
                "content": None,
                "error": str(e),
            })

    return enriched
