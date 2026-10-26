# Data Model: Semantic Cache Chat

## ChatRecord Model

### Definition
The `ChatRecord` represents a single question-answer interaction in the system. It is stored in PostgreSQL with the `pgvector` extension for embedding-based similarity searches.

### Database Table: `chat_records`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, default: gen_random_uuid() | Unique identifier for the chat record |
| `user_id` | UUID | FK → `users.id`, NOT NULL | Links to the associated User entity |
| `question` | TEXT | NOT NULL | The original prompt entered by the user |
| `embedding` | vector(1536) | NOT NULL | OpenAI `text-embedding-3-small` representation |
| `answer` | TEXT | NOT NULL | Response string (either cached or freshly generated) |
| `similarity_score` | FLOAT | NULLABLE | The computed cosine score when served from cache; NULL for openai-sourced answers |
| `source_type` | ENUM(CACHE, OPENAI_API) | NOT NULL | Indicates where the answer originated |
| `created_at` | TIMESTAMP | NOT NULL, default: now() | System creation timestamp |

### Indexes

- **Primary Key**: `id`
- **Foreign Key**: `user_id` → `users.id` with CASCADE on delete
- **Similarity Index**: `GIN` or `IVFFlat` index on `embedding` column (1536 dimensions) for cosine similarity search
  - Index name: `idx_chat_records_embedding_cosine`
  - Includes `user_id` in the search scope to enforce per-user isolation
- **Frequent Query Index**: `idx_chat_records_user_created` on `(user_id, created_at DESC)` for paginated history retrieval

### User Model (reference)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `email` | TEXT | UNIQUE, NOT NULL | User email address |
| `username` | TEXT | UNIQUE | Display name |
| `role` | ENUM(ADMIN, STANDARD, GUEST, AUDITOR) | NOT NULL | User role for authorization |
| `created_at` | TIMESTAMP | NOT NULL, default: now() | Account creation timestamp |

### Relationships

- **User ↔ ChatRecord**: One-to-Many (one user has many chat records)
  - User.chat_records: List of all their Q&A interactions
  - ChatRecord.user: The user who owns this record

### State Transitions

| From | To | Trigger |
|------|-----|---------|
| — | `CACHE | OPENAI_API` | New question submitted |
| `CACHE | OPENAI_API` | `CACHE | OPENAI_API` | New question processed (updates history) |
| `CACHE | OPENAI_API` | Flagged/Removed | Admin invalidation action |

### Pydantic Schemas

#### ChatRequest

| Field | Type | Description |
|-------|------|-------------|
| `question` | str | The user's question text |

#### ChatResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Record ID |
| `question` | str | The submitted question |
| `answer` | str | The generated/cached answer |
| `source_type` | str | "cache" or "openai_api" |
| `similarity_score` | float | Similarity score if cache hit; NULL otherwise |
| `created_at` | datetime | When the record was created |

#### ChatHistoryResponse

| Field | Type | Description |
|-------|------|-------------|
| `records` | list[ChatResponse] | Paginated list of user's chat history |
| `total` | int | Total count of records |
| `page` | int | Current page number |
| `pages` | int | Total number of pages |

## Embedding Model Details

- **Model**: `text-embedding-3-small` (OpenAI)
- **Dimensions**: 1536
- **Similarity**: Cosine similarity (≥0.85 threshold for cache hit)
- **Token limit**: 8191 tokens per question
- **Truncation**: Questions exceeding limit are truncated with warning metadata