"""对话 API 端点"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps.auth import CurrentUser
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageResponse,
)
from app.services.conversation import (
    add_message_to_conversation,
    create_conversation,
    delete_conversation,
    get_conversation_by_id,
    get_conversation_messages,
    get_user_conversations,
)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation_endpoint(
    current_user: Annotated[object | None, Depends(CurrentUser)],
    request: ConversationCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    
    conversation = await create_conversation(
        session,
        title=request.title,
        user_id=str(current_user.id),
        description=request.description,
        initial_message=request.title,
    )
    
    return ConversationResponse(
        id=str(conversation.id),
        user_id=conversation.user_id,
        title=conversation.title,
        description=conversation.description,
        context=conversation.context,
        metadata=conversation.conversation_metadata,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )
