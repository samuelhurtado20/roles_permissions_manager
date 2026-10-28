"""Metric collection middleware for operational observability."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger

logger = get_logger("metrics")


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks request latency and endpoint metrics."""

    def __init__(self, app):
        super().__init__(app)
        self._request_counts: dict[str, int] = defaultdict(int)
        self._latencies: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        response = await call_next(request)

        latency_ms = (time.time() - start_time) * 1000
        endpoint = request.url.path
        method = request.method
        key = f"{method} {endpoint}"

        self._request_counts[key] += 1
        self._latencies[key].append(latency_ms)

        # Log latency metric
        logger.info(
            "Request completed",
            extra={
                "endpoint": endpoint,
                "method": method,
                "latency_ms": round(latency_ms, 2),
                "status_code": response.status_code,
            },
        )

        return response

    def get_metrics(self) -> dict:
        """Return aggregated metrics snapshot."""
        metrics = {}
        for key, latencies in self._latencies.items():
            sorted_lat = sorted(latencies)
            count = len(sorted_lat)
            metrics[key] = {
                "request_count": self._request_counts[key],
                "latency_p50_ms": round(
                    sorted_lat[int(count * 0.50)] if count else 0, 2
                ),
                "latency_p95_ms": round(
                    sorted_lat[int(count * 0.95)] if count else 0, 2
                ),
                "avg_latency_ms": round(sum(sorted_lat) / count, 2) if count else 0,
            }
        return metrics