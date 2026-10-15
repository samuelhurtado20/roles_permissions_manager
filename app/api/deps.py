from app.services.openai_service import OpenAIService


def get_openai_service() -> OpenAIService:
    """Dependency for OpenAI service."""
    return OpenAIService()