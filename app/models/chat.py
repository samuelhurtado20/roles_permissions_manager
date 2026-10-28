"""ChatRecord model for semantic cache chat feature."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, Enum as SAEnum, Float, ForeignKey, Text, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.user import User  # noqa: F401 (ensures User mapper is configured)


class SourceType(str, Enum):
    """Source type for chat records."""
    CACHE = "cache"
    OPENAI_API = "openai_api"


class ChatRecord(Base):
    """Chat record model for semantic cache storage."""

    __tablename__ = "chat_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    answer = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=True)  # Populated on cache hits
    source_type = Column(SAEnum(SourceType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    user = relationship("User", back_populates="chat_records")