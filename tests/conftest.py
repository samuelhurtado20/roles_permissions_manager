"""Shared pytest fixtures for the test suite."""

import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.session import Base


@pytest.fixture
def test_db_session():
    """In-memory SQLite database session for unit tests.

    Uses SQLite with STATIC_POOL so the schema persists across queries within
    a single test.  The pgvector Vector type falls back to a binary/large
    field here, which is sufficient for testing business logic that does not
    need real vector-similarity operations (the ChatService.check_cache logic
    is exercised through mocking).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables (models must be imported so SQLAlchemy registers them)
    from app.models import user, role, permission, chat  # noqa: F401

    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def client(test_db_session):
    """FastAPI test client with the application configured."""
    from app.main import app
    return TestClient(app)
