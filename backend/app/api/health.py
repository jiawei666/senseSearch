"""
健康检查端点
"""
from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import check_db_connection
from app.core.milvus import check_milvus_connection

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    健康检查端点
    返回服务状态和依赖项状态
    """
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "dependencies": {
            "database": "connected" if await check_db_connection() else "disconnected",
            "milvus": "connected" if await check_milvus_connection() else "disconnected",
        },
    }
