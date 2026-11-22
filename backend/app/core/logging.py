import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# Context variable to hold the current request ID across async tasks
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id_ctx", default=None)


class JSONLogFormatter(logging.Formatter):
    """Formats log records as structured single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": req_id,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class TextLogFormatter(logging.Formatter):
    """Human-readable text log formatter for local interactive development."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        req_part = f"[{req_id}] " if req_id else ""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        base = (
            f"{timestamp} | {record.levelname:<8} | {req_part}{record.name}: {record.getMessage()}"
        )
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure root logger with structured output handler."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        stream_handler.setFormatter(JSONLogFormatter())
    else:
        stream_handler.setFormatter(TextLogFormatter())

    root_logger.addHandler(stream_handler)

    # Adjust external noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance with the specified name."""
    return logging.getLogger(name)
