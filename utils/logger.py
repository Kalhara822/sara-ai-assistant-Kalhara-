"""
Logging Infrastructure for SARA AI Assistant
Provides thread-safe logging to console and rotating log files.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import config

def setup_logger(name: str = "SARA") -> logging.Logger:
    """Initialize and configure main application logger."""
    config.ensure_directories()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    # Log Format
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(threadName)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler (Rotating log: max 5MB, keep 3 backups)
    log_file = config.LOGS_DIR / "sara.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    return logger

# Global Logger instance
logger = setup_logger()
