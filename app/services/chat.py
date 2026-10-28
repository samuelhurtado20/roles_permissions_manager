"""ChatService for semantic cache chat functionality."""

import time
import uuid
import logging
from threading import Lock
from typing import Optional

import numpy as np
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatRecord, SourceType
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, SourceType as SchemaSourceType

logger = logging.getLogger("chat_service")


class ChatService:
    """Service layer for chat functionality with semantic caching."""

    def __init__(self, db: Session):
        self.db = db
        self._user_locks: dict[int, Lock] = {}
        self._locks_lock = Lock()  # Lock for the locks dictionary itself

    def _get_user_lock(self, user_id: int) -> Lock:
        """Get or create a lock for a specific user (for concurrency handling)."""
        with self._locks_lock:
            if user_id not in self._user_locks:
                self._user_locks[user_id] = Lock()
            return self._user_locks[user_id]

    def compute_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""
        v1 = np.array(embedding1)
        v2 = np.array(embedding2)

        # Normalize vectors for cosine similarity
        v1_norm = v1 / np.linalg.norm(v1)
        v2_norm = v2 / np.linalg.norm(v2)

        return float(np.dot(v1_norm, v2_norm))

    def check_cache(
        self, user_id: int, query_embedding: list[float]
    ) -> Optional[ChatRecord]:
        """Check if there's a semantically matching record in the user's cache.

        Searches all stored chat records for the user using cosine similarity.
        Returns the record if similarity >= threshold, otherwise None.
        """
        query_tuple = tuple(query_embedding)

        # Query using pgvector cosine distance - search all records for this user.
        # cosine_distance maps to the <=> operator; similarity = 1 - distance.
        result = (
            self.db.query(ChatRecord)
            .filter(ChatRecord.user_id == user_id)
            .order_by(ChatRecord.embedding.cosine_distance(query_tuple).asc())
            .first()
        )

        if result is None:
            return None

        # Compute the actual similarity score for the best match
        similarity = self.compute_similarity(query_embedding, list(result.embedding))

        if similarity >= settings.SIMILARITY_THRESHOLD:
            return result

        return None

    def store_record(
        self,
        user_id: int,
        question: str,
        answer: str,
        embedding: list[float],
        source_type: SourceType,
        similarity_score: Optional[float] = None,
    ) -> ChatRecord:
        """Store a new chat record in the database."""
        record = ChatRecord(
            user_id=user_id,
            question=question,
            embedding=embedding,
            answer=answer,
            source_type=source_type,
            similarity_score=similarity_score,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def try_acquire_lock(self, user_id: int) -> bool:
        """Try to acquire the user lock (non-blocking).

        Returns True if this request acquired the lock (is first),
        False if another request already holds it.
        """
        lock = self._get_user_lock(user_id)
        return lock.acquire(blocking=False)

    def release_lock(self, user_id: int):
        """Release the user lock (must be called after processing)."""
        lock = self._get_user_lock(user_id)
        try:
            lock.release()
        except RuntimeError:
            # Lock not held by this thread, ignore
            pass

    def wait_for_lock_release(self, user_id: int, timeout: float = 5.0):
        """Wait for the first request to complete and store its result."""
        lock = self._get_user_lock(user_id)
        deadline = time.time() + timeout
        while lock.locked() and time.time() < deadline:
            time.sleep(0.05)

    async def process_chat(
        self, user_id: int, request: ChatRequest
    ) -> ChatResponse:
        """Process a chat request with semantic caching.

        1. Generate embedding for the question
        2. Check cache for similar questions
        3. If cache hit, return cached answer
        4. If cache miss, call OpenAI and store the result
        """
        start_time = time.time()

        from app.services.openai_client import OpenAIClient
        client = OpenAIClient()

        # Handle concurrency - first request wins pattern
        acquired = self.try_acquire_lock(user_id)

        if not acquired:
            # Another request is processing concurrently for this user.
            # Wait briefly then re-check cache (first request may have stored the result).
            self.wait_for_lock_release(user_id)
            # After waiting, check cache again
            embedding = await client.generate_embedding(request.question)
            cached_record = self.check_cache(user_id, embedding)
            if cached_record:
                return self._build_cache_hit_response(cached_record, user_id, time.time() - start_time)
            # If still no cache hit, proceed as this request needs to generate an answer
            acquired = True

        # Generate embedding
        try:
            embedding = await client.generate_embedding(request.question)
        except RuntimeError as exc:
            logger.error("Embedding generation failed", exc_info=exc)
            self.release_lock(user_id)
            raise HTTPException(
                status_code=503,
                detail="The AI service is temporarily unavailable. Please try again in a few minutes."
            )

        # Check for cache hit
        cached_record = self.check_cache(user_id, embedding)

        if cached_record:
            # Release lock before returning if we acquired it
            self.release_lock(user_id)
            return self._build_cache_hit_response(cached_record, user_id, time.time() - start_time)

        # Cache miss - route to OpenAI
        try:
            answer = await client.generate_chat_completion(request.question)
        except RuntimeError as exc:
            logger.error("OpenAI API failed", exc_info=exc)
            self.release_lock(user_id)
            raise HTTPException(
                status_code=503,
                detail="The AI service is temporarily unavailable. Please try again in a few minutes."
            )

        # Store the new record
        record = self.store_record(
            user_id=user_id,
            question=request.question,
            answer=answer,
            embedding=embedding,
            source_type=SourceType.OPENAI_API,
            similarity_score=None,
        )

        latency_ms = (time.time() - start_time) * 1000
        logger.info(
            "Cache miss - OpenAI response generated",
            extra={
                "user_id": user_id,
                "latency_ms": round(latency_ms, 2),
            },
        )

        # Release lock before returning
        self.release_lock(user_id)

        return ChatResponse(
            id=record.id,
            question=record.question,
            answer=record.answer,
            source_type=SchemaSourceType.OPENAI_API,
            similarity_score=None,
            created_at=record.created_at,
        )

    def _build_cache_hit_response(
        self, record: ChatRecord, user_id: int, latency: float
    ) -> ChatResponse:
        """Build and log a cache hit response."""
        response = ChatResponse(
            id=record.id,
            question=record.question,
            answer=record.answer,
            source_type=SchemaSourceType.CACHE,
            similarity_score=record.similarity_score,
            created_at=record.created_at,
        )

        logger.info(
            "Cache hit",
            extra={
                "user_id": user_id,
                "similarity_score": record.similarity_score,
                "latency_ms": round(latency * 1000, 2),
            },
        )

        return response

    def get_history(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> ChatHistoryResponse:
        """Get paginated chat history for a user."""
        total = (
            self.db.query(func.count(ChatRecord.id))
            .filter(ChatRecord.user_id == user_id)
            .scalar()
        )

        records = (
            self.db.query(ChatRecord)
            .filter(ChatRecord.user_id == user_id)
            .order_by(ChatRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        response_records = [
            ChatResponse(
                id=r.id,
                question=r.question,
                answer=r.answer,
                source_type=SchemaSourceType(r.source_type.value),
                similarity_score=r.similarity_score,
                created_at=r.created_at,
            )
            for r in records
        ]

        return ChatHistoryResponse(
            records=response_records,
            total=total,
            page=(offset // limit) + 1,
            pages=(total + limit - 1) // limit if total > 0 else 1,
        )

    def invalidate_record(self, user_id: int, record_id: uuid.UUID) -> bool:
        """Soft-delete or flag a chat record for invalidation.

        Returns True if the record was found and deleted, False otherwise.
        """
        record = (
            self.db.query(ChatRecord)
            .filter(ChatRecord.id == record_id, ChatRecord.user_id == user_id)
            .first()
        )

        if not record:
            return False

        self.db.delete(record)
        self.db.commit()
        return True