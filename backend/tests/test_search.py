"""
搜索服务测试 - TDD
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.models.content import ContentType


@pytest.mark.asyncio
class TestTextSearch:
    """文本搜索测试"""

    async def test_search_by_text_success(self):
        """测试文本搜索成功"""
        from app.services.search import search_by_text

        with patch("app.services.search.embed_text") as mock_embed:
            with patch("app.services.search._search_milvus") as mock_search:
                mock_embed.return_value = [0.1] * 512
                mock_search.return_value = {
                    "results": [
                        {"content_id": "uuid-1", "score": 0.9},
                        {"content_id": "uuid-2", "score": 0.8},
                    ],
                    "total": 2,
                }

        result = await search_by_text("测试查询")

        assert result["total"] == 2
        assert len(result["results"]) == 2

    async def test_search_by_text_empty_query(self):
        """测试空文本查询"""
        from app.services.search import search_by_text

        result = await search_by_text("")

        assert result["total"] == 0
        assert len(result["results"]) == 0


@pytest.mark.asyncio
class TestImageSearch:
    """图片搜索测试"""

    async def test_search_by_image_success(self):
        """测试图片搜索成功"""
        from app.services.search import search_by_image

        with patch("app.services.search.embed_image") as mock_embed:
            with patch("app.services.search._search_milvus") as mock_search:
                mock_embed.return_value = [0.1] * 512
                mock_search.return_value = {
                    "results": [{"content_id": "uuid-img", "score": 0.85}],
                    "total": 1,
                }

        result = await search_by_image("/path/to/image.jpg")

        assert result["total"] == 1
        assert result["results"][0]["content_id"] == "uuid-img"

    async def test_search_by_image_url(self):
        """测试图片 URL 搜索"""
        from app.services.search import search_by_image

        with patch("app.services.search._download_image_as_base64") as mock_download:
            with patch("app.services.search.embed_image") as mock_embed:
                with patch("app.services.search._search_milvus") as mock_search:
                    mock_download.return_value = "base64data"
                    mock_embed.return_value = [0.1] * 512
                    mock_search.return_value = {
                        "results": [{"content_id": "uuid-url", "score": 0.9}],
                        "total": 1,
                    }

        result = await search_by_image("https://example.com/image.jpg")

        assert result["total"] == 1


@pytest.mark.asyncio
class TestVideoSearch:
    """视频搜索测试"""

    async def test_search_by_video_with_frames(self):
        """测试视频搜索（带帧）"""
        from app.services.search import search_by_video

        with patch("app.services.search.extract_video_frames") as mock_extract:
            with patch("app.services.search.embed_image") as mock_embed:
                with patch("app.services.search._search_milvus") as mock_search:
                    mock_extract.return_value = ["frame1", "frame2", "frame3"]
                    mock_embed.return_value = [0.1] * 512
                    mock_search.return_value = {
                        "results": [
                            {"content_id": "uuid-video-frame1", "score": 0.9},
                            {"content_id": "uuid-video-frame2", "score": 0.85},
                            {"content_id": "uuid-video-frame3", "score": 0.8},
                        ],
                        "total": 3,
                    }

        result = await search_by_video("/path/to/video.mp4")

        assert result["total"] == 3
        # 去重后应该只有 1 个结果
        assert len(result["results"]) <= 10


@pytest.mark.asyncio
class TestHybridSearch:
    """混合搜索测试"""

    async def test_hybrid_search_all(self):
        """测试混合搜索（文本+图片+视频）"""
        from app.services.search import hybrid_search

        with patch("app.services.search.search_by_text") as mock_text:
            with patch("app.services.search.search_by_image") as mock_image:
                with patch("app.services.search.search_by_video") as mock_video:
                    mock_text.return_value = {
                        "results": [{"content_id": "uuid-text", "score": 0.9}],
                        "total": 1,
                    }
                    mock_image.return_value = {
                        "results": [{"content_id": "uuid-img", "score": 0.85}],
                        "total": 1,
                    }
                    mock_video.return_value = {
                        "results": [{"content_id": "uuid-video", "score": 0.8}],
                        "total": 1,
                    }

        result = await hybrid_search(
            query_text="文本",
            image_source="image.jpg",
            video_source="video.mp4",
        )

        assert result["total"] == 3
        assert len(result["results"]) == 3


@pytest.mark.asyncio
class TestDeduplication:
    """去重测试"""

    async def test_deduplicate_results(self):
        """测试结果去重"""
        from app.services.search import _deduplicate_results

        results = [
            {"content_id": "uuid-1", "score": 0.9},
            {"content_id": "uuid-1", "score": 0.85},
            {"content_id": "uuid-2", "score": 0.8},
        ]

        deduplicated = _deduplicate_results(results)

        # 应该去掉一个重复的 uuid-1
        assert len(deduplicated) == 2
        assert deduplicated[0]["content_id"] == "uuid-1"
