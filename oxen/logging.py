#!/usr/bin/env python3
"""
OxenORM Logging System

Provides comprehensive logging with structured logging, performance monitoring,
and production-ready log management.
"""

import logging
import logging.handlers
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum

from .config import get_config


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Logging context information"""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    operation: Optional[str] = None
    duration: Optional[float] = None
    database: Optional[str] = None
    query_count: int = 0
    error_count: int = 0


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class PerformanceLogger:
    """Performance logging and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('oxen.performance')
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
    
    def log_query(self, sql: str, duration: float, success: bool = True):
        """Log database query performance"""
        self.logger.info(
            "Database query executed",
            extra={
                'sql': sql,
                'duration': duration,
                'success': success,
                'operation': 'query'
            }
        )
        
        # Track metrics
        if 'query_durations' not in self.metrics:
            self.metrics['query_durations'] = []
        self.metrics['query_durations'].append(duration)
        
        if 'total_queries' not in self.counters:
            self.counters['total_queries'] = 0
        self.counters['total_queries'] += 1
        
        if not success:
            if 'failed_queries' not in self.counters:
                self.counters['failed_queries'] = 0
            self.counters['failed_queries'] += 1
    
    def log_operation(self, operation: str, duration: float, success: bool = True, **kwargs):
        """Log general operation performance"""
        self.logger.info(
            f"Operation {operation} completed",
            extra={
                'operation': operation,
                'duration': duration,
                'success': success,
                **kwargs
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = {
            'counters': self.counters.copy(),
            'averages': {},
            'totals': {}
        }
        
        for metric_name, values in self.metrics.items():
            if values:
                metrics['averages'][metric_name] = sum(values) / len(values)
                metrics['totals'][metric_name] = sum(values)
        
        return metrics
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.counters.clear()


class SecurityLogger:
    """Security event logging"""
    
    def __init__(self):
        self.logger = logging.getLogger('oxen.security')
    
    def log_login_attempt(self, username: str, success: bool, ip_address: str = None):
        """Log login attempt"""
        self.logger.warning(
            f"Login attempt for user {username}",
            extra={
                'event': 'login_attempt',
                'username': username,
                'success': success,
                'ip_address': ip_address
            }
        )
    
    def log_sql_injection_attempt(self, sql: str, ip_address: str = None):
        """Log SQL injection attempt"""
        self.logger.critical(
            "SQL injection attempt detected",
            extra={
                'event': 'sql_injection',
                'sql': sql,
                'ip_address': ip_address
            }
        )
    
    def log_file_upload(self, filename: str, file_size: int, user_id: str = None):
        """Log file upload"""
        self.logger.info(
            f"File uploaded: {filename}",
            extra={
                'event': 'file_upload',
                'filename': filename,
                'file_size': file_size,
                'user_id': user_id
            }
        )
    
    def log_unauthorized_access(self, resource: str, user_id: str = None, ip_address: str = None):
        """Log unauthorized access attempt"""
        self.logger.warning(
            f"Unauthorized access attempt to {resource}",
            extra={
                'event': 'unauthorized_access',
                'resource': resource,
                'user_id': user_id,
                'ip_address': ip_address
            }
        )


class OxenLogger:
    """Main OxenORM logger"""
    
    def __init__(self, name: str = 'oxen'):
        self.logger = logging.getLogger(name)
        self.performance = PerformanceLogger()
        self.security = SecurityLogger()
        self.context = LogContext()
        
        # Configure logger
        self._configure_logger()
    
    def _configure_logger(self):
        """Configure the logger with handlers and formatters"""
        config = get_config()
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, config.logging.level))
        
        # Console handler
        if config.logging.enable_console:
            console_handler = logging.StreamHandler()
            if config.is_production():
                console_formatter = StructuredFormatter()
            else:
                console_formatter = logging.Formatter(config.logging.format)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if config.logging.enable_file and config.logging.file_path:
            file_handler = logging.handlers.RotatingFileHandler(
                config.logging.file_path,
                maxBytes=config.logging.max_file_size,
                backupCount=config.logging.backup_count
            )
            file_formatter = StructuredFormatter()
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def set_context(self, **kwargs):
        """Set logging context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra={**asdict(self.context), **kwargs})
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra={**asdict(self.context), **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra={**asdict(self.context), **kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra={**asdict(self.context), **kwargs})
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra={**asdict(self.context), **kwargs})
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra={**asdict(self.context), **kwargs})
    
    @contextmanager
    def operation_context(self, operation: str, **kwargs):
        """Context manager for operation logging"""
        start_time = time.time()
        self.set_context(operation=operation, **kwargs)
        
        try:
            self.info(f"Starting operation: {operation}")
            yield
            duration = time.time() - start_time
            self.set_context(duration=duration)
            self.info(f"Operation completed: {operation}", duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.set_context(duration=duration, error_count=self.context.error_count + 1)
            self.exception(f"Operation failed: {operation}", duration=duration)
            raise
    
    def log_database_operation(self, operation: str, table: str = None, duration: float = None, **kwargs):
        """Log database operation"""
        self.info(
            f"Database operation: {operation}",
            extra={
                'operation': operation,
                'table': table,
                'duration': duration,
                'database': self.context.database,
                **kwargs
            }
        )
    
    def log_query_execution(self, sql: str, duration: float, success: bool = True):
        """Log query execution"""
        self.performance.log_query(sql, duration, success)
        self.log_database_operation(
            'query_execution',
            duration=duration,
            sql=sql,
            success=success
        )


# Global logger instance
_logger: Optional[OxenLogger] = None


def get_logger(name: str = 'oxen') -> OxenLogger:
    """Get global logger instance"""
    global _logger
    if _logger is None:
        _logger = OxenLogger(name)
    return _logger


def setup_logging(config=None):
    """Setup logging with configuration"""
    if config is None:
        config = get_config()
    
    logger = get_logger()
    logger._configure_logger()
    
    logger.info("Logging system initialized", environment=config.environment.value)


def log_performance_metrics():
    """Log current performance metrics"""
    logger = get_logger()
    metrics = logger.performance.get_metrics()
    
    logger.info(
        "Performance metrics summary",
        extra={
            'metrics': metrics,
            'operation': 'performance_summary'
        }
    )


def log_startup():
    """Log application startup"""
    logger = get_logger()
    config = get_config()
    
    logger.info(
        "OxenORM application starting",
        extra={
            'environment': config.environment.value,
            'debug': config.debug,
            'database_type': config.database.type.value,
            'operation': 'startup'
        }
    )


def log_shutdown():
    """Log application shutdown"""
    logger = get_logger()
    
    # Log final performance metrics
    log_performance_metrics()
    
    logger.info(
        "OxenORM application shutting down",
        extra={'operation': 'shutdown'}
    )


# Convenience functions for common logging patterns
def log_database_connection(connection_string: str, success: bool, duration: float = None):
    """Log database connection attempt"""
    logger = get_logger()
    logger.info(
        f"Database connection {'established' if success else 'failed'}",
        extra={
            'connection_string': connection_string,
            'success': success,
            'duration': duration,
            'operation': 'database_connection'
        }
    )


def log_migration_execution(migration_name: str, success: bool, duration: float = None):
    """Log migration execution"""
    logger = get_logger()
    logger.info(
        f"Migration {'executed' if success else 'failed'}: {migration_name}",
        extra={
            'migration_name': migration_name,
            'success': success,
            'duration': duration,
            'operation': 'migration'
        }
    )


def log_file_operation(operation: str, file_path: str, success: bool, **kwargs):
    """Log file operation"""
    logger = get_logger()
    logger.info(
        f"File operation {'completed' if success else 'failed'}: {operation}",
        extra={
            'operation': operation,
            'file_path': file_path,
            'success': success,
            **kwargs
        }
    )


if __name__ == "__main__":
    # Test logging system
    setup_logging()
    
    logger = get_logger()
    
    logger.info("Testing logging system")
    
    with logger.operation_context("test_operation"):
        logger.info("Inside test operation")
        time.sleep(0.1)
    
    logger.performance.log_query("SELECT * FROM users", 0.05)
    logger.security.log_file_upload("test.txt", 1024)
    
    log_performance_metrics() 