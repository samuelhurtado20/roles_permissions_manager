# Feature Specification: Semantic Cache Chat

**Feature Branch**: `001-semantic-cache-chat`

**Created**: 2026-10-26

**Status**: Ready for Planning

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Semantic Cache Hit (Priority: P1)

A Standard User submits a question that semantically matches a previously asked question (by the same user) at or above the 85% cosine similarity threshold, and the system returns the cached answer instantly.

**Why this priority**: This is the core value proposition — instant answers without LLM latency or cost for repeat queries.

**Independent Test**: Submit a question, receive an AI-generated answer. Submit a semantically equivalent rephrasing of that same question. Verify the second response is returned instantly, marked as "cache" source, and matches the original answer content.

**Acceptance Scenarios**:

1. **Given** a Standard User has previously asked "What is the capital of France?" and received "Paris is the capital of France.", **When** the same user asks "What's the capital city of France?", **Then** the system returns the cached answer "Paris is the capital of France." with source_type "cache" and similarity_score ≥ 0.85 within 500ms.

2. **Given** a Standard User has an existing cached Q&A pair, **When** they submit a semantically similar question with a typo ("What is teh capital of France?"), **Then** the system returns the cached answer if similarity ≥ 0.85.

3. **Given** a Standard User has multiple cached Q&A pairs, **When** they submit a question similar to multiple entries, **Then** the system returns the answer with the highest similarity score (provided it meets the 0.85 threshold).

---

### User Story 2 - OpenAI Fallback for Novel Questions (Priority: P1)

A Standard User submits a question with no semantic match at or above 85% similarity in their history, and the system routes it to an external AI service and stores the new Q&A for future use.

**Why this priority**: Ensures users always get answers to new questions; the cache is an optimization, not a gatekeeper.

**Independent Test**: Submit a brand-new question never seen before by this user. Verify the system routes to an external AI service, returns a generated answer marked "openai" source, and stores the new Q&A with embedding for future cache hits.

**Acceptance Scenarios**:

1. **Given** a Standard User with no prior history asks "Explain quantum entanglement in simple terms", **When** the system computes similarity against their (empty) history and finds no match ≥ 0.85, **Then** the question is sent to an external AI service, a generated answer is returned with source_type "openai", and the Q&A pair with embedding is persisted.

2. **Given** a Standard User has history but asks a completely unrelated question, **When** maximum similarity < 0.85, **Then** the system routes to an external AI service and stores the new interaction.

---

### User Story 3 - Role-Based Access Control (Priority: P1)

Administrators and Standard Users can submit queries and generate responses; Guests and Auditors can only view chat logs.

**Why this priority**: Security and authorization are foundational; incorrect permissions would expose data or allow unauthorized actions.

**Independent Test**: Authenticate as each role type. Verify Standard User/Administrator can submit questions and see responses. Verify Guest/Auditor cannot submit new queries but can view read-only history.

**Acceptance Scenarios**:

1. **Given** an authenticated Standard User, **When** they submit a question via the chat endpoint, **Then** the request is processed (cache check → AI fallback → store).

2. **Given** an authenticated Administrator, **When** they submit a question, **Then** the request is processed identically to Standard User.

3. **Given** an authenticated Guest, **When** they attempt to submit a question, **Then** the system returns a 403 Forbidden error.

4. **Given** an authenticated Auditor, **When** they attempt to submit a question, **Then** the system returns a 403 Forbidden error.

5. **Given** an authenticated Guest, **When** they request their chat history, **Then** the system returns a read-only list of past Q&A pairs without allowing new submissions.

---

### User Story 4 - Per-User Isolation (Priority: P2)

Each user's semantic cache is isolated; similarity searches only match against that user's own history.

**Why this priority**: Privacy and relevance — answers from other users' contexts may be inappropriate or sensitive.

**Independent Test**: Create two Standard Users. User A asks "What's my project deadline?" and gets an answer. User B asks the same question. Verify User B does NOT get User A's cached answer (different context/answer).

**Acceptance Scenarios**:

1. **Given** User A has a cached Q&A, **When** User B submits a semantically identical question, **When** User B's request is treated as a cache miss (or hits only User B's own history), **Then** User A's answer is never returned to User B.

---

### Edge Cases

- **Empty history**: First question from a new user always routes to an external AI service (no prior embeddings to compare).
- **Exactly at threshold**: A similarity score of exactly 0.85 qualifies as a cache hit.
- **Below threshold but close**: A score of 0.849 routes to the external AI service; the new answer is stored separately (not merged).
- **Embedding generation failure**: If the embedding API is unavailable, the system returns a graceful error to the user (e.g., HTTP 503).
- **External AI service failure**: If the external AI service is unavailable after a cache miss, the system returns a graceful error to the user (e.g., HTTP 503).
- **Concurrent identical requests**: Two identical questions submitted simultaneously by the same user — the first request wins; subsequent concurrent requests that complete after the first has stored its result receive the first request's cached answer.
- **Very long questions**: Questions exceeding the embedding model's token limit are truncated to the limit with a warning in the response metadata.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept plain-text questions from authenticated Standard Users and Administrators via a chat API endpoint.
- **FR-002**: System MUST generate a vector embedding for each incoming question using an embedding model.
- **FR-003**: System MUST compute cosine similarity between the new question's embedding and all stored embeddings belonging to the same user.
- **FR-004**: System MUST return the cached answer when maximum cosine similarity ≥ 0.85, with response metadata indicating source_type "cache" and the similarity_score.
- **FR-005**: System MUST route the question to an external AI chat completion model when maximum cosine similarity < 0.85 (or no history exists).
- **FR-006**: System MUST return the externally-generated answer with response metadata indicating source_type "openai".
- **FR-007**: System MUST persist every question-answer pair (question, embedding, answer, user_id, timestamp, source_type) for future similarity searches.
- **FR-008**: System MUST enforce role-based access: Standard Users and Administrators can submit queries; Guests and Auditors receive 403 on query submission.
- **FR-009**: System MUST allow Guests and Auditors to retrieve their own chat history in read-only mode.
- **FR-010**: System MUST isolate similarity searches per user — embeddings from other users are never compared or returned.
- **FR-011**: System MUST respond to cache hits within 500ms (target) and cache misses within acceptable external AI service latency.
- **FR-012**: System MUST return a graceful error to the user when the embedding API is unavailable (e.g., HTTP 503 Service Unavailable with a clear, user-friendly message).
- **FR-013**: System MUST handle concurrent requests for the same user correctly: when identical or near-identical questions are submitted simultaneously, the first request wins (routes to the external AI service and stores the answer); subsequent concurrent requests that complete after the first has stored its result receive the first request's cached answer.
- **FR-014**: System MUST handle questions exceeding the embedding model's token limit by truncating the question to the limit and including a warning in the response metadata.
- **FR-015**: System MUST support cache invalidation for incorrect or outdated answers via an explicit admin-only action that removes or flags the chat record so it is excluded from future cache hits.
- **FR-016**: System MUST emit structured JSON logs and record key operational metrics including: cache hit rate, request latency (p50 and p95), embedding API error rate, external AI service error rate, and active user count.
- **FR-017**: System MUST enforce configurable rate limiting on the chat endpoint (e.g., default 10 queries per user per 5-minute window) and return HTTP 429 when the limit is exceeded.

### Key Entities

- **ChatRecord**: Represents a single question-answer interaction. Attributes: id (UUID), user_id (UUID, FK to User), question (text), embedding (vector, fixed dimensions), answer (text), similarity_score (float, nullable, populated on cache hits), source_type (enum: CACHE | OPENAI_API), created_at (timestamp).
- **User**: Existing entity from the authorization system. Roles: Administrator, Standard User, Guest, Auditor. Referenced by user_id in ChatRecord.
- **Embedding**: The vector representation of a question (fixed-dimension float array from an embedding model).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cache hit responses are returned in under 500ms (95th percentile) from request receipt to response delivery.
- **SC-002**: Cache miss responses (external AI service fallback) complete within the upstream AI service's typical latency plus minimal overhead (target < 5 seconds end-to-end for 95th percentile).
- **SC-003**: Semantic cache hit rate achieves ≥ 30% for users with ≥ 10 prior questions within the same session/domain context.
- **SC-004**: Zero cross-user data leakage: in automated testing with 100 users each asking 50 questions, no user ever receives another user's cached answer.
- **SC-005**: Role enforcement correctness: 100% of Guest/Auditor query submissions return 403; 100% of Standard User/Administrator submissions are processed.
- **SC-006**: Answer accuracy: Cached answers are semantically equivalent to what the external AI service would generate for the same question (validated via human evaluation on a sample of 100 cached responses, ≥ 90% rated equivalent or better).
- **SC-007**: Cost reduction: Embedding + similarity search cost per cache hit is at least 90% lower than a full external AI service chat completion call.
- **SC-008**: System availability: Chat endpoint returns successful responses (2xx) for ≥ 99.5% of valid requests over a 30-day period.
- **SC-009**: Required observability signals are present and queryable: structured JSON logs contain requested fields; key metrics (cache hit rate, latency p50/p95, error rates by type) are tracked at the defined intervals.
- **SC-010**: Rate limiting is enforced: when a user exceeds their query limit (10 queries/5-minute window by default), the system returns HTTP 429 without processing additional requests within that window.

## Assumptions

- **Embedding model**: OpenAI's `text-embedding-3-small` (1536 dimensions) is used for all embedding generation. This is the default unless otherwise configured.
- **Chat completion model**: OpenAI's `gpt-4o-mini` is the default for fallback generation; `gpt-4o` may be used for higher-quality needs (configurable).
- **Similarity scope**: Similarity search is scoped to the authenticated user's history only (per-user isolation).
- **Threshold**: The 85% cosine similarity threshold is fixed at launch but configurable via environment variable for future tuning.
- **Data retention**: Chat records are retained indefinitely (no automatic TTL purge); data-retention policy as a separate concern is out of scope for v1.
- **Existing auth system**: The feature integrates with the existing JWT-based authentication and role system (Administrator, Standard User, Guest, Auditor) defined in the constitution. No specific data privacy regulations (GDPR, CCPA, HIPAA) are required for v1; standard business data handling applies.
- **Vector storage**: PostgreSQL with `pgvector` extension is used for embedding storage and similarity search (aligned with the constitution's PostgreSQL/SQLAlchemy/Alembic stack).
- **API design**: Follows the constitution's RESTful conventions — resource-oriented endpoints under `/api/chat`, Pydantic schemas for validation, service-layer business logic.
- **Token limits**: Questions exceeding the embedding model's token limit (8191 for `text-embedding-3-small`) are truncated to the limit with a warning in the response metadata.
- **Cache invalidation**: Manual invalidation via admin-only action only; automatic invalidation based on answer age or model version changes is out of scope for v1.

## Clarifications

### Session 2026-10-26

- Q: Does the chat feature need to comply with any data privacy regulations such as GDPR, CCPA, or HIPAA? → A: No specific compliance requirements (standard business data handling applies)
- Q: When the external AI service is unavailable after a cache miss, what should the system do? → A: Return a graceful error to the user (e.g., HTTP 503 Service Unavailable)
- Q: Should cached answers have an explicit retention period / TTL, or persist indefinitely until manually invalidated? → A: Indefinite retention (no automatic TTL purge); manual admin-only invalidation applies
- Q: What observability signals should the chat endpoint emit for operational visibility? → A: Structured JSON logs + key metrics: cache hit rate, p50/p95 latency, embedding/external-API error rates, active users
- Q: Should the chat endpoint enforce rate limiting / throttling? → A: Yes, strict rate limiting configurable (e.g., 10 queries/user/5min)