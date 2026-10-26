# Quickstart: Semantic Cache Chat

This guide provides runnable validation scenarios to prove the semantic cache chat feature works end-to-end.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development without Docker)
- OpenAI API key configured in `.env`

## Environment Setup

### Option 1: Using Docker (Recommended)

```bash
# Clone and enter the project
git clone <repo-url>
cd openrouter

# Start PostgreSQL with pgvector extension
docker-compose up -d

# Wait for services to be ready
docker-compose exec postgres pg_isready

# Apply migrations
docker-compose exec web alembic upgrade head
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy example env and configure
cp .env.example .env
# Set your OpenAI API key in .env

# Apply migrations
alembic upgrade head
```

## Validation Scenarios

### 1. Cache Hit (Semantic Similarity)

**Goal**: Verify that a question semantically similar to a previous one returns a cached answer.

```bash
# 1. Submit first question
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?"}'

# 2. Submit semantically similar rephrasing
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What's the capital city of France?"}'

# Expected: Second response has source_type "cache" and similarity_score ≥ 0.85
```

### 2. OpenAI Fallback (Novel Question)

**Goal**: Verify that a new question with no semantic match routes to OpenAI.

```bash
# Submit a brand-new question
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain quantum entanglement in simple terms"}'

# Expected: Response has source_type "openai_api" and similarity_score null
```

### 3. Role-Based Access Control

**Goal**: Verify that Guests and Auditors cannot submit questions.

```bash
# Attempt as Guest (should return 403)
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <guest-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'

# Expected: HTTP 403 Forbidden
```

```bash
# Attempt as Auditor (should return 403)
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <auditor-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'

# Expected: HTTP 403 Forbidden
```

### 4. Per-User Isolation

**Goal**: Verify that User A's cached answers are not returned to User B.

```bash
# User A submits question
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <user-a-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is my project deadline?"}'

# User B submits the same question (different user)
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <user-b-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is my project deadline?"}'

# Expected: User B does NOT get User A's cached answer
```

### 5. Cache Invalidation (Admin Only)

**Goal**: Verify that an admin can invalidate a specific cached record.

```bash
# Admin invalidates a cache record
curl -X DELETE "http://localhost:8000/api/chat/{record_id}" \
  -H "Authorization: Bearer <admin-jwt-token>"

# Expected: HTTP 204 No Content
```

```bash
# Non-admin attempts invalidation (should return 403)
curl -X DELETE "http://localhost:8000/api/chat/{record_id}" \
  -H "Authorization: Bearer <standard-user-jwt-token>"

# Expected: HTTP 403 Forbidden
```

### 6. Rate Limiting

**Goal**: Verify that exceeding the rate limit returns HTTP 429.

```bash
# Send multiple rapid requests
for i in {1..15}; do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST "http://localhost:8000/api/chat" \
    -H "Authorization: Bearer <user-jwt-token>" \
    -H "Content-Type: application/json" \
    -d '{"question": "Rate limit test question"}'
done

# Expected: First 10 return 200/201, subsequent return 429
```

## Running Tests

```bash
# Run unit and contract tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## Troubleshooting

- **pgvector not available**: Ensure PostgreSQL is started with `pgvector` extension enabled
- **OpenAI API key missing**: Check `.env` file has `OPENAI_API_KEY` set
- **JWT token invalid**: Ensure token is properly formatted and signed with the correct SECRET_KEY
- **Similarity search slow**: Consider adding an `ivfflat` index on the embedding column