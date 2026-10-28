"""Unit tests for ChatService business logic."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.chat import ChatService
from app.core.config import settings
from app.models.chat import ChatRecord, SourceType


class TestChatServiceSimilarity:
    """Tests for cosine similarity computation."""

    def test_identical_embeddings_have_similarity_1(self):
        """Test: Identical embeddings have cosine similarity of 1.0."""
        service = ChatService(db=Mock())
        emb = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = service.compute_similarity(emb, emb)
        assert abs(result - 1.0) < 1e-6

    def test_orthogonal_embeddings_have_similarity_0(self):
        """Test: Orthogonal embeddings have cosine similarity of 0."""
        service = ChatService(db=Mock())
        emb1 = [1.0, 0.0]
        emb2 = [0.0, 1.0]
        result = service.compute_similarity(emb1, emb2)
        assert abs(result) < 1e-6

    def test_opposite_embeddings_have_similarity_minus_1(self):
        """Test: Opposite embeddings have cosine similarity of -1.0."""
        service = ChatService(db=Mock())
        emb1 = [1.0, 0.0]
        emb2 = [-1.0, 0.0]
        result = service.compute_similarity(emb1, emb2)
        assert abs(result - (-1.0)) < 1e-6


class TestChatServiceThreshold:
    """Tests for similarity threshold checks."""

    def test_threshold_85_percent(self):
        """Test: SIMILARITY_THRESHOLD defaults to 0.85."""
        assert settings.SIMILARITY_THRESHOLD == 0.85

    def test_check_cache_returns_none_for_empty_history(self):
        """Test: check_cache returns None when user has no history."""
        db = Mock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        service = ChatService(db=db)

        result = service.check_cache(user_id=1, query_embedding=[0.1] * 1536)

        assert result is None

    def test_check_cache_returns_record_above_threshold(self):
        """Test: check_cache returns record when similarity >= threshold."""
        db = Mock()
        record = ChatRecord(
            id=uuid4(),
            user_id=1,
            question="What is the capital of France?",
            embedding=[0.1] * 1536,
            answer="Paris",
            source_type=SourceType.CACHE,
            similarity_score=0.9,
        )

        # Mock query result - mock returns this record
        mock_query = db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = record

        service = ChatService(db=db)
        result = service.check_cache(user_id=1, query_embedding=[0.1] * 1536)

        assert result is not None
        assert result.id == record.id
        assert result.question == "What is the capital of France?"

    def test_check_cache_returns_none_below_threshold(self):
        """Test: check_cache returns None when similarity < threshold."""
        db = Mock()
        # Vectors pointing in opposite directions => cosine similarity of -1.0
        record = ChatRecord(
            id=uuid4(),
            user_id=1,
            question="What is the capital of France?",
            embedding=[1.0] * 1536,
            answer="Paris",
            source_type=SourceType.CACHE,
            similarity_score=0.5,
        )

        mock_query = db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = record

        service = ChatService(db=db)
        # Query vector pointing in the opposite direction => similarity < threshold
        result = service.check_cache(user_id=1, query_embedding=[-1.0] * 1536)

        assert result is None


class TestChatServiceStoreRecord:
    """Tests for storing chat records."""

    def test_store_record_sets_fields_correctly(self):
        """Test: store_record creates record with correct fields."""
        db = Mock()
        service = ChatService(db=db)

        record = service.store_record(
            user_id=1,
            question="Test question",
            answer="Test answer",
            embedding=[0.1] * 1536,
            source_type=SourceType.OPENAI_API,
        )

        assert record.user_id == 1
        assert record.question == "Test question"
        assert record.answer == "Test answer"
        assert record.source_type == SourceType.OPENAI_API
        assert record.similarity_score is None

        # Verify db operations called
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(record)


class TestChatServiceConcurrency:
    """Tests for concurrency handling."""

    def test_try_acquire_lock_returns_true_first_time(self):
        """Test: First request acquires the lock."""
        service = ChatService(db=Mock())
        result = service.try_acquire_lock(user_id=1)
        assert result is True

    def test_try_acquire_lock_returns_false_second_time(self):
        """Test: Second request cannot acquire lock while first holds it."""
        service = ChatService(db=Mock())
        service.try_acquire_lock(user_id=1)
        result = service.try_acquire_lock(user_id=1)
        assert result is False

    def test_release_lock_allows_another_acquisition(self):
        """Test: After releasing lock, another request can acquire."""
        service = ChatService(db=Mock())
        service.try_acquire_lock(user_id=1)
        service.release_lock(user_id=1)
        result = service.try_acquire_lock(user_id=1)
        assert result is True


class TestChatServiceHistory:
    """Tests for chat history retrieval."""

    def test_get_history_returns_empty_for_new_user(self):
        """Test: get_history returns empty history for user with no records."""
        db = Mock()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        service = ChatService(db=db)
        result = service.get_history(user_id=1)

        assert result.records == []
        assert result.total == 0
        assert result.pages == 1

    def test_get_history_returns_records(self):
        """Test: get_history returns user's records paginated."""
        db = Mock()
        mock_record = Mock()
        mock_record.id = uuid4()
        mock_record.question = "What is AI?"
        mock_record.answer = "AI is artificial intelligence."
        mock_record.source_type = SourceType.OPENAI_API
        mock_record.similarity_score = None
        mock_record.created_at = datetime.utcnow()

        db.query.return_value.filter.return_value.scalar.return_value = 1
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]

        service = ChatService(db=db)
        result = service.get_history(user_id=1)

        assert result.total == 1
        assert len(result.records) == 1
        assert result.records[0].question == "What is AI?"
        assert result.records[0].source_type == SourceType.OPENAI_API.value


class TestChatServiceInvalidation:
    """Tests for admin cache invalidation."""

    def test_invalidate_record_returns_true_when_found(self):
        """Test: invalidate_record deletes and returns True when record found."""
        db = Mock()
        record = Mock()
        record.id = uuid4()
        record.user_id = 1

        db.query.return_value.filter.return_value.first.return_value = record
        service = ChatService(db=db)

        result = service.invalidate_record(user_id=1, record_id=record.id)

        assert result is True
        db.delete.assert_called_once_with(record)
        db.commit.assert_called_once()

    def test_invalidate_record_returns_false_when_not_found(self):
        """Test: invalidate_record returns False when record not found."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        service = ChatService(db=db)

        result = service.invalidate_record(user_id=1, record_id=uuid4())

        assert result is False