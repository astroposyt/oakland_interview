import logging
import logging.config
import json
import os
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    A custom formatter that outputs logs as JSON. 
    Crucial for production environments so log aggregators can parse fields.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging() -> None:
    """
    Initializes the logging configuration. 
    Called exactly once during application startup.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()


    if env == "production":
        formatter = "json"
    else:
        formatter = "standard"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(module)s:%(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {

            "oakland": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
          
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)

def get_logger(name: str) -> logging.Logger:
    """
    Dependency Injection mechanism for logging.
    Ensures all app loggers sit under the 'oakland.' namespace.
    """
    if not name.startswith("oakland."):
        name = f"oakland.{name}"
    return logging.getLogger(name)