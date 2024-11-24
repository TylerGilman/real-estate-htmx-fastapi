import os
from dotenv import load_dotenv
from functools import lru_cache
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Project Info
    PROJECT_NAME = "Real Estate Management"
    VERSION = "1.0.0"
    
    # Base paths
    APP_DIR = Path(__file__).resolve().parent.parent  # app folder
    BASE_DIR = APP_DIR.parent  # project root
    TEMPLATES_DIR = APP_DIR / "templates"
    STATIC_DIR = APP_DIR / "static"
    
    # Logging settings
    LOG_DIR = BASE_DIR / "logs"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "json"  # or "text" for plain text logs
    LOG_ROTATION = "10 MB"
    LOG_RETENTION = "30 days"
    
    # Database settings
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "real_estate")
    
    # Construct database URL
    @property
    def DATABASE_URL(self):
        return (
            f"mysql+mysqlconnector://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
    
    # Template configuration
    TEMPLATES_AUTO_RELOAD = True
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Session configuration
    SESSION_COOKIE_NAME = "real_estate_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("ENVIRONMENT", "development") == "production"
    
    # Development settings
    DEBUG = os.getenv("ENVIRONMENT", "development") == "development"
    
    # Logging configuration dictionary
    @property
    def LOGGING_CONFIG(self):
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "app.core.logging_config.CustomJSONFormatter",
                },
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard" if self.DEBUG else "json",
                    "stream": "ext://sys.stdout",
                    "level": self.LOG_LEVEL,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "json",
                    "filename": str(self.LOG_DIR / "app.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "level": self.LOG_LEVEL,
                },
                "error_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "formatter": "json",
                    "filename": str(self.LOG_DIR / "error.log"),
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 30,
                    "level": "ERROR",
                },
            },
            "loggers": {
                "real_estate_app": {
                    "handlers": ["console", "file", "error_file"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
            },
        }

@lru_cache()
def get_settings():
    """Cache and return settings instance"""
    return Settings()

settings = get_settings()

# Create logs directory if it doesn't exist
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
