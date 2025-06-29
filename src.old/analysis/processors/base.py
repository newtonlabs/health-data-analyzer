"""Base processor class for all data source processors.

This module provides a base class with common functionality for all data processors,
including timezone handling, logging, and error handling.
"""

from datetime import datetime
from typing import Any, Optional, Union

from src.utils.date_utils import DateUtils
from src.utils.logging_utils import HealthLogger


class BaseProcessor:
    """Base class for all data processors."""
    
    def __init__(self):
        """Initialize the base processor with a logger."""
        self.logger = HealthLogger(self.__class__.__name__)
        
    def parse_timestamp(self, timestamp: Union[str, int, float], to_local: bool = True) -> Optional[datetime]:
        """Parse timestamp to datetime object.
        
        Args:
            timestamp: Timestamp string in ISO format or Unix timestamp
            to_local: Whether to convert to local time
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            result = DateUtils.parse_timestamp(timestamp, to_local)
            if result is None:
                self.logger.warning(f"Failed to parse timestamp: {timestamp}")
            return result
        except Exception as e:
            self.logger.warning(f"Error parsing timestamp {timestamp}: {e}")
            return None
            
    def log_timestamp_conversion(self, original: Any, converted: datetime, label: str = "Timestamp") -> None:
        """Log timestamp conversion for debugging.
        
        Args:
            original: Original timestamp value
            converted: Converted datetime object
            label: Label for the log message
        """
        if converted:
            self.logger.info(f"{label} (original): {original}")
            self.logger.info(f"{label} (converted): {converted.isoformat()}")
