"""
Advanced logging system for SuperSID Pro
Provides comprehensive logging with rotation, colors, and multiple outputs
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback
from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = logging. DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        log_color = self.COLORS. get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self. COLORS['RESET']}"
        record.name = f"\033[94m{record.name}\033[0m"
        return super().format(record)

class SuperSIDLogger:
    """Advanced logger for SuperSID Pro"""
    
    def __init__(self, name: str = "SuperSID_Pro"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        self.performance_logger = logging.getLogger(f"{name}. Performance")
        self.data_logger = logging.getLogger(f"{name}.Data")
        self.error_logger = logging.getLogger(f"{name}.Error")
        
        if not self. logger.handlers:
            self. setup_handlers()
    
    def setup_handlers(self):
        """Setup all logging handlers"""
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        if sys.stdout.isatty():
            console_handler = logging. StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        main_handler = logging.handlers.RotatingFileHandler(
            log_dir / "supersid_pro.log",
            maxBytes=10*1024*1024, 
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        main_handler.setFormatter(main_formatter)
        self.logger.addHandler(main_handler)
        
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "supersid_pro_errors.log",
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(main_formatter)
        self.logger.addHandler(error_handler)
        
        perf_handler = logging.handlers.RotatingFileHandler(
            log_dir / "performance.log",
            maxBytes=5*1024*1024,
            backupCount=2,
            encoding='utf-8'
        )
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        )
        perf_handler.setFormatter(perf_formatter)
        self.performance_logger.addHandler(perf_handler)
        self.performance_logger.setLevel(logging.INFO)
        
        data_handler = logging.handlers.RotatingFileHandler(
            log_dir / "data_processing.log",
            maxBytes=10*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        data_formatter = logging.Formatter(
            '%(asctime)s - DATA - %(levelname)s - %(message)s'
        )
        data_handler.setFormatter(data_formatter)
        self.data_logger.addHandler(data_handler)
        self.data_logger. setLevel(logging.INFO)
    
    def log_exception(self, exception: Exception, context: str = ""):
        """Log exception with full traceback"""
        error_msg = f"Exception in {context}: {str(exception)}"
        traceback_str = traceback.format_exc()
        
        self.error_logger.error(f"{error_msg}\nTraceback:\n{traceback_str}")
        
        self.logger.error(f"Exception: {exception} (Context: {context})")
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log performance metrics"""
        msg = f"{operation}: {duration:.3f}s"
        if details:
            msg += f" - {details}"
        self.performance_logger.info(msg)
    
    def log_data_event(self, event_type: str, data: dict):
        """Log data processing events"""
        self.data_logger.info(f"{event_type}: {data}")

_logger_instance: Optional[SuperSIDLogger] = None

def setup_logger(debug: bool = False) -> None:
    """Setup global logger instance"""
    global _logger_instance
    _logger_instance = SuperSIDLogger()
    
    if debug:
        _logger_instance.logger.setLevel(logging. DEBUG)
        for handler in _logger_instance.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)

def get_logger(name: str = "SuperSID_Pro") -> logging.Logger:
    """Get logger instance"""
    if _logger_instance is None:
        setup_logger()
    
    return logging.getLogger(name)

def log_exception(exception: Exception, context: str = ""):
    """Convenience function to log exceptions"""
    if _logger_instance:
        _logger_instance.log_exception(exception, context)

def log_performance(operation: str, duration: float, details: dict = None):
    """Convenience function to log performance"""
    if _logger_instance:
        _logger_instance.log_performance(operation, duration, details)

def log_data_event(event_type: str, data: dict):
    """Convenience function to log data events"""
    if _logger_instance:
        _logger_instance.log_data_event(event_type, data)

def log_execution_time(operation_name: str = None):
    """Decorator to automatically log function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                log_performance(op_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                log_performance(f"{op_name} (FAILED)", duration)
                log_exception(e, f"Function: {op_name}")
                raise
        return wrapper
    return decorator