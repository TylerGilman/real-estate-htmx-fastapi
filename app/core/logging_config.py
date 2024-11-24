# app/core/logging_config.py
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from typing import Any, Dict
import threading

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
        }
        
        if record.exc_info:
            log_object["exception"] = {
                "type": str(record.exc_info[0].__name__),
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
            
        return json.dumps(log_object)

def create_logger():
    """Create and configure the logger"""
    _logger = logging.getLogger("real_estate_app")
    _logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    _logger.handlers.clear()
    
    # Create formatters
    json_formatter = CustomJSONFormatter()
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(standard_formatter)
    console_handler.setLevel(logging.DEBUG)
    _logger.addHandler(console_handler)
    
    try:
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File Handler
        file_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(logging.INFO)
        _logger.addHandler(file_handler)
        
        # Error File Handler
        error_handler = TimedRotatingFileHandler(
            log_dir / "error.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)
        _logger.addHandler(error_handler)
        
    except Exception as e:
        _logger.error(f"Failed to set up file logging: {str(e)}")
        
    return _logger

# Create the logger instance
logger = create_logger()
