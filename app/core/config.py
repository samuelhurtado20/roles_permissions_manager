from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    APP_NAME: str = "FastAPI Backend"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/fastapi_db"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Semantic cache settings
    SIMILARITY_THRESHOLD: float = 0.85
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_TOKEN_LIMIT: int = 8191

    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()