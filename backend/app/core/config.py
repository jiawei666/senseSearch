"""
应用配置 - 使用 pydantic-settings
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础配置
    app_name: str = "sensesearch-backend"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///:memory:"

    # Milvus 配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection_name: str = "sensesearch"

    # API 配置
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # 安全配置
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 天

    # 文件上传配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "uploads"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
