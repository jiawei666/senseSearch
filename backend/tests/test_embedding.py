"""
嵌入服务测试 - TDD
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.content import Content, ContentType, ContentSource, ContentStatus


@pytest.mark.asyncio
class TestTextEmbedding:
    """文本嵌入测试"""

    async def test_embed_text_success(self):
        """测试文本嵌入成功"""
        from app.services.embedding import embed_text

        # Mock 嵌入 API 调用
        with patch("app.services.embedding._call_embedding_api") as mock_api:
            mock_api.return_value = [0.1] * 512

            result = await embed_text("测试文本")

            assert len(result) == 512
            mock_api.assert_called_once()

    async def test_embed_text_empty(self):
        """测试空文本嵌入失败"""
        from app.services.embedding import embed_text

        with pytest.raises(ValueError, match="文本不能为空"):
            await embed_text("")

    async def test_embed_text_long_text(self):
        """测试长文本截断"""
        from app.services.embedding import embed_text

        # 超过限制的长文本
        long_text = "测试" * 10000

        with patch("app.services.embedding._call_embedding_api") as mock_api:
            mock_api.return_value = [0.1] * 512

            result = await embed_text(long_text)

            # 应该截断到合理长度
            mock_api.assert_called_once()
            call_args = mock_api.call_args
            assert len(call_args[0][0]) < 10000


@pytest.mark.asyncio
class TestImageEmbedding:
    """图片嵌入测试"""

    async def test_embed_image_from_path(self):
        """测试从路径嵌入图片"""
        from app.services.embedding import embed_image

        with (
            patch("app.services.embedding._read_image_as_base64") as mock_read,
            patch("app.services.embedding._call_embedding_api") as mock_api,
        ):
            mock_read.return_value = "base64_image_data"
            mock_api.return_value = [0.1] * 512

            result = await embed_image("/path/to/image.jpg")

            assert len(result) == 512
            mock_read.assert_called_once_with("/path/to/image.jpg")

    async def test_embed_image_from_url(self):
        """测试从 URL 嵌入图片"""
        from app.services.embedding import embed_image

        with (
            patch("app.services.embedding._download_image_as_base64") as mock_download,
            patch("app.services.embedding._call_embedding_api") as mock_api,
        ):
            mock_download.return_value = "base64_image_data"
            mock_api.return_value = [0.1] * 512

            result = await embed_image("https://example.com/image.jpg")

            assert len(result) == 512
            mock_download.assert_called_once_with(
                "https://example.com/image.jpg"
            )


@pytest.mark.asyncio
class TestVideoProcessing:
    """视频处理测试"""

    async def test_extract_frames_success(self):
        """测试视频抽帧成功"""
        from app.services.video import extract_video_frames

        with (
            patch("app.services.video._validate_video_file") as mock_validate,
            patch("app.services.video._run_ffmpeg_extract_frames") as mock_ffmpeg,
        ):
            mock_validate.return_value = None
            # 返回 5 帧，每帧都是 base64
            mock_ffmpeg.return_value = [f"frame_{i}_base64" for i in range(5)]

            frames = await extract_video_frames(
                "/path/to/video.mp4", interval_seconds=2
            )

            assert len(frames) == 5
            mock_ffmpeg.assert_called_once()

    async def test_extract_frames_invalid_file(self):
        """测试无效视频文件"""
        from app.services.video import extract_video_frames

        with patch("app.services.video._validate_video_file") as mock_validate:
            mock_validate.side_effect = ValueError("不是有效的视频文件")

            with pytest.raises(ValueError, match="不是有效的视频文件"):
                await extract_video_frames("/path/to/invalid.mp4")

    async def test_extract_frames_empty_video(self):
        """测试空视频（无法抽帧）"""
        from app.services.video import extract_video_frames

        with (
            patch("app.services.video._validate_video_file") as mock_validate,
            patch("app.services.video._run_ffmpeg_extract_frames") as mock_ffmpeg,
        ):
            mock_validate.return_value = None
            mock_ffmpeg.return_value = []  # 空视频

            frames = await extract_video_frames("/path/to/empty.mp4")

            assert frames == []


@pytest.mark.asyncio
class TestIndexPipeline:
    """索引管线测试"""

    async def test_index_text_content(self, db_session):
        """测试索引文本内容"""
        from app.services.index import index_content

        # 创建测试内容
        content = Content(
            type=ContentType.TEXT,
            title="测试标题",
            description="测试描述",
            source=ContentSource.PRIVATE,
            owner_id=None,
        )
        db_session.add(content)
        await db_session.commit()

        with (
            patch("app.services.index.embed_text") as mock_embed,
            patch("app.services.index._save_to_milvus") as mock_save,
        ):
            mock_embed.return_value = [0.1] * 512
            mock_save.return_value = None

            result = await index_content(db_session, str(content.id))

            assert result["status"] == "indexed"
            mock_embed.assert_called_once()
            mock_save.assert_called_once()

    async def test_index_image_content(self, db_session):
        """测试索引图片内容"""
        from app.services.index import index_content

        content = Content(
            type=ContentType.IMAGE,
            title="测试图片",
            description="图片描述",
            file_path="/path/to/image.jpg",
            source=ContentSource.PRIVATE,
            owner_id=None,
        )
        db_session.add(content)
        await db_session.commit()

        with (
            patch("app.services.index.embed_image") as mock_embed,
            patch("app.services.index._save_to_milvus") as mock_save,
        ):
            mock_embed.return_value = [0.1] * 512
            mock_save.return_value = None

            result = await index_content(db_session, str(content.id))

            assert result["status"] == "indexed"

    async def test_index_video_content(self, db_session):
        """测试索引视频内容"""
        from app.services.index import index_content

        content = Content(
            type=ContentType.VIDEO,
            title="测试视频",
            description="视频描述",
            file_path="/path/to/video.mp4",
            source=ContentSource.PRIVATE,
            owner_id=None,
        )
        db_session.add(content)
        await db_session.commit()

        with (
            patch("app.services.index.extract_video_frames") as mock_extract,
            patch("app.services.index.embed_image") as mock_embed,
            patch("app.services.index._save_to_milvus") as mock_save,
        ):
            mock_extract.return_value = [f"frame_{i}" for i in range(3)]
            mock_embed.return_value = [0.1] * 512
            mock_save.return_value = None

            result = await index_content(db_session, str(content.id))

            assert result["status"] == "indexed"
            # 应该嵌入 3 帧
            assert mock_embed.call_count == 3

    async def test_index_content_not_found(self, db_session):
        """测试索引不存在的内容"""
        from app.services.index import index_content
        from uuid import uuid4

        with pytest.raises(ValueError, match="内容不存在"):
            await index_content(db_session, str(uuid4()))


@pytest.mark.skip("需要 Milvus 服务运行")
@pytest.mark.asyncio
class TestMilvusOperations:
    """Milvus 操作测试"""

    async def test_save_vector_to_milvus(self):
        """测试保存向量到 Milvus"""
        from app.services.index import _save_to_milvus
        from uuid import uuid4

        content_id = str(uuid4())
        vector = [0.1] * 512
        modality = "text"

        with patch("app.services.index.get_milvus_client") as mock_client:
            mock_milvus = MagicMock()
            mock_client.return_value = mock_milvus

            await _save_to_milvus(
                content_id=content_id,
                embedding=vector,
                modality=modality,
                frame_index=-1,
            )

            # 验证调用
            assert mock_milvus.insert.called

    async def test_initialize_milvus_collection(self):
        """测试初始化 Milvus collection"""
        from app.services.index import initialize_milvus_collection

        with patch("app.services.index.get_milvus_client") as mock_client:
            mock_milvus = MagicMock()
            mock_client.return_value = mock_milvus
            mock_milvus.has_collection.return_value = False
            mock_milvus.create_collection.return_value = None
            mock_milvus.create_index.return_value = None
            mock_milvus.load.return_value = None

            result = await initialize_milvus_collection()

            assert result is True
            mock_milvus.create_collection.assert_called_once()

    async def test_collection_already_exists(self):
        """测试 collection 已存在"""
        from app.services.index import initialize_milvus_collection

        with patch("app.services.index.get_milvus_client") as mock_client:
            mock_milvus = MagicMock()
            mock_client.return_value = mock_milvus
            mock_milvus.has_collection.return_value = True

            result = await initialize_milvus_collection()

            assert result is True
            mock_milvus.create_collection.assert_not_called()
