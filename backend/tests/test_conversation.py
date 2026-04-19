"""
对话引擎测试 - TDD
"""
import pytest

from app.models.conversation import MessageRole


@pytest.mark.asyncio
class TestConversationCRUD:
    """对话 CRUD 测试"""

    async def test_create_conversation_success(self, db_session):
        """测试创建对话成功"""
        from app.services.conversation import create_conversation

        conversation = await create_conversation(
            db_session,
            title="测试对话",
            description="这是一个测试对话",
            initial_message="你好",
        )

        assert conversation.title == "测试对话"

    async def test_create_conversation_with_user(self, db_session, test_user):
        """测试为用户创建对话"""
        from app.services.conversation import create_conversation

        conversation = await create_conversation(
            db_session,
            title="用户的对话",
            user_id=test_user["id"],
            description="这是一个用户对话",
            initial_message="用户消息",
        )

        assert conversation.user_id == test_user["id"]

    async def test_get_conversation_by_id(self, db_session, test_conversation):
        """测试获取对话详情"""
        from app.services.conversation import get_conversation_by_id

        conversation = await get_conversation_by_id(db_session, str(test_conversation.id))

        assert conversation is not None
        assert conversation.title == test_conversation.title


@pytest.mark.asyncio
class TestMessageManagement:
    """消息管理测试"""

    async def test_add_user_message(self, db_session, test_conversation):
        """测试添加用户消息"""
        from app.services.conversation import add_message_to_conversation

        with pytest.importorskip("app.services.conversation.hybrid_search"):
            message = await add_message_to_conversation(
                db_session,
                str(test_conversation.id),
                MessageRole.USER,
                "测试用户消息",
            )

        assert message.role == MessageRole.USER


@pytest.mark.asyncio
class TestLLMIntegration:
    """LLM 集成测试"""

    async def test_llm_intent_recognition(self):
        """测试 LLM 意图识别 - 搜索"""
        from app.services.llm import recognize_intent

        result = await recognize_intent("搜索猫的照片", [])

        assert result["action"] == "search"

    async def test_llm_summarize_results(self):
        """测试 LLM 结果总结"""
        from app.services.llm import summarize_results

        mock_results = [
            {"content_id": "id1", "title": "结果 1"},
            {"content_id": "id2", "title": "结果 2"},
        ]

        result = await summarize_results(
            mock_results,
            query="搜索猫的照片",
            max_results=5,
        )

        assert "summary" in result


@pytest.mark.asyncio
class TestMultiTurnContext:
    """多轮对话上下文测试"""

    async def test_conversation_context_manager(self, db_session, test_conversation):
        """测试对话上下文管理"""
        from app.services.conversation import get_conversation_context

        context = await get_conversation_context(db_session, str(test_conversation.id), max_messages=10)

        assert isinstance(context, list)


# ============ Fixtures ============
@pytest.fixture
async def test_user(db_session):
    """创建测试用户"""
    from app.models.user import User
    from uuid import uuid4

    # 创建测试用户
    test_user = User(
        id=uuid4(),
        github_id=99999,
        username="testuser",
        email="testuser@example.com",
        avatar_url=None,
    )
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    return {
        "id": str(test_user.id),
        "email": "testuser@example.com",
        "username": "testuser",
    }


@pytest.fixture
async def test_conversation(db_session, test_user):
    """创建测试对话"""
    from app.services.conversation import create_conversation

    # 创建测试对话
    conversation = await create_conversation(
        db_session,
        title="测试对话",
        user_id=test_user["id"],
        description="这是一个测试对话",
        initial_message="你好",
    )

    return {
        "id": str(test_user["id"]),
        "user": test_user,
        "conversation": conversation,
    }
