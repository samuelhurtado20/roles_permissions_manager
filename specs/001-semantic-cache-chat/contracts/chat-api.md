# Chat API Contracts

## API Endpoints

All chat-related endpoints are under `/api/chat` prefix. Authentication is required via JWT bearer token in the `Authorization` header for POST and DELETE endpoints. Guests and Auditors may receive historical data from GET endpoints.

---

## 1. Submit Question (POST /api/chat)

Submits a new question. Returns either a cached answer (from the user's history with ≥85% similarity) or generates a new answer via the external AI service.

### Permissions
- **Allowed**: Administrator, Standard User
- **Forbidden (403)**: Guest, Auditor

### Request

```http
POST /api/chat
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

```json
{
  "question": "What is the capital of France?"
}
```

**Request Schema** (`ChatRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The user's question (max 5000 characters) |

### Response

**200 OK** (Cache Hit)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What is the capital of France?",
  "answer": "Paris is the capital of France.",
  "source_type": "cache",
  "similarity_score": 0.92,
  "created_at": "2026-10-26T14:30:00Z"
}
```

**201 Created** (Cache Miss — New Answer Generated)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What is the capital of France?",
  "answer": "Paris is the capital of France.",
  "source_type": "openai_api",
  "similarity_score": null,
  "created_at": "2026-10-26T14:30:00Z"
}
```

**403 Forbidden** — Guest or Auditor attempts to submit

```json
{
  "detail": "Insufficient permissions to submit questions"
}
```

**429 Too Many Requests** — Rate limit exceeded (default: 10 queries per user per 5 minutes)

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

**503 Service Unavailable** — Embedding API or External AI service unavailable

```json
{
  "detail": "The AI service is temporarily unavailable. Please try again in a few minutes."
}
```

---

## 2. Retrieve Chat History (GET /api/chat/history)

Retrieves a paginated list of the authenticated user's (or specified user's for admins) chat records.

### Permissions
- **Allowed**: Administrator, Standard User, Guest, Auditor
- Guests and Auditors can only view their own history.

### Request

```http
GET /api/chat/history?limit=20&offset=0
Authorization: Bearer <jwt_token>
```

| Query Parameter | Type | Required | Default | Description |
|----------------|------|----------|---------|-------------|
| `limit` | int | No | 20 | Number of records to return (max: 100) |
| `offset` | int | No | 0 | Number of records to skip |

### Response

**200 OK**

```json
{
  "records": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "question": "What is the capital of France?",
      "answer": "Paris is the capital of France.",
      "source_type": "openai_api",
      "similarity_score": null,
      "created_at": "2026-10-26T14:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

**Response Schema** (`ChatHistoryResponse`):

| Field | Type | Description |
|-------|------|-------------|
| `records` | list[ChatResponse] | Chat records for the user |
| `total` | int | Total number of records for the user |
| `page` | int | Current page number (1-based) |
| `pages` | int | Total number of pages |

---

## 3. Invalidate Cache Record (DELETE /api/chat/{record_id})

Removes or flags a specific chat record from being used for cache hits.

### Permissions
- **Allowed**: Administrator
- **Forbidden (403)**: Standard User, Guest, Auditor

### Request

```http
DELETE /api/chat/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <jwt_token>
```

### Response

**204 No Content** — Record successfully invalidated

**403 Forbidden** — Non-admin attempts invalidation

```json
{
  "detail": "Only administrators can invalidate cache records"
}
```

**404 Not Found** — Record does not exist

```json
{
  "detail": "Chat record not found"
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /api/chat | 10 requests | 5 minutes per user |
| GET /api/chat/history | 60 requests | 1 minute per user |
| DELETE /api/chat/{id} | 5 requests | 1 minute per admin |

Exceeding limits returns HTTP **429** with `Retry-After` header (seconds).

---

## Metadata Fields

Responses include the following metadata when applicable:

| Field | Present When | Description |
|-------|-------------|-------------|
| `similarity_score` | Cache hits only | Cosine similarity score (≥0.85) |
| `source_type` | All responses | "cache" or "openai_api" |
| `created_at` | All responses | ISO 8601 timestamp of record creation |