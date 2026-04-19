"""
测试配置 - 初始化数据库、fixtures
"""
import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models.user import User
from app.models.content import Content
from app.services.auth import create_access_token

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # 创建所有模型的表
        await conn.run_sync(User.metadata.create_all)
        await conn.run_sync(Content.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session
        # 每个测试后回滚
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    # 覆盖数据库依赖以使用测试数据库
    from app import core

    async def override_get_db():
        async_session_maker = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session_maker() as session:
            yield session

    from app.core import database
    from app.main import app as main_app

    main_app.dependency_overrides[database.get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    main_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_milvus_client():
    """Mock Milvus 客户端 - 避免实际连接"""
    mock_client = MagicMock()
    mock_client.has_collection.return_value = True
    mock_client.insert.return_value = None
    mock_client.create_index.return_value = None
    mock_client.create_collection.return_value = None
    mock_client.load.return_value = None
    mock_client.delete.return_value = None

    # Mock get_milvus_client
    from unittest.mock import patch

    with patch("app.core.milvus._milvus_client", mock_client):
        with patch("app.core.milvus.get_milvus_client", return_value=mock_client):
            yield mock_client


@pytest.fixture
async def test_user(db_session) -> dict:
    """创建测试用户（直接操作数据库）"""
    from uuid import uuid4

    user = User(
        id=uuid4(),
        github_id=12345,
        username="testuser",
        email="testuser@example.com",
        avatar_url="https://avatar.example.com",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return {
        "id": str(user.id),
        "email": "testuser@example.com",
        "username": "testuser",
    }


@pytest.fixture
async def auth_token(test_user: dict) -> str:
    """获取认证 token"""
    return create_access_token(data={"sub": test_user["id"]})


@pytest.fixture
async def test_user_with_token(db_session) -> dict:
    """创建测试用户并返回 ID 和 token"""
    from uuid import uuid4

    user = User(
        id=uuid4(),
        github_id=54321,
        username="uploader",
        email="uploader@example.com",
        avatar_url="https://uploader.avatar.com",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})

    return {
        "id": str(user.id),
        "email": "uploader@example.com",
        "username": "uploader",
        "token": token,
    }
