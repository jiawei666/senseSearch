"""对话 API（简化版）"""
from typing import Annotated, Any

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


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation_endpoint(
    current_user: Annotated[object | None, Depends(CurrentUser)],
    request: ConversationCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录")
    
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


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_endpoint(
    conversation_id: str,
    current_user: Annotated[object | None, Depends(CurrentUser)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    conversation = await get_conversation_by_id(session, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id and conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权限访问此对话")
    
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


@router.get("", response_model=dict[str, Any]])
async def list_conversations(
    current_user: Annotated[object | None, Depends(CurrentUser)],
    limit: int = 20,
    offset: int = 0,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录")
    
    conversations, total = await get_user_conversations(
        session,
        str(current_user.id),
        limit=limit,
        offset=offset,
    )
    
    return {
        "items": [
            {
                "id": str(c.id),
                "user_id": c.user_id,
                "title": c.title,
                "description": c.description,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in conversations
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message_endpoint(
    conversation_id: str,
    current_user: Annotated[object | None, Depends(CurrentUser)],
    request: MessageCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录")
    
    conversation = await get_conversation_by_id(session, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id and conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权限访问此对话")
    
    message = await add_message_to_conversation(
        session,
        conversation_id,
        role="user",
        content=request.content,
        action="search",
    )
    
    return MessageResponse(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        role=message.role,
        content=message.content,
        attachments=message.attachments,
        search_results=message.search_results,
        created_at=message.created_at,
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation_endpoint(
    conversation_id: str,
    current_user: Annotated[object | None, Depends(CurrentUser)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录")
    
    conversation = await get_conversation_by_id(session, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.user_id and conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权限删除此对话")
    
    await delete_conversation(session, conversation_id)
