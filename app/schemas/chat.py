"""Pydantic schemas for semantic cache chat feature."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Source type for chat responses."""
    CACHE = "cache"
    OPENAI_API = "openai_api"


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    question: str = Field(..., min_length=1, max_length=5000)

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    id: UUID
    question: str
    answer: str
    source_type: SourceType
    similarity_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Response schema for chat history endpoint."""

    records: list[ChatResponse]
    total: int
    page: int
    pages: int

    class Config:
        from_attributes = True