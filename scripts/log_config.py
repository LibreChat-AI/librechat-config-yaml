"""Centralized logging configuration for the model fetcher pipeline.

Usage:
    from log_config import setup_logging
    setup_logging()  # Call once at entry point
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line (JSONL) for CI/machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include provider if set via LoggerAdapter extra
        if hasattr(record, "provider"):
            entry["provider"] = record.provider
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable format: 2026-03-16 12:00:00 [INFO] logger: message"""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging.

    Detects CI environment (CI=true or GITHUB_ACTIONS=true) and switches
    to JSON-lines format. Otherwise uses human-readable format.

    Call this ONCE at the program entry point.
    """
    is_ci = (
        os.environ.get("CI", "").lower() in ("true", "1")
        or os.environ.get("GITHUB_ACTIONS", "").lower() in ("true", "1")
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter() if is_ci else HumanFormatter())

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(level)
    # Remove any existing handlers to avoid duplicates
    root.handlers.clear()
    root.addHandler(handler)
