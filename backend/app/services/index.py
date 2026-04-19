"""
索引服务 - 内容索引管线、Milvus 操作
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pymilvus import MilvusClient, utility

from app.core.config import get_settings
from app.core.milvus import get_milvus_client
from app.models.content import Content, ContentStatus, ContentType
from app.services.embedding import embed_batch_texts, embed_image, embed_text
from app.services.video import extract_video_frames, get_video_duration

settings = get_settings()

# Milvus collection 配置
COLLECTION_NAME = settings.milvus_collection_name
EMBEDDING_DIM = 512


async def initialize_milvus_collection() -> bool:
    """
    初始化 Milvus collection

    Returns:
        是否成功
    """
    try:
        from app.core.milvus import _get_thread_pool, get_milvus_client
        import asyncio

        loop = asyncio.get_event_loop()
        client = await loop.run_in_executor(_get_thread_pool(), get_milvus_client)

        # 检查 collection 是否存在
        has_collection = await loop.run_in_executor(
            _get_thread_pool(), lambda: client.has_collection(COLLECTION_NAME)
        )

        if has_collection:
            return True

        # 创建 collection schema
        schema = utility.create_schema(
            auto_id=True,
            enable_dynamic_field=False,
            fields=[
                {"field_name": "id", "datatype": DataType.INT64, "is_primary": True},
                {"field_name": "content_id", "datatype": DataType.VARCHAR, "max_length": 36},
                {"field_name": "embedding", "datatype": DataType.FLOAT_VECTOR, "dim": EMBEDDING_DIM},
                {"field_name": "modality", "datatype": DataType.VARCHAR, "max_length": 20},
                {"field_name": "frame_index", "datatype": DataType.INT32},
            ],
        )

        # 创建 collection
        await loop.run_in_executor(
            _get_thread_pool(),
            lambda: client.create_collection(COLLECTION_NAME, schema=schema)
        )

        # 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128},
        }
        await loop.run_in_executor(
            _get_thread_pool(),
            lambda: client.create_index(COLLECTION_NAME, "embedding", index_params)
        )

        # 加载 collection
        await loop.run_in_executor(
            _get_thread_pool(),
            lambda: client.load(COLLECTION_NAME)
        )

        return True

    except Exception as e:
        print(f"初始化 Milvus collection 失败: {e}")
        return False


from pymilvus import DataType


async def _save_to_milvus(
    content_id: str,
    embedding: list[float],
    modality: str,
    frame_index: int = -1,
) -> None:
    """
    保存向量到 Milvus

    Args:
        content_id: 内容 ID
        embedding: 嵌入向量
        modality: 模态 (text/image/video_frame)
        frame_index: 帧索引（视频帧专用，非视频为 -1）
    """
    from app.core.milvus import _get_thread_pool, get_milvus_client
    import asyncio

    loop = asyncio.get_event_loop()
    client = await loop.run_in_executor(_get_thread_pool(), get_milvus_client)

    data = [
        {
            "content_id": content_id,
            "embedding": embedding,
            "modality": modality,
            "frame_index": frame_index,
        }
    ]

    await loop.run_in_executor(
        _get_thread_pool(),
        lambda: client.insert(COLLECTION_NAME, data=data)
    )


async def index_content(
    session: Any, content_id: str
) -> dict[str, Any]:
    """
    索引内容

    Args:
        session: 数据库会话
        content_id: 内容 ID

    Returns:
        索引结果: {"status": "...", "indexed_at": "...", "error_message": "...|None"}
    """
    from sqlalchemy import select

    # 验证 UUID 格式
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise ValueError("无效的内容 ID")

    # 获取内容
    result = await session.execute(
        select(Content).where(Content.id == content_uuid)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise ValueError("内容不存在")

    # 更新状态为 indexing
    content.status = ContentStatus.INDEXED
    # 实际应该有一个 INDEXING 状态，这里简化直接设为 INDEXED

    try:
        if content.type == ContentType.TEXT:
            # 文本索引
            embedding = await embed_text(
                f"{content.title} {content.description or ''}"
            )
            await _save_to_milvus(
                content_id=str(content.id),
                embedding=embedding,
                modality="text",
                frame_index=-1,
            )

        elif content.type == ContentType.IMAGE:
            # 图片索引
            if content.file_path:
                embedding = await embed_image(content.file_path)
                await _save_to_milvus(
                    content_id=str(content.id),
                    embedding=embedding,
                    modality="image",
                    frame_index=-1,
                )
            else:
                raise ValueError("图片内容缺少文件路径")

        elif content.type == ContentType.VIDEO:
            # 视频索引 - 抽帧并嵌入
            if content.file_path:
                frames = await extract_video_frames(content.file_path)

                if not frames:
                    # 空视频，只用描述
                    embedding = await embed_text(
                        f"{content.title} {content.description or ''}"
                    )
                    await _save_to_milvus(
                        content_id=str(content.id),
                        embedding=embedding,
                        modality="text",
                        frame_index=-1,
                    )
                else:
                    # 批量嵌入帧
                    frame_embeddings = []
                    for i, frame in enumerate(frames):
                        try:
                            emb = await embed_image(frame)
                            frame_embeddings.append((i, emb))
                        except Exception as e:
                            print(f"嵌入帧 {i} 失败: {e}")
                            continue

                    # 保存所有帧
                    for frame_idx, embedding in frame_embeddings:
                        await _save_to_milvus(
                            content_id=str(content.id),
                            embedding=embedding,
                            modality="video_frame",
                            frame_index=frame_idx,
                        )

                    # 更新元数据
                    if content.extra_metadata is None:
                        content.extra_metadata = {}
                    content.extra_metadata["frame_count"] = len(frame_embeddings)
                    try:
                        duration = get_video_duration(content.file_path)
                        content.extra_metadata["duration"] = duration
                    except Exception:
                        pass

            else:
                raise ValueError("视频内容缺少文件路径")

        else:
            raise ValueError(f"不支持的内容类型: {content.type}")

        # 更新状态
        content.status = ContentStatus.INDEXED
        content.updated_at = datetime.utcnow()
        await session.commit()

        return {
            "status": "indexed",
            "indexed_at": datetime.utcnow().isoformat(),
            "error_message": None,
        }

    except Exception as e:
        # 更新为失败状态
        content.status = ContentStatus.INDEX_FAILED
        content.updated_at = datetime.utcnow()
        await session.commit()

        return {
            "status": "index_failed",
            "indexed_at": None,
            "error_message": str(e),
        }


async def batch_index_content(
    session: Any, content_ids: list[str]
) -> dict[str, Any]:
    """
    批量索引内容

    Args:
        session: 数据库会话
        content_ids: 内容 ID 列表

    Returns:
        索引结果: {"total": int, "success": int, "failed": int, "details": list}
    """
    results = []
    success_count = 0
    failed_count = 0

    for content_id in content_ids:
        try:
            result = await index_content(session, content_id)
            results.append({"content_id": content_id, **result})
            if result["status"] == "indexed":
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            results.append({
                "content_id": content_id,
                "status": "index_failed",
                "indexed_at": None,
                "error_message": str(e),
            })
            failed_count += 1

    return {
        "total": len(content_ids),
        "success": success_count,
        "failed": failed_count,
        "details": results,
    }


async def delete_from_index(content_id: str) -> bool:
    """
    从索引中删除内容

    Args:
        content_id: 内容 ID

    Returns:
        是否成功
    """
    from app.core.milvus import _get_thread_pool, get_milvus_client
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        client = await loop.run_in_executor(_get_thread_pool(), get_milvus_client)

        # 删除该 content_id 的所有向量
        expr = f'content_id == "{content_id}"'
        await loop.run_in_executor(
            _get_thread_pool(),
            lambda: client.delete(COLLECTION_NAME, expr)
        )

        return True

    except Exception as e:
        print(f"从索引删除失败: {e}")
        return False
