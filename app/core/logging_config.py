# app/core/logging_config.py
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from typing import Any, Dict
import threading
import os
from dotenv import load_dotenv

load_dotenv()


class CustomJSONFormatter(logging.Formatter):
    """Custom JSON formatter that includes additional context"""

    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": threading.get_ident(),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }

        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = {
                "type": str(record.exc_info[0].__name__),
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_object.update(record.extra_fields)

        return json.dumps(log_object)


def get_log_level() -> int:
    """Get log level from environment variable"""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level, logging.INFO)


def setup_logger(name: str = "app"):
    """Create and configure the application logger"""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Get log level from environment
    log_level = get_log_level()

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    json_formatter = CustomJSONFormatter()
    dev_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        dev_formatter if os.getenv("ENVIRONMENT") == "development" else json_formatter
    )
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File Handler for general logs
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    # File Handler for errors only
    error_handler = TimedRotatingFileHandler(
        log_dir / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    # Development debug log
    if os.getenv("ENVIRONMENT") == "development":
        debug_handler = RotatingFileHandler(
            log_dir / "debug.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        debug_handler.setFormatter(dev_formatter)
        debug_handler.setLevel(logging.DEBUG)
        logger.addHandler(debug_handler)

    return logger


# Create the logger instance
logger = setup_logger()
