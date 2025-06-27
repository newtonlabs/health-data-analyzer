"""Base class for data extractors.

This module provides the base class for all data extractor implementations,
defining the common interface and shared functionality for converting
raw API responses into structured data records.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

# Note: Specific model imports removed since BaseExtractor now uses generic Dict[str, List]
# Individual extractors import the specific models they need
from src.models.enums import DataSource
from src.utils.logging_utils import HealthLogger
from src.utils.date_utils import DateUtils


class BaseExtractor(ABC):
    """Base class for all data extractors.
    
    Extractors are responsible for converting raw API responses into
    structured data records. They should handle data validation,
    type conversion, and basic error handling.
    """
    
    def __init__(self, data_source: DataSource):
        """Initialize the extractor.
        
        Args:
            data_source: The data source this extractor handles
        """
        self.data_source = data_source
        self.logger = HealthLogger(self.__class__.__name__)
        # Note: DataExporter removed - pipeline now uses PipelinePersistence
    
    @abstractmethod
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract structured data from raw API response.
        
        This is the main entry point for data extraction. Implementations
        should process the raw API data and return a dictionary containing
        lists of structured records organized by data type.
        
        Args:
            raw_data: Raw API response data
            
        Returns:
            Dictionary with data type keys (e.g., 'workouts', 'recovery') 
            and values as lists of structured record objects
            
        Example:
            {
                'workouts': [WorkoutRecord(...), ...],
                'recovery': [RecoveryRecord(...), ...],
                'sleep': [SleepRecord(...), ...]
            }
        """
        pass
    
    # Utility methods for common extraction tasks
    
    def parse_timestamp(
        self, 
        timestamp: Union[str, int, float, None], 
        to_local: bool = True
    ) -> Optional[datetime]:
        """Parse timestamp to datetime object.
        
        Args:
            timestamp: Timestamp string in ISO format or Unix timestamp
            to_local: Whether to convert to local time
            
        Returns:
            Datetime object or None if parsing fails
        """
        if timestamp is None:
            return None
            
        try:
            result = DateUtils.parse_timestamp(timestamp, to_local)
            if result is None:
                self.logger.warning(f"Failed to parse timestamp: {timestamp}")
            return result
        except Exception as e:
            self.logger.warning(f"Error parsing timestamp {timestamp}: {e}")
            return None
    
    def parse_date(self, date_value: Union[str, date, None]) -> Optional[date]:
        """Parse date value to date object.
        
        Args:
            date_value: Date string or date object
            
        Returns:
            Date object or None if parsing fails
        """
        if date_value is None:
            return None
        
        if isinstance(date_value, date):
            return date_value
        
        if isinstance(date_value, str):
            try:
                # Try parsing as ISO date
                return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
            except ValueError:
                try:
                    # Try parsing as date only
                    return datetime.strptime(date_value, '%Y-%m-%d').date()
                except ValueError:
                    self.logger.warning(f"Failed to parse date: {date_value}")
                    return None
        
        return None
    
    def safe_get(
        self, 
        data: Dict[str, Any], 
        key: str, 
        default: Any = None,
        expected_type: type = None
    ) -> Any:
        """Safely get value from dictionary with type checking.
        
        Args:
            data: Dictionary to get value from
            key: Key to look up
            default: Default value if key not found or type mismatch
            expected_type: Expected type for the value
            
        Returns:
            Value from dictionary or default
        """
        if not isinstance(data, dict) or key not in data:
            return default
        
        value = data[key]
        
        if expected_type and not isinstance(value, expected_type):
            self.logger.warning(
                f"Expected {expected_type.__name__} for key '{key}', "
                f"got {type(value).__name__}: {value}"
            )
            return default
        
        return value
    
    def safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to integer.
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Integer value or default
        """
        if value is None:
            return default
        
        try:
            return int(float(value))  # Handle string numbers
        except (ValueError, TypeError):
            self.logger.warning(f"Failed to convert to int: {value}")
            return default
    
    def safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float.
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Float value or default
        """
        if value is None:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            self.logger.warning(f"Failed to convert to float: {value}")
            return default
    
    def log_extraction_stats(
        self, 
        record_type: str, 
        extracted_count: int,
        raw_count: Optional[int] = None
    ) -> None:
        """Log extraction statistics for monitoring.
        
        Args:
            record_type: Type of records extracted (e.g., 'workouts')
            extracted_count: Number of records successfully extracted
            raw_count: Number of raw records processed (if different)
        """
        log_msg = f"Extracted {extracted_count} {record_type} records"
        if raw_count is not None and raw_count != extracted_count:
            log_msg += f" from {raw_count} raw records"
        
        self.logger.info(log_msg)

    # Note: CSV export methods removed - pipeline now uses PipelinePersistence for all data persistence
