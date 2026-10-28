"""Error handling middleware for consistent API error responses."""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("errors")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware that catches unhandled exceptions and returns consistent JSON errors."""

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled exception during request processing")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )