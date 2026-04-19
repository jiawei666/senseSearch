"""
Milvus 向量数据���连接配置
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from pymilvus import MilvusClient, connections

from app.core.config import get_settings

settings = get_settings()

# Milvus 客户端实例
_milvus_client: MilvusClient | None = None
_thread_pool: ThreadPoolExecutor | None = None


def _get_thread_pool() -> ThreadPoolExecutor:
    """获取线程池"""
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = ThreadPoolExecutor(max_workers=1)
    return _thread_pool


def _init_milvus_client() -> MilvusClient:
    """在单独线程中初始化 Milvus 客户端"""
    return MilvusClient(
        uri=f"http://{settings.milvus_host}:{settings.milvus_port}"
    )


def get_milvus_client() -> MilvusClient:
    """获取 Milvus 客户端单例"""
    global _milvus_client
    if _milvus_client is None:
        _milvus_client = _init_milvus_client()
    return _milvus_client


async def check_milvus_connection() -> bool:
    """检查 Milvus 连接状态（带超时）"""
    loop = asyncio.get_event_loop()
    try:
        # 在线程池中运行，2 秒超时
        result = await asyncio.wait_for(
            loop.run_in_executor(_get_thread_pool(), _check_milvus_sync),
            timeout=2.0,
        )
        return result
    except (asyncio.TimeoutError, Exception):
        return False


def _check_milvus_sync() -> bool:
    """同步检查 Milvus 连接"""
    try:
        client = get_milvus_client()
        client.list_collections()
        return True
    except Exception:
        return False


async def close_milvus_connection() -> None:
    """关闭 Milvus 连接"""
    global _milvus_client, _thread_pool
    if _milvus_client is not None:
        try:
            connections.disconnect("default")
        except Exception:
            pass
        _milvus_client = None
    if _thread_pool is not None:
        _thread_pool.shutdown(wait=False)
        _thread_pool = None
