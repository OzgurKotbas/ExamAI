"""
utils/logger.py – Structured logging configuration.
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from pythonjsonlogger.jsonlogger import JsonFormatter


class JSONFormatter(JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp if not present
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Add application name
        log_record['application'] = 'examai-backend'
        
        # Add environment
        from config import settings
        log_record['environment'] = settings.APP_ENV


def setup_logging():
    """Setup structured logging configuration."""
    from config import settings
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.is_production:
        # Use JSON formatting in production
        formatter = JSONFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(application)s %(environment)s'
        )
    else:
        # Use readable formatting in development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


# Initialize logging on import
setup_logging()
