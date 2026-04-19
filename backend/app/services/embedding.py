"""
多模态嵌入服务 - 文本、图片、视频帧
"""
import base64
import io
from typing import TYPE_CHECKING

import httpx

from app.core.config import get_settings

if TYPE_CHECKING:
    pass

settings = get_settings()

# 嵌入配置
EMBEDDING_API_URL = settings.embedding_api_url
EMBEDDING_API_KEY = getattr(settings, "embedding_api_key", "")
EMBEDDING_DIMENSION = 512
MAX_TEXT_LENGTH = 2000


async def _call_embedding_api(
    modality: str, data: str | list[str]
) -> list[float]:
    """
    调用嵌入 API

    Args:
        modality: text | image
        data: 文本内容或 base64 图片列表

    Returns:
        嵌入向量
    """
    headers = {}
    if EMBEDDING_API_KEY:
        headers["Authorization"] = f"Bearer {EMBEDDING_API_KEY}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if modality == "text":
            payload = {"text": data, "dimension": EMBEDDING_DIMENSION}
        else:  # image
            payload = {"images": data, "dimension": EMBEDDING_DIMENSION}

        # TODO: 替换为实际嵌入 API
        # response = await client.post(
        #     f"{EMBEDDING_API_URL}/{modality}",
        #     json=payload,
        #     headers=headers,
        # )
        # response.raise_for_status()
        # result = response.json()
        # return result["embedding"]

        # MVP: 返回 mock 向量
        import hashlib

        # 使用数据内容的哈希生成确定性向量
        if modality == "text":
            hash_val = int(hashlib.md5(str(data).encode()).hexdigest()[:16], 16)
        else:
            hash_val = int(hashlib.md5(str(data[0]).encode()).hexdigest()[:16], 16)

        # 生成 512 维向量
        vector = []
        for i in range(EMBEDDING_DIMENSION):
            vector.append(((hash_val >> (i % 16)) & 1) * 0.3 + 0.1)

        # 归一化
        norm = sum(x * x for x in vector) ** 0.5
        return [x / norm for x in vector]


async def embed_text(text: str) -> list[float]:
    """
    嵌入文本为向量

    Args:
        text: 待嵌入文本

    Returns:
        512 维向量

    Raises:
        ValueError: 文本为空
    """
    if not text or not text.strip():
        raise ValueError("文本不能为空")

    # 截断超长文本
    truncated = text[:MAX_TEXT_LENGTH].strip()
    if not truncated:
        raise ValueError("文本不能为空")

    return await _call_embedding_api("text", truncated)


def _read_image_as_base64(file_path: str) -> str:
    """
    读取本地图片并转换为 base64

    Args:
        file_path: 图片文件路径

    Returns:
        base64 编码的图片数据
    """
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def _download_image_as_base64(url: str) -> str:
    """
    下载图片并转换为 base64

    Args:
        url: 图片 URL

    Returns:
        base64 编��的图片数据

    Raises:
        ValueError: 下载失败
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")
        except httpx.HTTPError as e:
            raise ValueError(f"下载图片失败: {e}")


async def embed_image(source: str) -> list[float]:
    """
    嵌入图片为向量

    Args:
        source: 图片路径或 URL

    Returns:
        512 维向量

    Raises:
        ValueError: 图片处理失败
    """
    # 判断是 URL 还是本地路径
    if source.startswith(("http://", "https://")):
        base64_data = await _download_image_as_base64(source)
    else:
        base64_data = _read_image_as_base64(source)

    return await _call_embedding_api("image", [base64_data])


async def embed_batch_texts(texts: list[str]) -> list[list[float]]:
    """
    批量嵌入文本

    Args:
        texts: 文本列表

    Returns:
        向量列表
    """
    if not texts:
        return []

    # MVP: 并行调用单个嵌入
    import asyncio

    results = await asyncio.gather(
        *[embed_text(text[:MAX_TEXT_LENGTH]) for text in texts]
    )
    return results
