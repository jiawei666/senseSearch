"""
GitHub OAuth 认证测试 - TDD 第一步：RED
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select


@pytest.mark.asyncio
class TestGitHubAuth:
    """GitHub OAuth 认证测试"""

    async def test_github_auth_url_redirects(self, client: AsyncClient):
        """测试 /auth/github 返回 302 重定向到 GitHub"""
        response = await client.get("/api/v1/auth/github", follow_redirects=False)

        assert response.status_code == 302
        location = response.headers.get("location")
        assert location is not None
        assert "github.com/login/oauth/authorize" in location
        assert "client_id=" in location
        assert "redirect_uri=" in location
        assert "scope=user:email" in location

    async def test_github_callback_creates_new_user(
        self, client: AsyncClient, db_session
    ):
        """测试 GitHub 回调创建新用户"""
        mock_github_response = {
            "access_token": "gh_test_token",
        }
        mock_user_response = {
            "id": 123456,
            "login": "testgithubuser",
            "email": "github@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/123456?v=4",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            # Mock post for token exchange
            mock_post = AsyncMock()
            mock_post_response = MagicMock()
            mock_post_response.json.return_value = mock_github_response
            mock_post_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_post_response

            # Mock get for user info
            mock_get = AsyncMock()
            mock_get_response = MagicMock()
            mock_get_response.json.return_value = mock_user_response
            mock_get_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_get_response

            # Setup the mock client instance
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_class.return_value.__aenter__.return_value = (
                mock_client_instance
            )
            mock_client_class.return_value.__aexit__.return_value = None

            response = await client.get(
                "/api/v1/auth/github/callback?code=test_code"
            )

            # 验证重定向到前端
            assert response.status_code == 302
            location = response.headers.get("location")
            assert location is not None
            assert "localhost:3000/auth/callback" in location

            # 验证返回了 JWT token
            assert "token=" in location

            # 验证用户已创建
            from app.models.user import User

            result = await db_session.execute(
                select(User).where(User.github_id == 123456)
            )
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.username == "testgithubuser"
            assert user.email == "github@example.com"
            assert user.avatar_url == "https://avatars.githubusercontent.com/u/123456?v=4"

    async def test_github_callback_finds_existing_user(
        self, client: AsyncClient, db_session
    ):
        """测试 GitHub 回调找到现有用户"""
        # 预先创建用户
        from app.models.user import User
        from uuid import uuid4

        existing_user = User(
            id=uuid4(),
            github_id=789012,
            username="oldusername",
            email="old@example.com",
            avatar_url="https://old.avatar.com",
        )
        db_session.add(existing_user)
        await db_session.commit()

        mock_github_response = {
            "access_token": "gh_test_token",
        }
        mock_user_response = {
            "id": 789012,
            "login": "newusername",
            "email": "new@example.com",
            "avatar_url": "https://new.avatar.com",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_post = AsyncMock()
            mock_post_response = MagicMock()
            mock_post_response.json.return_value = mock_github_response
            mock_post_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_post_response

            mock_get = AsyncMock()
            mock_get_response = MagicMock()
            mock_get_response.json.return_value = mock_user_response
            mock_get_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_get_response

            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_class.return_value.__aenter__.return_value = (
                mock_client_instance
            )
            mock_client_class.return_value.__aexit__.return_value = None

            response = await client.get(
                "/api/v1/auth/github/callback?code=test_code"
            )

            # 验证重定向
            assert response.status_code == 302
            location = response.headers.get("location")
            assert location is not None
            assert "localhost:3000/auth/callback" in location
            assert "token=" in location

            # 验证用户信息已更新
            await db_session.refresh(existing_user)
            assert existing_user.username == "newusername"
            assert existing_user.email == "new@example.com"
            assert existing_user.avatar_url == "https://new.avatar.com"

            # 验证只有一个用户（没有创建新用户）
            result = await db_session.execute(select(User))
            count = len(result.all())
            assert count == 1

    async def test_github_callback_updates_user_info(
        self, client: AsyncClient, db_session
    ):
        """测试再次登录更新用户信息"""
        from app.models.user import User
        from uuid import uuid4

        # 第一次登录创建的用户
        user = User(
            id=uuid4(),
            github_id=999888,
            username="firstuser",
            email="first@example.com",
            avatar_url="https://first.avatar.com",
        )
        db_session.add(user)
        await db_session.commit()

        # GitHub 返回更新后的信息
        mock_github_response = {"access_token": "gh_test_token"}
        mock_user_response = {
            "id": 999888,
            "login": "updateduser",
            "email": "updated@example.com",
            "avatar_url": "https://updated.avatar.com",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_post = AsyncMock()
            mock_post_response = MagicMock()
            mock_post_response.json.return_value = mock_github_response
            mock_post_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_post_response

            mock_get = AsyncMock()
            mock_get_response = MagicMock()
            mock_get_response.json.return_value = mock_user_response
            mock_get_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_get_response

            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_class.return_value.__aenter__.return_value = (
                mock_client_instance
            )
            mock_client_class.return_value.__aexit__.return_value = None

            await client.get("/api/v1/auth/github/callback?code=test_code")

            # 验证信息已更新
            await db_session.refresh(user)
            assert user.username == "updateduser"
            assert user.email == "updated@example.com"
            assert user.avatar_url == "https://updated.avatar.com"

    async def test_github_callback_invalid_code(self, client: AsyncClient):
        """测试无效 code 返回错误"""
        # Mock GitHub 返回错误
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_post = AsyncMock()
            mock_post_response = MagicMock()
            mock_post_response.raise_for_status.side_effect = Exception(
                "Invalid code"
            )
            mock_post.return_value = mock_post_response

            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_class.return_value.__aenter__.return_value = (
                mock_client_instance
            )
            mock_client_class.return_value.__aexit__.return_value = None

            response = await client.get(
                "/api/v1/auth/github/callback?code=invalid_code"
            )

            # 验证重定向到错误页面
            assert response.status_code == 302
            location = response.headers.get("location")
            assert location is not None
            assert "localhost:3000/auth/callback" in location
            assert "error=" in location


@pytest.mark.asyncio
class TestCurrentUser:
    """获取当前用��测试"""

    async def test_get_current_user(self, client: AsyncClient, db_session):
        """测试 /auth/me 返回用户信息"""
        from app.models.user import User
        from uuid import uuid4

        # 创建测试用户
        user = User(
            id=uuid4(),
            github_id=111222,
            username="testuser",
            email="test@example.com",
            avatar_url="https://avatar.example.com",
        )
        db_session.add(user)
        await db_session.commit()

        # 创建 JWT token
        from app.services.auth import create_access_token

        token = create_access_token(data={"sub": str(user.id)})

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["avatar_url"] == "https://avatar.example.com"
        assert "password" not in data
        assert "password_hash" not in data

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """测试无效 token 返回 401"""
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """测试没有 token 返回 401"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_current_user_with_nullable_email(
        self, client: AsyncClient, db_session
    ):
        """测试用户没有邮箱的情况"""
        from app.models.user import User
        from uuid import uuid4

        # 创建没有邮箱的用户
        user = User(
            id=uuid4(),
            github_id=333444,
            username="noemailuser",
            email=None,
            avatar_url=None,
        )
        db_session.add(user)
        await db_session.commit()

        from app.services.auth import create_access_token

        token = create_access_token(data={"sub": str(user.id)})

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["username"] == "noemailuser"
        assert data["email"] is None
        assert data["avatar_url"] is None
