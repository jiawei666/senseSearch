"""
内容相关的 Pydantic schemas
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.content import ContentSource, ContentStatus, ContentType


class ContentCreateRequest(BaseModel):
    """创建内容请求"""

    type: ContentType
    title: str = Field(..., max_length=200, min_length=1)
    description: str | None = Field(None, max_length=2000)
    file_path: str | None = Field(None, max_length=500)
    source: ContentSource = ContentSource.PRIVATE
    tags: list[str] | None = None
    extra_metadata: dict[str, Any] | None = None


class ContentResponse(BaseModel):
    """内容响应"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    title: str
    description: str | None
    file_path: str | None
    source: str
    owner_id: str | None
    tags: list[str] | None
    status: str
    extra_metadata: dict[str, Any] | None
    created_at: str
    updated_at: str


class IndexStatusResponse(BaseModel):
    """索引状态响应"""

    content_id: str
    status: str
    indexed_at: str | None = None
    error_message: str | None = None
