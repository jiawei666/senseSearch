"""
健康检查端点测试 - TDD 第一步：RED
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check_returns_200():
    """
    测试健康检查端点返回 200 状态码
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_returns_json():
    """
    测试健康检查端点返回 JSON 格式
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_health_check_response_structure():
    """
    测试健康检查端点返回正确的响应结构
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "version" in data
        assert "service" in data
        assert data["service"] == "sensesearch-backend"


@pytest.mark.asyncio
async def test_health_check_includes_db_status():
    """
    测试健康检查端点包含数据库状态
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]


@pytest.mark.asyncio
async def test_health_check_includes_milvus_status():
    """
    测试健康检查端点包含 Milvus 状态
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        data = response.json()
        assert "dependencies" in data
        assert "milvus" in data["dependencies"]
