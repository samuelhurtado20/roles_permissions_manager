# Implementation Plan: Semantic Cache Chat

**Branch**: `001-semantic-cache-chat` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-semantic-cache-chat/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Implement a chat endpoint with vector similarity caching using OpenAI embeddings. Questions are matched against the user's cached history using cosine similarity (≥85% threshold). Cache hits return instantly; cache misses route to OpenAI and store the new Q&A pair. Supports role-based access control with per-user isolation.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, pgvector, OpenAI Python SDK, python-jose (JWT), Pydantic v2/pydantic-settings, Alembic, Uvicorn, pytest

**Storage**: PostgreSQL with pgvector extension for embedding storage and similarity search

**Testing**: pytest with httpx for async testing, pytest-asyncio for async test support

**Target Platform**: Linux server (local Docker for development)

**Project Type**: web-service - FastAPI micro-service with PostgreSQL backend

**Performance Goals**: 
- Cache hits: <500ms p95
- Cache misses: <5s p95 (plus external AI latency)
- ≥30% cache hit rate for active users

**Constraints**: 
- pgvector similarity search queries on embedding vectors
- Per-user isolation for security and relevance
- Admin-only cache invalidation

**Scale/Scope**: Initial implementation supporting ~100 concurrent users with indefinite chat history retention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principle Compliance

- **I. Service Layer Pattern**: ✅ Will implement `ChatService` under `app/services/` containing all business logic (embedding generation, similarity search, cache decision logic). Route handlers in `app/api/routes/chat.py` will delegate to the service.

- **II. Model-Driven Database with Alembic Migrations**: ✅ Will define `ChatRecord` model in `app/models/` inheriting from `app.db.session.Base`. All schema changes applied via Alembic migrations in `alembic/versions/`.

- **III. Schema Validation with Pydantic**: ✅ Request/response schemas (`ChatRequest`, `ChatResponse`) will be defined in `app/schemas/chat.py`. Route handlers will declare `response_model=ChatResponse`.

- **IV. RESTful Route Conventions**: ✅ Endpoints follow `/api/chat` prefix with POST for submission, GET with pagination for history, DELETE for admin invalidation. Standard HTTP status codes (201, 200, 204, 403, 404, 429, 503).

- **V. Environment-Based Configuration**: ✅ All config (OpenAI API keys, rate limits, similarity threshold, embedding model) loaded via `pydantic_settings.BaseSettings` in `app/core/config.py`.

## Project Structure

### Documentation (this feature)

```text
specs/001-semantic-cache-chat/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

Single project structure following constitution's service-layer pattern:

```text
app/
├── api/
│   └── routes/
│       └── chat.py           # Chat endpoints (POST /api/chat, GET /api/chat/history, DELETE /api/chat/{id})
├── core/
│   └── config.py             # Settings via pydantic-settings
├── db/
│   └── session.py            # SQLAlchemy session/Metadata/Bases
├── models/
│   ├── __init__.py
│   ├── user.py               # User model (existing auth system)
│   └── chat.py               # ChatRecord model with pgvector
├── schemas/
│   └── chat.py               # Pydantic schemas for request/response validation
├── services/
│   ├── chat.py               # ChatService (embedding, similarity, cache logic, OpenAI calls)
│   └── openai_client.py      # OpenAI client wrapper (circuit breaker, retry logic)
├── utils/
│   ├── rate_limit.py         # Rate limiting decorator (in-memory sliding window)
│   ├── logger.py             # Structured JSON logging utility
│   ├── metrics.py            # Metric collection middleware
│   └── errors.py             # Error handling middleware
├── main.py                   # FastAPI app factory, router registration

alembic/
└── versions/
    └── *.py                  # Database migrations

tests/
├── contract/
│   └── test_chat_api.py      # API contract tests
├── unit/
│   └── test_chat_service.py  # Service unit tests
└── integration/
    └── test_chat_full.py     # End-to-end tests

.env.example                   # Configuration template
Dockerfile
docker-compose.yml
requirements.txt
```

**Structure Decision**: Single-service FastAPI application following constitution pattern with clean separation between routes (API layer), services (business logic), models (database), and schemas (validation). Models live directly under `app/models/` per constitution's model-driven principle.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No Violations | The specification aligns perfectly with constitution principles. All services will follow the service-layer pattern, models will be properly migrated with Alembic, and routes will delegate to services with Pydantic validation.

## Phase 0: Research Artifacts

See [research.md](research.md) for resolved dependencies and best practices.
