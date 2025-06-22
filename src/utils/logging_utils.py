"""Logging utilities for health data analyzer."""

import logging
import os
from datetime import datetime
from typing import Optional

def configure_logging() -> None:
    """Configure logging based on LOG_LEVEL environment variable.
    
    The LOG_LEVEL can be set to: DEBUG, INFO, WARNING, ERROR, CRITICAL
    If not set, defaults to WARNING.
    """
    # Get log level from environment variable or default to WARNING
    log_level_name = os.environ.get("LOG_LEVEL", "WARNING").upper()
    
    # Map string log level to logging constants
    log_level = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }.get(log_level_name, logging.WARNING)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)


# Configure logging when module is imported
configure_logging()

class HealthLogger:
    """Logger for health data operations."""

    def __init__(self, name: str):
        """Initialize logger.

        Args:
            name: Logger name, typically module name
        """
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Set up logger with standard configuration."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # Logger level is inherited from root logger
            # No need to set it explicitly here

    def log_skipped_date(self, date: datetime, reason: str):
        """Log skipped recovery date.

        Args:
            date: Date that was skipped
            reason: Why it was skipped
        """
        self.logger.warning(f"Skipped recovery date {date}: {reason}")

    def log_data_counts(self, data_type: str, count: int):
        """Log number of data items processed.

        Args:
            data_type: Type of data (e.g., 'recovery', 'workout')
            count: Number of items
        """
        self.logger.debug(f"Found {count} {data_type} records")

    def debug(self, msg: str):
        """Log debug message.

        Args:
            msg: Debug message
        """
        self.logger.debug(msg)

    def info(self, msg: str):
        """Log info message.

        Args:
            msg: Info message
        """
        self.logger.info(msg)

    def warning(self, msg: str):
        """Log warning message.

        Args:
            msg: Warning message
        """
        self.logger.warning(msg)

    def error(self, msg: str):
        """Log error message.

        Args:
            msg: Error message
        """
        self.logger.error(msg)

   