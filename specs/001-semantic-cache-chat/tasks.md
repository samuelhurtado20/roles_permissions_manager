---
description: "Task list template for feature implementation"
---

# Tasks: Semantic Cache Chat

**Input**: Design documents from `/specs/001-semantic-cache-chat/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

<!--
  ============================================================================
  IMPORTANT: The tasks below are SPECIFICALLY GENERATED for the Semantic Cache Chat feature.
  Each task follows the checklist format exactly and maps to user stories from spec.md.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (app/, tests/, alembic/, .env.example, Dockerfile, docker-compose.yml)
- [X] T002 Install project dependencies in requirements.txt (FastAPI, SQLAlchemy, pgvector, OpenAI SDK, python-jose, Pydantic, Alembic, pytest)
- [X] T003 [P] Configure project configuration in app/core/config.py using pydantic_settings.BaseSettings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup database configuration in app/db/session.py with SQLAlchemy engine and Base
- [X] T005 [P] Create Alembic migration infrastructure (alembic.ini, env.py, versions/)
- [X] T006 [P] Setup JWT authentication middleware in app/utils/auth.py using python-jose
- [X] T007 [P] Setup error handling middleware in app/utils/errors.py
- [X] T008 Create User model in app/models/user.py (id, email, username, role, created_at)
- [X] T009 Configure .env with OPENAI_API_KEY, DATABASE_URL, SECRET_KEY, and rate limit settings
- [X] T010 Setup OpenAPI documentation and FastAPI app factory in app/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semantic Cache Hit (Priority: P1) 🎯 MVP

**Goal**: Allow Standard Users to submit questions that semantically match stored history (≥85% similarity) and return the cached answer instantly within 500ms.

**Independent Test**: Submit a question from a user, receive an AI-generated answer. Submit a semantically equivalent rephrasing. Verify the second response has source_type "cache" and similarity_score ≥ 0.85 within 500ms.

### Implementation for User Story 1

- [X] T011 [P] Create ChatRecord model in app/models/chat.py (id, user_id FK, question, embedding vector(1536), answer, similarity_score, source_type, created_at)
- [X] T012 [P] Create Alembic migration for chat_records table with pgvector embedding column
- [X] T013 [US1] Implement ChatService in app/services/chat.py with methods: generate_embedding(), compute_similarity(), check_cache(), store_record(), handle_concurrency() (first-request-wins pattern)
- [X] T014 [US1] Create Pydantic schemas in app/schemas/chat.py (ChatRequest, ChatResponse, ChatHistoryResponse) with similarity_score as float≥0 and source_type as enum
- [X] T015 [US1] Implement POST /api/chat endpoint in app/api/routes/chat.py with cache hit logic and 500ms response target
- [X] T016 [US1] Add rate limiting decorator to POST /api/chat endpoint (default 10 queries/user/5min)
- [X] T017 [US1] Implement role-based access: reject Guest/Auditor with 403 on POST /api/chat
- [X] T019 [US1] Configure cosine similarity search index on embedding column using ivfflat

**Checkpoint**: User Story 1 is fully functional and testable - cache hits return within 500ms

---

## Phase 4: User Story 2 - OpenAI Fallback for Novel Questions (Priority: P1)

**Goal**: Route questions with no semantic match (<85% similarity or no history) to OpenAI for generation and store the new Q&A pair for future cache hits.

**Independent Test**: Submit a brand-new question. Verify the system routes to OpenAI, returns source_type "openai", stores the Q&A with embedding, and the answer is available for future cache hits.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement OpenAI client wrapper in app/services/openai_client.py with generate_chat_completion() and generate_embedding() methods
- [X] T021 [US2] Add openai_api fallback routing logic to ChatService when similarity < 0.85 or empty history
- [X] T022 [US2] Implement cache miss storage in ChatService.store_record() with embedding persistence
- [X] T023 [US2] Add health check endpoint for OpenAI API status in app/api/routes/chat.py
- [X] T024 [US2] Implement graceful error handling for OpenAI API failures (HTTP 503)
- [X] T025 [US2] Add response metadata: source_type "openai_api" for new answers
- [X] T026 [US2] Implement embedding API failure handling (FR-012): return HTTP 503 with user-friendly message and Retry-After header
- [X] T027 [US2] Implement token limit handling (FR-014): truncate questions exceeding 8191 tokens with warning metadata

**Checkpoint**: User Story 2 is fully functional - novel questions route to OpenAI and store for caching

---

## Phase 5: User Story 3 - Role-Based Access Control (Priority: P1)

**Goal**: Enforce role-based access where Administrators and Standard Users can submit queries; Guests and Auditors receive 403 on query submission but can view read-only history.

**Independent Test**: Authenticate as each role type. Verify Standard User/Administrator can submit questions; Guest/Auditor receive 403 on submission but can GET history.

### Implementation for User Story 3

- [X] T028 [P] [US3] Add role field to User model (ADMIN, STANDARD, GUEST, AUDITOR)
- [X] T029 [US3] Implement role-based authorization decorator in app/utils/auth.py
- [X] T030 [US3] Protect POST /api/chat with role check (allow ADMIN, STANDARD; reject GUEST, AUDITOR)
- [X] T031 [US3] Protect DELETE /api/chat/{id} with admin-only check (allow ADMIN; reject others)
- [X] T032 [US3] Implement GET /api/chat/history with read-only access for all authenticated roles
- [X] T033 [US3] Add 403 error responses for unauthorized role attempts

**Checkpoint**: User Story 3 is fully functional - role-based access enforced on all endpoints

---

## Phase 6: User Story 4 - Per-User Isolation (Priority: P2)

**Goal**: Ensure each user's semantic cache is isolated; similarity searches only match against that user's own history for privacy and relevance.

**Independent Test**: Create two Standard Users. Have User A ask a question and get an answer. Have User B ask the same question. Verify User B does NOT receive User A's cached answer.

### Implementation for User Story 4

- [X] T034 [P] [US4] Verify all similarity queries are scoped to user_id in ChatService
- [X] T035 [P] [US4] Add database index on (user_id, embedding) for efficient per-user similarity search
- [X] T036 [US4] Update query_history endpoint to filter by authenticated user's user_id
- [X] T037 [US4] Add test case verifying cross-user data isolation

**Checkpoint**: User Story 4 is fully functional - complete user data isolation verified

---

## Phase 7: User Story 5 - Cache Invalidation (Admin) (Priority: P2)

**Goal**: Support admin-only explicit invalidation that removes or flags chat records so they are excluded from future cache hits.

**Independent Test**: Administrator deletes a specific chat record. Verify it returns 204. Subsequent questions should not match against that invalidated record.

### Implementation for User Story 5

- [X] T038 [P] [US5] Create DELETE /api/chat/{record_id} endpoint in app/api/routes/chat.py
- [X] T039 [US5] Implement soft-delete or flag invalidation in ChatService
- [X] T040 [US5] Add admin-only authorization check on DELETE endpoint
- [X] T041 [US5] Update similarity search to exclude invalidated records
- [X] T042 [US5] Add 404 response for non-existent record_id

**Checkpoint**: User Story 5 is fully functional - admin can invalidate cached records

---

## Phase 8: User Story 6 - Observability & Metrics (Priority: P2)

**Goal**: Emit structured JSON logs and record key operational metrics including cache hit rate, request latency (p50/p95), embedding API error rate, external AI service error rate, and active user count.

**Independent Test**: Verify logs contain required fields (timestamp, user_id, request_id, endpoint, source_type, latency_ms). Verify metrics are queryable and cache hit rate ≥ 30% for active users.

### Implementation for User Story 6

- [X] T043 [P] [US6] Create logging utility in app/utils/logger.py with structured JSON output
- [X] T044 [P] [US6] Add metric collection middleware in app/utils/metrics.py
- [X] T045 [US6] Track cache_hit_rate, embedding_error_rate, openai_error_rate, active_user_count
- [X] T046 [US6] Track latency_p50 and latency_p95 for cache hits and misses
- [X] T047 [US6] Add /metrics endpoint for metric discovery
- [X] T048 [US6] Configure log format to include correlation_id for request tracing

**Checkpoint**: User Story 6 is fully functional - observability signals present and queryable

---

## Phase 9: User Story 7 - Rate Limiting (Priority: P2)

**Goal**: Enforce configurable rate limiting on the chat endpoint (default 10 queries per user per 5-minute window) returning HTTP 429 when exceeded.

**Independent Test**: Submit 11 rapid requests. Verify first 10 succeed, 11th returns HTTP 429 with Retry-After header.

### Implementation for User Story 7

- [X] T049 [P] [US7] Implement rate limiting decorator in app/utils/rate_limit.py using in-memory store (dictionary-based sliding window)
- [X] T050 [US7] Protect POST /api/chat with rate limiting (10 queries/5min default, in-memory store)
- [X] T051 [US7] Configure rate_limit_requests and rate_limit_window in config.py
- [X] T052 [US7] Return HTTP 429 with Retry-After header when limit exceeded
- [X] T053 [US7] Add config-based rate limit override mechanism (rate_limit_requests and rate_limit_window environment variables)

**Checkpoint**: User Story 7 is fully functional - rate limiting enforced with proper 429 responses

---

## Phase 10: Test Suite & Documentation

**Purpose**: Validation and polish - ensure everything works and is documented

- [X] T054 [P] Create contract tests in tests/contract/test_chat_api.py for all endpoints
- [X] T055 [P] Create unit tests for ChatService in tests/unit/test_chat_service.py
- [X] T056 [P] Create integration tests in tests/integration/test_chat_full.py
- [X] T057 Update quickstart.md with working validation commands
- [X] T058 Run all tests and verify 100% pass rate
- [X] T059 Run quickstart.md validation scenarios end-to-end
- [X] T060 [P] Implement performance benchmark tests to validate semantic cache hit response latency (< 500ms p95) vs. OpenAI fallback latency (< 5s p95) in Phase 10.
- [X] T061 [P] Implement fallback and health check tests for cache service availability (SC-008) to ensure graceful degrading when vector store or OpenAI API is unreachable.
- [X] T062 [P] Implement circuit breaker pattern in OpenAI client for graceful degradation during service outages (SC-008)
- [X] T063 [P] Expand health check endpoint to verify database connectivity and OpenAI API availability with dependency status (SC-008)
- [X] T064 [P] Add load test for cache hit p95 latency (< 500ms) under concurrent load (SC-001)
- [X] T065 [P] Add load test for cache miss p95 latency (< 5s) under concurrent load (SC-002)
- [X] T066 [P] Add cache hit rate validation test (≥ 30% for active users with ≥ 10 prior questions) (SC-003)

**Checkpoint**: Complete test suite and documentation verified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
- **Test Suite (Phase 10)**: Depends on all implementation phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - No dependencies (independent test: new question routes to OpenAI)
- **User Story 3 (P1)**: Can start after Foundational - No dependencies (independent test: role verification)
- **User Story 4 (P2)**: Can start after Foundational - No dependencies (independent test: cross-user isolation)
- **User Story 5 (P2)**: Can start after Foundational - No dependencies (independent test: admin invalidation)
- **User Story 6 (P2)**: Can start after Foundational - No dependencies (independent test: observability signals)
- **User Story 7 (P2)**: Can start after Foundational - No dependencies (independent test: rate limiting)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- All User Story 1 tasks marked [P] can run in parallel
- User Stories 2-7 can be worked on in parallel by different team members
- All tests for each story marked [P] can run in parallel

### Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create ChatRecord model in app/models/chat.py"
Task: "Create Alembic migration for chat_records table"

# Launch all service tests for User Story 1 together:
Task: "Test cache hit within 500ms with similarity ≥ 0.85"
Task: "Test cache miss routes to OpenAI"
Task: "Test role-based access returns 403 for Guest/Auditor"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Semantic Cache Hit)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy MVP - instant cached answers for repeated queries

### Incremental Delivery

1. Foundation ready
2. Add User Story 1 → Test → Deploy MVP
3. Add User Story 2 → Test → Deploy
4. Add User Story 3 → Test → Deploy
5. Add User Story 4 → Test → Deploy
6. Add User Story 5 → Test → Deploy
7. Add User Story 6 → Test → Deploy
8. Add User Story 7 → Test → Deploy
9. Add Test Suite & Documentation
10. Full feature complete with observability and rate limiting

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Dev A: User Story 1 (MVP)
   - Dev B: User Story 2
   - Dev C: User Story 3
   - Dev D: User Story 4
   - Dev E: User Story 5
   - Dev F: User Story 6
   - Dev G: User Story 7
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
