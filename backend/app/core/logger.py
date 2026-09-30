"""Structured and PII-safe logging setup for the Parakh backend."""

import logging
import sys
from backend.app.core.safety import mask_pii

# Reconfigure stdout/stderr to utf-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class PIIMaskingFormatter(logging.Formatter):
    """Custom formatter that automatically masks PII in log records."""

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return mask_pii(formatted)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a clean format including request IDs and PII redaction."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PIIMaskingFormatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    # Quieten noisy third-party loggers
    for name in ("httpx", "httpcore", "chromadb", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)


# Create a module-level logger for use in other modules
logger = logging.getLogger("parakh")
