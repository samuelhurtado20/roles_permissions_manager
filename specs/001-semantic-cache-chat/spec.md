# Feature Specification: Semantic Cache Chat

**Feature Branch**: `001-semantic-cache-chat`

**Created**: 2026-10-26

**Status**: Draft (Initial Draft — Clarifications Resolved)

**Input**: User description: Feature Specification: Semantic Cache Chat
1. Executive Summary & Intent
Implement a chat interface capability that evaluates incoming user questions against past conversation history using vector similarity embeddings. If a new question has an 85% or higher cosine similarity to a previously asked question by the same user, return the cached answer immediately to save API latency and cost. Otherwise, route the query to OpenAI, return the response, and store the question-answer pair along with its embedding.

2. Existing Prerequisites & Authorization
User Roles: Extends existing core authorization system.

Role Permissions:

Administrator / Standard User: Full access to query the chat assistant, generate responses, and store history.

Guest / Auditor: Read-only access to past chat logs (cannot initiate new queries or generate embeddings).

3. Core Functional Requirements
User Stories
US-1: Semantic Query Matching

As a Standard User,

I want instantaneous answers to questions I (or my system context) have already asked,

So that I do not incur unnecessary processing latency or duplicate LLM calls.

US-2: Dynamic OpenAI Fallback

As a Standard User,

I want my novel questions routed directly to OpenAI,

So that I receive an up-to-date, accurate AI completion when no high-confidence match exists.

4. Technical Specifications & Workflow
1
1. Capture & Embed Query
Frontend / API Endpoint
Standard User submits a plain-text prompt Q_new.

Check role permissions (Standard User or Administrator).

Generate vector embedding E_new using OpenAI's embedding API (e.g., text-embedding-3-small).

2
2. Similarity Search
Vector Storage / DB Query
Perform a Cosine Similarity lookup comparing E_new against all stored embedding vectors E_stored in the scope.

Compute similarity score:

Similarity= 
∥E 
new

 ∥∥E 
stored

 ∥
E 
new

 ⋅E 
stored

 

 
3
3. Decision Threshold (85% Cutoff)
Business Logic
If Maximum Similarity ≥0.85:

Retrieve stored answer A_cached.

Return A_cached to the user marked with metadata source: "cache".

If Maximum Similarity <0.85:

Send Q_new to OpenAI Chat Completion API (gpt-4o / gpt-4o-mini).

Receive generated answer A_new.

Store (Q_new, E_new, A_new, timestamp, user_id) in the database.

Return A_new marked with metadata source: "openai".

5. Data Model Schema Specification
Field Name    Type    Description
id    UUID / Primary Key    Unique identifier for the chat record
user_id    UUID / Foreign Key    Links to existing User Role entity
question    Text    Original prompt entered by the user
embedding    Vector(1536)    OpenAI embedding representation
answer    Text    Response string (either cached or freshly generated)
similarity_score    Float    The computed cosine score if served from cache
source_type    Enum    CACHE or OPENAI_API
created_at    Timestamp    System creation time

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Semantic Cache Hit (Priority: P1)

A Standard User submits a question that semantically matches a previously asked question (by the same user) at or above the 85% cosine similarity threshold.

**Why this priority**: This is the core value proposition—instant answers without LLM latency or cost for repeat queries.

**Independent Test**: Submit a question, receive an AI-generated answer. Submit a semantically equivalent rephrasing of that same question. Verify the second response is returned instantly, marked as "cache" source, and matches the original answer content.

**Acceptance Scenarios**:

1. **Given** a Standard User has previously asked "What is the capital of France?" and received "Paris is the capital of France.", **When** the same user asks "What's the capital city of France?", **Then** the system returns the cached answer "Paris is the capital of France." with source_type "cache" and similarity_score ≥ 0.85 within 500ms.

2. **Given** a Standard User has an existing cached Q&A pair, **When** they submit a semantically similar question with a typo ("What is teh capital of France?"), **Then** the system returns the cached answer if similarity ≥ 0.85.

3. **Given** a Standard User has multiple cached Q&A pairs, **When** they submit a question similar to multiple entries, **Then** the system returns the answer with the highest similarity score (provided it meets the 0.85 threshold).

---

### User Story 2 - OpenAI Fallback for Novel Questions (Priority: P1)

A Standard User submits a question with no semantic match at or above 85% similarity in their history.

**Why this priority**: Ensures users always get answers to new questions; the cache is an optimization, not a gatekeeper.

**Independent Test**: Submit a brand-new question never seen before by this user. Verify the system routes to OpenAI, returns a generated answer marked "openai" source, and stores the new Q&A with embedding for future cache hits.

**Acceptance Scenarios**:

1. **Given** a Standard User with no prior history asks "Explain quantum entanglement in simple terms", **When** the system computes similarity against their (empty) history and finds no match ≥ 0.85, **Then** the question is sent to OpenAI, a generated answer is returned with source_type "openai", and the Q&A pair with embedding is persisted.

2. **Given** a Standard User has history but asks a completely unrelated question, **When** maximum similarity < 0.85, **Then** the system routes to OpenAI and stores the new interaction.

---

### User Story 3 - Role-Based Access Control (Priority: P1)

Administrators and Standard Users can submit queries and generate responses; Guests and Auditors can only view chat logs.

**Why this priority**: Security and authorization are foundational; incorrect permissions would expose data or allow unauthorized actions.

**Independent Test**: Authenticate as each role type. Verify Standard User/Administrator can submit questions and see responses. Verify Guest/Auditor cannot submit new queries but can view read-only history.

**Acceptance Scenarios**:

1. **Given** an authenticated Standard User, **When** they submit a question via the chat endpoint, **Then** the request is processed (cache check → OpenAI fallback → store).

2. **Given** an authenticated Administrator, **When** they submit a question, **Then** the request is processed identically to Standard User.

3. **Given** an authenticated Guest, **When** they attempt to submit a question, **Then** the system returns a 403 Forbidden error.

4. **Given** an authenticated Auditor, **When** they attempt to submit a question, **Then** the system returns a 403 Forbidden error.

5. **Given** an authenticated Guest, **When** they request their chat history, **Then** the system returns a read-only list of past Q&A pairs without allowing new submissions.

---

### User Story 4 - Per-User Isolation (Priority: P2)

Each user's semantic cache is isolated; similarity searches only match against that user's own history.

**Why this priority**: Privacy and relevance—answers from other users' contexts may be inappropriate or sensitive.

**Independent Test**: Create two Standard Users. User A asks "What's my project deadline?" and gets an answer. User B asks the same question. Verify User B does NOT get User A's cached answer (different context/answer).

**Acceptance Scenarios**:

1. **Given** User A has a cached Q&A, **When** User B submits a semantically identical question, **Then** User B's request is treated as a cache miss (or hits only User B's own history), and User A's answer is never returned to User B.

---

### Edge Cases

- **Empty history**: First question from a new user always routes to OpenAI (no prior embeddings to compare).
- **Exactly at threshold**: A similarity score of exactly 0.85 qualifies as a cache hit.
- **Below threshold but close**: A score of 0.849 routes to OpenAI; the new answer is stored separately (not merged).
- **Embedding generation failure**: If the embedding API is unavailable, the system falls back to OpenAI chat completion directly (no cache check) and stores the result without an embedding for future retry, or returns a graceful error. [NEEDS CLARIFICATION: fallback behavior when embedding API fails]
- **Concurrent identical requests**: Two identical questions submitted simultaneously by the same user—both should be handled correctly (first gets cache miss + OpenAI, second could hit cache if first completed storage). [NEEDS CLARIFICATION: concurrency handling for simultaneous identical queries]
- **Very long questions**: Questions exceeding the embedding model's token limit are truncated or rejected with a clear error. [NEEDS CLARIFICATION: handling of questions exceeding embedding token limits]
- **Answer updates/corrections**: If a user rates a cached answer as incorrect, or an admin flags it, the system should invalidate that cache entry. [NEEDS CLARIFICATION: cache invalidation mechanism for incorrect answers]

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept plain-text questions from authenticated Standard Users and Administrators via a chat API endpoint.
- **FR-002**: System MUST generate a vector embedding for each incoming question using an embedding model.
- **FR-003**: System MUST compute cosine similarity between the new question's embedding and all stored embeddings belonging to the same user.
- **FR-004**: System MUST return the cached answer when maximum cosine similarity ≥ 0.85, with response metadata indicating source_type "cache" and the similarity_score.
- **FR-005**: System MUST route the question to an AI chat completion model when maximum cosine similarity < 0.85 (or no history exists).
- **FR-006**: System MUST return the AI-generated answer with response metadata indicating source_type "openai".
- **FR-007**: System MUST persist every question-answer pair (question, embedding, answer, user_id, timestamp, source_type) for future similarity searches.
- **FR-008**: System MUST enforce role-based access: Standard Users and Administrators can submit queries; Guests and Auditors receive 403 on query submission.
- **FR-009**: System MUST allow Guests and Auditors to retrieve their own chat history in read-only mode.
- **FR-010**: System MUST isolate similarity searches per user—embeddings from other users are never compared or returned.
- **FR-011**: System MUST respond to cache hits within 500ms (target) and cache misses within acceptable OpenAI API latency.
- **FR-012**: System MUST return a graceful error to the user when the embedding API is unavailable (e.g., HTTP 503 Service Unavailable with a clear, user-friendly message), rather than bypassing the cache check or silently returning an incorrect answer.
- **FR-013**: System MUST handle concurrent requests for the same user correctly: when identical or near-identical questions are submitted simultaneously, the first request wins (routes to OpenAI and stores the answer); subsequent concurrent requests that complete after the first has stored its result receive the first request's cached answer, avoiding duplicate OpenAI calls.
- **FR-014**: System MUST handle questions exceeding the embedding model's token limit by truncating the question to the limit (8191 tokens for the default embedding model) and including a warning in the response metadata indicating the question was truncated.
- **FR-015**: System MUST support cache invalidation for incorrect or outdated answers via an explicit admin-only action that removes or flags the chat record so it is excluded from future cache hits.

### Key Entities

- **ChatRecord**: Represents a single question-answer interaction. Attributes: id (UUID), user_id (UUID, FK to User), question (text), embedding (vector, 1536 dimensions), answer (text), similarity_score (float, nullable, populated on cache hits), source_type (enum: CACHE | OPENAI_API), created_at (timestamp).
- **User**: Existing entity from the authorization system. Roles: Administrator, Standard User, Guest, Auditor. Referenced by user_id in ChatRecord.
- **Embedding**: The vector representation of a question (1536-dimension float array from OpenAI text-embedding-3-small or equivalent).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cache hit responses are returned in under 500ms (95th percentile) from request receipt to response delivery.
- **SC-002**: Cache miss responses (OpenAI fallback) complete within the upstream OpenAI API's typical latency plus minimal overhead (target < 5 seconds end-to-end for 95th percentile).
- **SC-003**: Semantic cache hit rate achieves ≥ 30% for users with ≥ 10 prior questions within the same session/domain context.
- **SC-004**: Zero cross-user data leakage: in automated testing with 100 users each asking 50 questions, no user ever receives another user's cached answer.
- **SC-005**: Role enforcement correctness: 100% of Guest/Auditor query submissions return 403; 100% of Standard User/Administrator submissions are processed.
- **SC-006**: Answer accuracy: Cached answers are semantically equivalent to what OpenAI would generate for the same question (validated via human evaluation on a sample of 100 cached responses, ≥ 90% rated equivalent or better).
- **SC-007**: Cost reduction: Embedding + similarity search cost per cache hit is at least 90% lower than a full OpenAI chat completion call.
- **SC-008**: System availability: Chat endpoint returns successful responses (2xx) for ≥ 99.5% of valid requests over a 30-day period.

## Assumptions

- **Embedding model**: OpenAI's `text-embedding-3-small` (1536 dimensions) is used for all embedding generation. This is the default unless otherwise configured.
- **Chat completion model**: OpenAI's `gpt-4o-mini` is the default for fallback generation; `gpt-4o` may be used for higher-quality needs (configurable).
- **Similarity scope**: Similarity search is scoped to the authenticated user's history only (per-user isolation).
- **Threshold**: The 85% cosine similarity threshold is fixed at launch but configurable via environment variable for future tuning.
- **Data retention**: Chat records are retained indefinitely unless a separate data-retention policy is introduced (out of scope for this feature).
- **Existing auth system**: The feature integrates with the existing JWT-based authentication and role system (Administrator, Standard User, Guest, Auditor) defined in the constitution.
- **Vector storage**: PostgreSQL with `pgvector` extension is used for embedding storage and similarity search (aligned with the constitution's PostgreSQL/SQLAlchemy/Alembic stack).
- **API design**: Follows the constitution's RESTful conventions—resource-oriented endpoints under `/api/chat`, Pydantic schemas for validation, service-layer business logic.
- **Error handling**: User-friendly error messages with appropriate HTTP status codes; embedding failures fall back to direct OpenAI call without caching (reasonable default).
- **Concurrency**: Standard database transaction isolation handles concurrent writes; cache reads are eventually consistent (reasonable default).
- **Token limits**: Questions exceeding the embedding model's token limit (8191 for text-embedding-3-small) are truncated to the limit with a warning in the response metadata.
- **Cache invalidation**: Manual invalidation via admin action or user feedback flag is supported; automatic invalidation based on answer age or model version changes is out of scope for v1.