# FastAPI Backend with PostgreSQL and OpenAI

A production-ready FastAPI backend project with PostgreSQL database integration and OpenAI API connectivity.

## Project Structure

```
openrouter/
├── app/                 # Main application code
│   ├── api/            # API routes and dependencies
│   │   ├── deps.py     # Dependency providers
│   │   └── routes/     # API endpoint routers
│   │       ├── __init__.py
│   │       ├── users.py # User management endpoints
│   │       └── openai.py # OpenAI integration endpoints
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
│   │   └── openai.py   # OpenAI request/response schemas
│   ├── services/       # Business logic services
│   │   ├── __init__.py
│   │   └── openai_service.py # OpenAI API wrapper
│   ├── main.py         # FastAPI application entry point
│   └── __init__.py
├── alembic/            # Database migration files
│   ├── versions/       # Migration versions (generated)
│   ├── env.py          # Alembic environment
│   └── script.py.mako  # Migration template
├── alembic.ini         # Alembic configuration
├── docker-compose.yml  # Docker Compose for local development
├── Dockerfile          # Container image definition
├── .env                # Environment variables (local)
├── .env.example        # Example environment variables
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Features

- **FastAPI** web framework with automatic OpenAPI documentation
- **PostgreSQL** database with SQLAlchemy ORM and Alembic migrations
- **OpenAI API** integration for text generation
- **User authentication** system with password hashing
- **Docker support** for easy deployment
- **Environment-based configuration** using python-dotenv
- **RESTful API design** with proper status codes and validation

## Setup Instructions

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional, for containerized setup)
- PostgreSQL (if not using Docker)

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your settings:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to add your OpenAI API key and adjust database credentials if needed.

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Setup

1. Copy `.env.example` to `.env` and configure your settings
2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## API Endpoints

### Users
- `POST /users/` - Create a new user
- `GET /users/` - List users (with pagination)
- `GET /users/{user_id}` - Get a specific user

### OpenAI
- `POST /openai/generate` - Send a prompt to OpenAI and get a response

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
| `SECRET_KEY` | Secret key for JWT tokens | "change-me-in-production" |
| `ALGORITHM` | JWT algorithm | "HS256" |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 30 |

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

## Testing

Run tests with pytest:
```bash
pytest
```

## License

MIT


#$env:PYTHONPATH="."; .\.venv\Scripts\alembic.exe upgrade head`