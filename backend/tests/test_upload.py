"""
文件上传和内容管理测试 - TDD
"""
import base64
import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.content import Content, ContentType, ContentSource, ContentStatus


@pytest.mark.asyncio
class TestFileUpload:
    """文件上传测试"""

    async def test_upload_image_success(self, client: AsyncClient):
        """测试上传图片成功"""
        # 创建测试图片数据
        img_data = b"fake_image_data"

        files = {
            "file": ("test.jpg", img_data, "image/jpeg"),
        }
        data = {
            "title": "测试图片",
            "description": "图片描述",
            "source": "private",
            "tags": "test, image",
        }

        with pytest.importorskip("PIL", reason="需要 PIL"):
            response = await client.post(
                "/api/v1/content/upload",
                files=files,
                data=data,
            )

    async def test_upload_video_success(self, client: AsyncClient):
        """测试上传视频成功"""
        video_data = b"fake_video_data"

        files = {
            "file": ("test.mp4", video_data, "video/mp4"),
        }
        data = {
            "title": "测试视频",
            "description": "视频描述",
            "source": "private",
        }

        with pytest.importorskip("PIL", reason="需要 PIL"):
            response = await client.post(
                "/api/v1/content/upload",
                files=files,
                data=data,
            )

    async def test_upload_public_content(self, client: AsyncClient):
        """测试上传公共内容（不需要登录）"""
        img_data = b"fake_public_image"

        files = {
            "file": ("public.jpg", img_data, "image/jpeg"),
        }
        data = {
            "title": "公共图片",
            "source": "public",
        }

        with pytest.importorskip("PIL", reason="需要 PIL"):
            response = await client.post(
                "/api/v1/content/upload",
                files=files,
                data=data,
            )

    async def test_upload_private_without_auth(self, client: AsyncClient):
        """测试私有内容未登录失败"""
        img_data = b"fake_image_data"

        files = {
            "file": ("private.jpg", img_data, "image/jpeg"),
        }
        data = {
            "title": "私有图片",
            "source": "private",
        }

        response = await client.post(
            "/api/v1/content/upload",
            files=files,
            data=data,
        )
        assert response.status_code == 401

    async def test_upload_unsupported_format(self, client: AsyncClient):
        """测试不支持格式失败"""
        file_data = b"fake_data"

        files = {
            "file": ("test.xyz", file_data, "application/octet-stream"),
        }
        data = {
            "title": "不支持格式",
            "source": "private",
        }

        response = await client.post(
            "/api/v1/content/upload",
            files=files,
            data=data,
        )
        assert response.status_code in {400, 422}


@pytest.mark.asyncio
class TestContentCRUD:
    """内容 CRUD 测试"""

    async def test_get_content_success(self, client: AsyncClient, db_session):
        """测试获取内容成功"""
        from app.services.content import create_content
        from uuid import uuid4

        content = await create_content(
            db_session,
            type=ContentType.TEXT,
            title="测试内容",
            description="内容描述",
            source=ContentSource.PUBLIC,
        )

        response = await client.get(f"/api/v1/content/{content.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(content.id)
        assert data["title"] == "测试内容"

    async def test_get_content_not_found(self, client: AsyncClient):
        """测试获取不存在内容"""
        from uuid import uuid4

        response = await client.get(f"/api/v1/content/{uuid4()}")
        assert response.status_code == 404

    async def test_list_contents(self, client: AsyncClient, db_session):
        """测试列出内容"""
        from app.services.content import create_content

        # 创建多个测试内容
        for i in range(3):
            await create_content(
                db_session,
                type=ContentType.TEXT,
                title=f"内容 {i}",
                description=f"描述 {i}",
                source=ContentSource.PUBLIC,
            )

        response = await client.get("/api/v1/content")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    async def test_list_contents_with_pagination(
        self, client: AsyncClient, db_session
    ):
        """测试分页列出内容"""
        from app.services.content import create_content

        # 创建 10 个内容
        for i in range(10):
            await create_content(
                db_session,
                type=ContentType.TEXT,
                title=f"内容 {i}",
                source=ContentSource.PUBLIC,
            )

        # 获取第一页（5 条）
        response = await client.get("/api/v1/content?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] >= 10

        # 获取第二页
        response = await client.get("/api/v1/content?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5

    async def test_list_contents_filter_by_type(
        self, client: AsyncClient, db_session
    ):
        """测试按类型筛选"""
        from app.services.content import create_content

        await create_content(
            db_session, type=ContentType.TEXT, title="文本", source=ContentSource.PUBLIC
        )
        await create_content(
            db_session, type=ContentType.IMAGE, title="图片", source=ContentSource.PUBLIC
        )
        await create_content(
            db_session, type=ContentType.VIDEO, title="视频", source=ContentSource.PUBLIC
        )

        # 筛选图片
        response = await client.get("/api/v1/content?content_type=image")
        assert response.status_code == 200
        data = response.json()
        assert all(item["type"] == "image" for item in data["items"])

    async def test_update_content(
        self, client: AsyncClient, db_session, test_user
    ):
        """测试更新内容"""
        from app.services.content import create_content
        from uuid import uuid4

        content = await create_content(
            db_session,
            type=ContentType.TEXT,
            title="原标题",
            source=ContentSource.PRIVATE,
            owner_id=test_user["id"],
        )

        response = await client.put(
            f"/api/v1/content/{content.id}",
            json={"title": "新标题", "description": "新描述"},
            headers={"Authorization": f'Bearer {test_user["token"]}'},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"

    async def test_update_content_unauthorized(
        self, client: AsyncClient, db_session
    ):
        """测试未授权更新内容"""
        from app.services.content import create_content

        content = await create_content(
            db_session,
            type=ContentType.TEXT,
            title="测试",
            source=ContentSource.PRIVATE,
            owner_id=uuid4(),  # 另一个用户
        )

        response = await client.put(
            f"/api/v1/content/{content.id}",
            json={"title": "新标题"},
        )
        assert response.status_code == 401

    async def test_delete_content(
        self, client: AsyncClient, db_session, test_user
    ):
        """测试删除内容"""
        from app.services.content import create_content
        from uuid import uuid4

        content = await create_content(
            db_session,
            type=ContentType.TEXT,
            title="待删除",
            source=ContentSource.PRIVATE,
            owner_id=test_user["id"],
        )

        response = await client.delete(
            f"/api/v1/content/{content.id}",
            headers={"Authorization": f'Bearer {test_user["token"]}'},
        )
        assert response.status_code == 204

    async def test_delete_content_unauthorized(
        self, client: AsyncClient, db_session
    ):
        """测试未授权删除内容"""
        from app.services.content import create_content

        content = await create_content(
            db_session,
            type=ContentType.TEXT,
            title="测试",
            source=ContentSource.PRIVATE,
            owner_id=uuid4(),  # 另一个用户
        )

        response = await client.delete(f"/api/v1/content/{content.id}")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestIndexing:
    """索引触发测试"""

    async def test_trigger_index(
        self, client: AsyncClient, db_session, test_user
    ):
        """测试触发内容索引"""
        from app.services.content import create_content
        from uuid import uuid4

        content = await create_content(
            db_session,
            type=ContentType.TEXT,
            title="待索引",
            description="内容",
            source=ContentSource.PRIVATE,
            owner_id=test_user["id"],
        )

        response = await client.post(
            f"/api/v1/content/{content.id}/index",
            headers={"Authorization": f'Bearer {test_user["token"]}'},
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_trigger_index_unauthorized(
        self, client: AsyncClient, db_session
    ):
        """测试未授权触发索引"""
        from app.services.content import create_content

        content = await create_content(
            db_session,
            type=ContentType.TEXT,
            title="测试",
            source=ContentSource.PRIVATE,
            owner_id=uuid4(),
        )

        response = await client.post(f"/api/v1/content/{content.id}/index")
        assert response.status_code == 401


# ============ Fixtures ============
@pytest.fixture
async def test_user(client: AsyncClient, db_session) -> dict:
    """创建测试用户"""
    # 注册用户
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "uploader",
            "email": "uploader@example.com",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201

    # 登录获取 token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "uploader@example.com",
            "password": "SecurePass123!",
        },
    )
    assert login_response.status_code == 200
    login_data = login_response.json()

    # 获取用户 ID
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f'Bearer {login_data["access_token"]}'},
    )
    me_data = me_response.json()

    return {
        "id": me_data["id"],
        "email": "uploader@example.com",
        "password": "SecurePass123!",
        "token": login_data["access_token"],
    }
