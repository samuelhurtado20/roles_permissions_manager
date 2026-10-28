"""Chat API routes for semantic cache chat feature."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.chat import ChatService
from app.utils.auth import get_current_user
from app.utils.logger import get_logger
from app.utils.rate_limit import rate_limit, rate_limiter

router = APIRouter(prefix="/chat", tags=["chat"])

logger = get_logger("chat_api")


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def submit_question(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a new question for semantic caching.

    Returns either a cached answer (if similarity >= 85%) or generates
    a new answer via OpenAI and stores it for future cache hits.
    """
    user_id = user.id

    # Rate limiting per user
    rate_limit(user_id)

    # Log the request
    logger.info(
        "Chat request received",
        extra={
            "user_id": user_id,
            "question": request.question,
        },
    )

    service = ChatService(db)

    try:
        response = await service.process_chat(user_id, request)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat processing failed", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable. Please try again in a few minutes.",
        )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get the authenticated user's chat history (paginated).

    Available to all authenticated roles: Administrator, Standard User, Guest, Auditor.
    """
    user_id = user.id

    service = ChatService(db)
    return service.get_history(user_id, limit, offset)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_cache_record(
    record_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invalidate a cache record (admin-only).

    Only users with Administrator role can invalidate cache records.
    """
    # Check if user is admin (role name == 'ADMIN')
    if user.role is None or user.role.name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can invalidate cache records",
        )

    service = ChatService(db)

    if not service.invalidate_record(user.id, record_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat record not found",
        )

    return None