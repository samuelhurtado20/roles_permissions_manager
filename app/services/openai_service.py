from openai import AsyncOpenAI

from app.core.config import settings


class OpenAIService:
    """Service for interacting with the OpenAI API."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate(self, prompt: str) -> str:
        """Generate a completion from OpenAI."""
        if not settings.OPENAI_API_KEY:
            return "OpenAI API key not configured."

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""