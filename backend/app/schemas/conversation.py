"""对话 schemas"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.models.conversation import MessageRole


class ConversationAction(str, Enum):
    SEARCH = "search"
    CLARIFY = "clarify"
    SUMMARIZE = "summarize"


class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    action: ConversationAction | None = Field(None)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    attachments: list[str] | None
    search_results: list[dict[str, Any]] | None
    created_at: datetime


class ConversationCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)


class ConversationResponse(BaseModel):
    id: str
    user_id: str | None
    title: str
    description: str | None
    context: dict[str, Any] | None
    conversation_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]


class IntentRecognitionRequest(BaseModel):
    query: str
    conversation_id: str | None = None


class LLMResponse(BaseModel):
    action: ConversationAction
    query: str | None
    filters: dict[str, Any] | None
    result_ids: list[str] | None
    summary: str | None
    answer: str | None


class SummarizeRequest(BaseModel):
    conversation_id: str
    max_results: int = 5
