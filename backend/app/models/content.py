"""
内容数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ContentSource(str, Enum):
    """内容来源"""
    PUBLIC = "public"
    PRIVATE = "private"


class ContentStatus(str, Enum):
    """内容索引状态"""
    PENDING = "pending"
    INDEXED = "indexed"
    INDEX_FAILED = "index_failed"


class Content(Base):
    """内容模型"""

    __tablename__ = "content"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    type: Mapped[ContentType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[ContentSource] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ContentStatus] = mapped_column(
        String(20),
        default=ContentStatus.PENDING,
        nullable=False,
        index=True,
    )
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
