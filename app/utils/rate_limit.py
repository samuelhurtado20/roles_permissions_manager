"""Rate limiting decorator using in-memory sliding window store."""

import time
from collections import defaultdict
from typing import Callable, Dict, List

from fastapi import HTTPException, status

from app.core.config import settings


class RateLimiter:
    """In-memory sliding window rate limiter per user."""

    def __init__(self):
        self._requests: Dict[int, List[float]] = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        """Check if the user's request is within the rate limit window.

        Returns True if allowed, False if the limit is exceeded.
        """
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW

        # Prune old timestamps outside the window
        self._requests[user_id] = [
            ts for ts in self._requests[user_id] if ts > window_start
        ]

        if len(self._requests[user_id]) >= settings.RATE_LIMIT_REQUESTS:
            return False

        self._requests[user_id].append(now)
        return True

    def retry_after(self, user_id: int) -> int:
        """Return seconds until the rate limit window resets for this user."""
        if not self._requests.get(user_id):
            return settings.RATE_LIMIT_WINDOW

        oldest = min(self._requests[user_id])
        return max(int(oldest + settings.RATE_LIMIT_WINDOW - time.time()), 1)


# Singleton instance
rate_limiter = RateLimiter()


def rate_limit(user_id: int):
    """Decorator/dependency to enforce per-user rate limiting.

    Raises HTTPException 429 with Retry-After header when limit exceeded.
    """
    if not rate_limiter.is_allowed(user_id):
        retry_after = rate_limiter.retry_after(user_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )