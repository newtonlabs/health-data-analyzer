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