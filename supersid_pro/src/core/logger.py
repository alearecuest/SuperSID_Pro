"""
Logging system for SuperSID Pro
Provides comprehensive logging capabilities
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS. get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self. COLORS['RESET']}"
        return super().format(record)

class SuperSIDLogger:
    """SuperSID Pro logging manager"""
    
    def __init__(self, name: str = "SuperSID_Pro"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self.setup_handlers()
    
    def setup_handlers(self):
        """Setup logging handlers"""
        # Create logs directory
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Console handler with colors
        console_handler = logging. StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "supersid_pro.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "supersid_pro_errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self. logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def get_logger(self):
        """Get the logger instance"""
        return self.logger

# Global logger instance
_logger_instance: Optional[SuperSIDLogger] = None

def setup_logger(debug: bool = False) -> None:
    """Setup global logger"""
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