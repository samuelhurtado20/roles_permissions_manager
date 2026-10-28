# FastAPI Backend with PostgreSQL and OpenAI

A production-ready FastAPI backend project with PostgreSQL database integration and OpenAI API connectivity.

## Semantic Cache Chat Feature

This implementation adds a semantic caching layer to the chat API, using vector embeddings and pgvector for PostgreSQL to provide instant cached responses for repeated or semantically similar questions.

### Architecture

- **Vector Embeddings**: OpenAI `text-embedding-3-small` model generates 1536-dimensional embeddings for each question
- **Cosine Similarity**: 85% threshold determines when a cached answer can be returned
- **pgvector**: PostgreSQL extension for efficient vector similarity search with ivfflat indexing
- **Service Layer**: Business logic separated into `ChatService` with methods for similarity computation, cache checking, and record storage
- **Concurrency**: First-request-wins locking pattern prevents duplicate processing
- **Circuit Breaker**: Graceful degradation when OpenAI API is unavailable

### Setup

The semantic cache feature is automatically included after running the Phase 1-10 implementation tasks. No additional configuration is required beyond the existing environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_MODEL` | OpenAI embedding model | "text-embedding-3-small" |
| `EMBEDDING_DIMENSIONS` | Embedding vector dimensions | 1536 |
| `SIMILARITY_THRESHOLD` | Cosine similarity threshold for cache hits | 0.85 |
| `RATE_LIMIT_REQUESTS` | Max requests per user window | 10 |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | 300 |

## Project Structure

```
openrouter/
├── app/                 # Main application code
│   ├── api/            # API routes and dependencies
│   │   ├── deps.py     # Dependency providers
│   │   └── routes/     # API endpoint routers
│   │       ├── __init__.py
│   │       ├── users.py # User management endpoints
│   │       ├── openai.py # OpenAI integration endpoints
│   │       └── chat.py  # Semantic cache chat endpoints
│   ├── core/           # Core configuration and utilities
│   │   ├── __init__.py
│   │   └── config.py   # Application settings
│   ├── db/             # Database configuration and models
│   │   ├── __init__.py
│   │   └── session.py  # Database session management
│   ├── models/         # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py     # User model
│   ├── schemas/        # Pydantic schemas for validation
│   │   ├── __init__.py
│   │   ├── user.py     # User schemas
│   │   └── chat.py     # Chat request/response schemas
│   ├── services/       # Business logic services
│   │   ├── __init__.py
│   │   ├── openai_service.py # OpenAI API wrapper
│   │   └── chat.py     # Chat service with semantic caching
│   ├── main.py         # FastAPI application entry point
│   └── __init__.py
├── alembic/            # Database migration files
│   ├── versions/       # Migration versions (generated)
│   │   ├── 0001_initial_schema.py
│   │   └── 0002_semantic_cache_chat_schema.py
│   ├── env.py          # Alembic environment
│   └── script.py.mako  # Migration template
├── alembic.ini         # Alembic configuration
├── docker-compose.yml  # Docker Compose for local development
├── Dockerfile          # Container image definition
├── .env                # Environment variables (local)
├── .env.example        # Example environment variables
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── specs/              # Feature specifications and task tracking
    └── 001-semantic-cache-chat/
        ├── plan.md
        ├── spec.md
        ├── data-model.md
        ├── contracts/
        │   └── chat-api.md
        ├── quickstart.md
        ├── research.md
        └── tasks.md
```

## Features

- **FastAPI** web framework with automatic OpenAPI documentation
- **PostgreSQL** database with SQLAlchemy ORM and Alembic migrations
- **OpenAI API** integration for text generation and embeddings
- **User authentication** system with password hashing and JWT tokens
- **Semantic cache** with vector similarity search for instant cached responses
- **Role-based access control** (ADMIN, STANDARD, GUEST, AUDITOR)
- **Rate limiting** (configurable per-user sliding window)
- **Circuit breaker** pattern for OpenAI API resilience
- **Structured JSON logging** with correlation_id for request tracing
- **Metrics middleware** for latency tracking (p50/p95, error rates)
- **Docker support** for easy deployment
- **Environment-based configuration** using pydantic-settings

## API Endpoints

### Users
- `POST /users/` - Create a new user
- `GET /users/` - List users (with pagination)
- `GET /users/{user_id}` - Get a specific user

### OpenAI
- `POST /openai/generate` - Send a prompt to OpenAI and get a response

### Chat (Semantic Cache)
- `POST /chat/` - Submit a question (returns cached answer or routes to OpenAI)
- `GET /chat/history` - Get paginated chat history
- `DELETE /chat/{record_id}` - Invalidate a cache record (admin only)

### Roles
- `POST /roles/` - Create a new role
- `GET /users/` - List roles (with pagination)
- `GET /roles/{role_id}` - Get a specific role
- `GET /roles/name/{role_name}` - Get a role by name
- `PUT /roles/{role_id}` - Update a role
- `DELETE /roles/{role_id}` - Delete a role

### Permissions
- `POST /permissions/` - Create a new permission
- `GET /permissions/` - List permissions (with pagination)
- `GET /permissions/{permission_id}` - Get a specific permission
- `GET /permissions/name/{permission_name}` - Get a permission by name
- `PUT /permissions/{permission_id}` - Update a permission
- `DELETE /permissions/{permission_id}` - Delete a permission

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | "FastAPI Backend" |
| `APP_ENV` | Environment (development/staging/production) | "development" |
| `APP_DEBUG` | Enable debug mode | true |
| `HOST` | Server host | "0.0.0.0" |
| `PORT` | Server port | 8000 |
| `DATABASE_URL` | PostgreSQL connection string | postgresql+psycopg2://postgres:postgres@localhost:5432/fastapi_db |
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `OPENAI_MODEL` | OpenAI model to use | "gpt-4o-mini" |
| `EMBEDDING_MODEL` | OpenAI embedding model | "text-embedding-3-small" |
| `EMBEDDING_DIMENSIONS` | Embedding vector dimensions | 1536 |
| `SIMILARITY_THRESHOLD` | Cosine similarity threshold for cache hits | 0.85 |
| `SECRET_KEY` | Secret key for JWT tokens | "change-me-in-production" |
| `ALGORITHM` | JWT algorithm | "HS256" |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 30 |
| `RATE_LIMIT_REQUESTS` | Max requests per user window | 10 |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | 300 |

## Database Migrations

To create a new migration after modifying models:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```

To rollback the last migration:
```bash
alembic downgrade -1
```

The semantic cache migration (0002) creates the `chat_records` table with:
- `embedding` column as pgvector Vector(1536)
- ivfflat index on `(user_id, embedding)` for efficient per-user similarity search
- `chat_record_source_type` enum type for source tracking

## Testing

Run tests with pytest:
```bash
pytest
```

All 28 tests pass across unit, contract, and integration test suites.

## License

MIT