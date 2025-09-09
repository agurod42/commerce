"""
Logging configuration for wholesale agent.
Production-ready logging with structured output and error tracking.
"""
import os
import sys
import logging
import logging.handlers
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'query'):
            log_entry['query'] = record.query
        if hasattr(record, 'response_time'):
            log_entry['response_time_ms'] = record.response_time
        
        return json.dumps(log_entry, default=str)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format basic message
        formatted = f"{color}[{record.levelname}]{reset} {timestamp} {record.name}: {record.getMessage()}"
        
        # Add location info for errors
        if record.levelno >= logging.ERROR:
            formatted += f" ({record.module}.{record.funcName}:{record.lineno})"
        
        # Add exception traceback
        if record.exc_info:
            formatted += f"\\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logger(name: str, level: str = "INFO", 
                log_dir: Optional[str] = None,
                structured: bool = False,
                console_output: bool = True) -> logging.Logger:
    """
    Set up a logger with appropriate handlers.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to ./logs)
        structured: Whether to use structured JSON logging
        console_output: Whether to output to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set level
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create log directory
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), 'logs')
    
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # File handler for all logs
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    
    if structured:
        file_handler.setFormatter(StructuredFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    logger.addHandler(file_handler)
    
    # Separate error log file
    error_file = os.path.join(log_dir, f"{name}_errors.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    
    if structured:
        error_handler.setFormatter(StructuredFormatter())
    else:
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
        ))
    
    logger.addHandler(error_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if structured:
            console_handler.setFormatter(StructuredFormatter())
        else:
            # Use colored formatter for development
            if os.getenv('ENVIRONMENT', 'development') == 'development':
                console_handler.setFormatter(ColoredConsoleFormatter())
            else:
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
        
        logger.addHandler(console_handler)
    
    return logger


class LoggingMixin:
    """Mixin class to add logging capabilities to any class."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_query(self, query: str, response_time: Optional[float] = None, 
                  user_id: Optional[str] = None, session_id: Optional[str] = None):
        """Log a user query with metadata."""
        extra = {
            'query': query,
            'response_time': response_time,
            'user_id': user_id,
            'session_id': session_id
        }
        
        self.logger.info("User query processed", extra=extra)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an error with context."""
        extra = context or {}
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True, extra=extra)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        extra = {
            'operation': operation,
            'duration_ms': duration * 1000,
            **kwargs
        }
        
        self.logger.info(f"Performance: {operation}", extra=extra)


class AuditLogger:
    """Specialized logger for audit trails."""
    
    def __init__(self, log_dir: Optional[str] = None):
        self.logger = setup_logger(
            'audit',
            level='INFO',
            log_dir=log_dir,
            structured=True,
            console_output=False
        )
    
    def log_user_action(self, action: str, user_id: Optional[str] = None,
                       session_id: Optional[str] = None, **kwargs):
        """Log user actions for audit purposes."""
        extra = {
            'action': action,
            'user_id': user_id,
            'session_id': session_id,
            **kwargs
        }
        
        self.logger.info(f"User action: {action}", extra=extra)
    
    def log_system_event(self, event: str, **kwargs):
        """Log system events."""
        extra = {
            'event': event,
            **kwargs
        }
        
        self.logger.info(f"System event: {event}", extra=extra)
    
    def log_data_access(self, table: str, operation: str, 
                       user_id: Optional[str] = None, **kwargs):
        """Log database access for compliance."""
        extra = {
            'table': table,
            'operation': operation,
            'user_id': user_id,
            **kwargs
        }
        
        self.logger.info(f"Data access: {operation} on {table}", extra=extra)


def configure_root_logger(level: str = "INFO", structured: bool = False):
    """Configure the root logger for the entire application."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set root level
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


# Global audit logger instance
audit_logger = AuditLogger()


# Error tracking utilities
class ErrorTracker:
    """Track and aggregate errors for monitoring."""
    
    def __init__(self):
        self.error_counts = {}
        self.logger = setup_logger('error_tracker', structured=True)
    
    def track_error(self, error_type: str, error_message: str, 
                   context: Optional[Dict[str, Any]] = None):
        """Track an error occurrence."""
        error_key = f"{error_type}:{error_message}"
        
        if error_key not in self.error_counts:
            self.error_counts[error_key] = {
                'count': 0,
                'first_seen': datetime.now(),
                'last_seen': datetime.now(),
                'context': context or {}
            }
        
        self.error_counts[error_key]['count'] += 1
        self.error_counts[error_key]['last_seen'] = datetime.now()
        
        # Log the error
        self.logger.error(
            f"Error tracked: {error_type} - {error_message}",
            extra={
                'error_type': error_type,
                'error_message': error_message,
                'count': self.error_counts[error_key]['count'],
                'context': context
            }
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors."""
        return {
            'total_unique_errors': len(self.error_counts),
            'total_error_occurrences': sum(e['count'] for e in self.error_counts.values()),
            'top_errors': sorted(
                [
                    {
                        'error': key,
                        'count': data['count'],
                        'first_seen': data['first_seen'].isoformat(),
                        'last_seen': data['last_seen'].isoformat()
                    }
                    for key, data in self.error_counts.items()
                ],
                key=lambda x: x['count'],
                reverse=True
            )[:10]
        }


# Global error tracker instance
error_tracker = ErrorTracker()