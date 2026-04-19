"""对话管理服务 - TDD MVP 版本"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message, MessageRole
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageResponse,
)
from app.services.llm import (
    clarify_intent,
    generate_conversational_answer,
    recognize_intent,
    summarize_results,
)
from app.services.search import (
    enrich_search_results,
    hybrid_search,
)


async def create_conversation(
    session: AsyncSession,
    title: str,
    user_id: str | None = None,
    description: str | None = None,
    initial_message: str | None = None,
) -> Conversation:
    conversation = Conversation(
        title=title,
        user_id=user_id,
        description=description,
        conversation_metadata={"source": "user_initiated"},
    )
    session.add(conversation)
    await session.commit()
    
    if initial_message:
        from app.services.conversation import add_message_to_conversation
        await add_message_to_conversation(
            session,
            str(conversation.id),
            MessageRole.USER,
            initial_message,
            action="search",
        )
    
    await session.refresh(conversation)
    return conversation


async def add_message_to_conversation(
    session: AsyncSession,
    conversation_id: str,
    role: MessageRole,
    content: str,
    action: str = "search",
    search_results: list[dict[str, Any]] | None = None,
) -> Message:
    from app.models.conversation import Conversation as ConvModel
    from uuid import UUID

    result = await session.execute(
        select(ConvModel).where(ConvModel.id == UUID(conversation_id))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ValueError("对话不存在")

    message = Message(
        conversation_id=UUID(conversation_id),
        role=role,
        content=content,
        created_at=datetime.utcnow(),
    )

    if action == "search":
        conversation_history = await get_conversation_messages(session, str(conversation.id))
        intent_result = await recognize_intent(query=content, conversation_history=conversation_history)

        if intent_result["action"] == "search":
            search_result = await hybrid_search(
                query_text=intent_result["query"],
                image_source=None,
                video_source=None,
                limit=intent_result.get("limit", 20),
            )

            enriched_results = await enrich_search_results(search_result["results"], session)

            message.search_results = {
                "items": enriched_results,
                "total": search_result["total"],
                "query": intent_result["query"],
                "filters": intent_result.get("filters", {}),
            }
        elif intent_result["action"] == "clarify":
            message.content = intent_result["question"]

    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_conversation_by_id(
    session: AsyncSession,
    conversation_id: str,
) -> Conversation | None:
    from app.models.conversation import Conversation as ConvModel
    from uuid import UUID

    result = await session.execute(
        select(ConvModel).where(ConvModel.id == UUID(conversation_id))
    )
    return result.scalar_one_or_none()


async def get_conversation_messages(
    session: AsyncSession,
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Message]:
    from app.models.conversation import Message as MessageModel
    from uuid import UUID

    result = await session.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == UUID(conversation_id))
        .order_by(MessageModel.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_user_conversations(
    session: AsyncSession,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Conversation], int]:
    from app.models.conversation import Conversation as ConvModel

    result = await session.execute(
        select(ConvModel).where(ConvModel.user_id == user_id)
    )
    conversations = list(result.scalars().all())
    total = len(conversations)

    return conversations, total


async def get_conversation_context(
    session: AsyncSession,
    conversation_id: str,
    max_messages: int = 10,
) -> list[dict[str, Any]]:
    messages = await get_conversation_messages(session, conversation_id, max_messages)

    context = []
    for msg in messages:
        context.append({
            "role": msg.role.value,
            "content": msg.content,
        })

    return context


async def delete_conversation(
    session: AsyncSession,
    conversation_id: str,
) -> bool:
    from app.models.conversation import Conversation as ConvModel
    from uuid import UUID

    result = await session.execute(
        select(ConvModel).where(ConvModel.id == UUID(conversation_id))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ValueError("对话不存在")

    await session.delete(conversation)
    await session.commit()
    return True


async def update_conversation_context(
    session: AsyncSession,
    conversation_id: str,
    context: dict[str, Any] | None = None,
    conversation_metadata: dict[str, Any] | None = None,
) -> Conversation:
    from app.models.conversation import Conversation as ConvModel
    from uuid import UUID

    result = await session.execute(
        select(ConvModel).where(ConvModel.id == UUID(conversation_id))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ValueError("对话不存在")

    if context is not None:
        conversation.context = context

    if conversation_metadata is not None:
        if conversation.conversation_metadata is None:
            conversation.conversation_metadata = {}
        conversation.conversation_metadata.update(conversation_metadata)

    conversation.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def stream_conversation_updates(
    session: AsyncSession,
    conversation_id: str,
    message: Message,
) -> dict[str, Any]:
    message = await add_message_to_conversation(
        session,
        conversation_id,
        MessageRole.USER,
        message.content,
    )

    conversation_context = await get_conversation_context(session, conversation_id)
    llm_response = await generate_conversational_answer(
        query=message.content,
        search_results=message.search_results if message.search_results else None,
        conversation_history=conversation_context,
    )

    assistant_message = await add_message_to_conversation(
        session,
        conversation_id,
        MessageRole.ASSISTANT,
        llm_response["answer"],
        attachments=None,
        search_results=None,
    )

    await update_conversation_context(
        session,
        conversation_id,
        context=llm_response.get("context"),
    )

    return {
        "type": "message",
        "role": "assistant",
        "content": llm_response["answer"],
        "reference_ids": llm_response.get("reference_ids", []),
        "suggestions": llm_response.get("suggestions", []),
    }
