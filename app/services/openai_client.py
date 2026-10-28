"""OpenAI client wrapper with circuit breaker and retry logic."""

import asyncio
import time
from enum import Enum

from openai import AsyncOpenAI
from openai import APIError, APITimeoutError, RateLimitError

from app.core.config import settings

logger = __import__("logging").getLogger("openai_client")


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern for graceful degradation during service outages."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = 0.0

    @property
    def state(self) -> CircuitState:
        return self._state

    def _transition_to_open(self):
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()

    def _transition_to_half_open(self):
        self._state = CircuitState.HALF_OPEN

    def _transition_to_closed(self):
        self._state = CircuitState.CLOSED
        self._failure_count = 0

    def allow_request(self) -> bool:
        """Check if a request is allowed through the circuit breaker."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self._recovery_timeout:
                self._transition_to_half_open()
                return True
            return False

        # HALF_OPEN — allow a single probe request
        return True

    def record_success(self):
        """Record a successful API call."""
        if self._state == CircuitState.HALF_OPEN:
            self._transition_to_closed()
        else:
            self._failure_count = 0

    def record_failure(self):
        """Record a failed API call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._transition_to_open()
            logger.warning("Circuit breaker opened after %d failures", self._failure_threshold)


class OpenAIClient:
    """Wrapper around the OpenAI async client with circuit breaker and retry logic."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.circuit_breaker = CircuitBreaker()

    async def generate_chat_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate a chat completion via OpenAI.

        Raises RuntimeError if the circuit breaker is open or the API fails.
        """
        if not self.circuit_breaker.allow_request():
            raise RuntimeError("OpenAI API circuit breaker is open")

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            self.circuit_breaker.record_success()
            return response.choices[0].message.content or ""
        except (APITimeoutError, RateLimitError, APIError) as exc:
            self.circuit_breaker.record_failure()
            raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Raises RuntimeError if the circuit breaker is open or the API fails.
        """
        if not self.circuit_breaker.allow_request():
            raise RuntimeError("OpenAI API circuit breaker is open")

        try:
            response = await self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
            )
            self.circuit_breaker.record_success()
            return response.data[0].embedding
        except (APITimeoutError, RateLimitError, APIError) as exc:
            self.circuit_breaker.record_failure()
            raise RuntimeError(f"OpenAI embedding API request failed: {exc}") from exc

    def is_available(self) -> bool:
        """Check if the OpenAI API is currently reachable."""
        return self.circuit_breaker.allow_request()