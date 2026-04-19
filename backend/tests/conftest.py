"""
测试配置 - 初始化数据库、fixtures
"""
import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models.user import User

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)

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


@pytest.fixture
async def test_user(client: AsyncClient) -> dict:
    """创建测试用户"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    return {
        "email": "testuser@example.com",
        "password": "SecurePass123!",
    }


@pytest.fixture
async def auth_token(client: AsyncClient, test_user: dict) -> str:
    """获取认证 token"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]
