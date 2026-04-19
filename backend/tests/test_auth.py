"""
用户认证服务测试 - TDD 第一步：RED
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUserRegistration:
    """用户注册测试"""

    async def test_register_success(self, client: AsyncClient):
        """测试成功注册用户"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        """测试重复邮箱注册失败"""
        # 第一次注册
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
            },
        )
        # 第二次注册相同邮箱
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_register_invalid_email(self, client: AsyncClient):
        """测试无效邮箱格式"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """测试弱密码被拒绝"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "123",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestUserLogin:
    """用户登录测试"""

    async def test_login_success(self, client: AsyncClient, test_user):
        """测试成功登录"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """测试错误密码"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """测试不存在的用户"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestCurrentUser:
    """获取当前用户测试"""

    async def test_get_current_user_success(self, client: AsyncClient, auth_token):
        """测试成功获取当前用户"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "password" not in data
        assert "password_hash" not in data

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """测试没有 token"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """测试无效 token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
