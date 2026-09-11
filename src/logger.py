"""Centralized structured logging module for ATS Core MVP."""
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "ats_system.log"


class ISO8601Formatter(logging.Formatter):
    """Formatter that outputs timestamps in ISO 8601 format."""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat()


def get_logger(name: str = "ats_core") -> logging.Logger:
    """Return a configured logger with console and rotating file handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s"
    formatter = ISO8601Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler (max 10MB, 5 backups)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        # Fallback to console only if file access fails
        pass

    return logger


logger = get_logger("ats_core")
