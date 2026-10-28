"""Structured JSON logging utility for observability."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


class JsonFormatter(logging.Formatter):
    """Formatter that outputs structured JSON log records."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include correlation/tracing fields if present
        if getattr(record, "request_id", None):
            log_entry["request_id"] = record.request_id
        if getattr(record, "user_id", None):
            log_entry["user_id"] = record.user_id
        if getattr(record, "endpoint", None):
            log_entry["endpoint"] = record.endpoint
        if getattr(record, "source_type", None):
            log_entry["source_type"] = record.source_type
        if getattr(record, "similarity_score", None):
            log_entry["similarity_score"] = record.similarity_score
        if getattr(record, "latency_ms", None):
            log_entry["latency_ms"] = record.latency_ms
        if getattr(record, "correlation_id", None):
            log_entry["correlation_id"] = record.correlation_id

        return json.dumps(log_entry)


def get_logger(name: str = "semantic_cache") -> logging.Logger:
    """Get a configured structured JSON logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger