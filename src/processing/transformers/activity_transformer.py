"""Activity data transformer for cleaning and normalizing activity records."""

from typing import List, Optional
from datetime import datetime

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import ActivityRecord
from src.models.enums import DataSource


class ActivityTransformer(RecordListTransformer[ActivityRecord]):
    """Transformer for cleaning and normalizing activity records.
    
    This transformer handles ActivityRecord objects from any source (Oura, etc.)
    and focuses on data type-specific cleaning rather than source-specific logic.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Activity metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Activity transformer."""
        super().__init__()
        
        # No validation thresholds needed for activity data - it's already reliable
        # Focus on data cleaning and normalization only
    
    def transform_record(self, record: ActivityRecord) -> Optional[ActivityRecord]:
        """Transform a single activity record.
        
        Args:
            record: Raw activity record from extractor
            
        Returns:
            Cleaned and normalized activity record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid activity record filtered out: {record.date}")
            return None
        
        # Create a cleaned copy of the record
        cleaned_record = ActivityRecord(
            date=record.date,
            source=record.source,
            steps=self._normalize_steps(record.steps),
            active_calories=self._normalize_calories(record.active_calories),
            total_calories=self._normalize_calories(record.total_calories)
        )
        
        self.logger.debug(f"Transformed activity record: {cleaned_record.date}")
        return cleaned_record
    
    def validate_record(self, record: ActivityRecord) -> bool:
        """Validate an activity record for basic requirements.
        
        Args:
            record: Activity record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Only check essential fields - no value validation needed for activity data
        if not record.date:
            return False
        
        # Check source
        if record.source != DataSource.OURA:
            return False
        
        # Activity data is reliable - no need for value range validation
        return True
    
    def filter_record(self, record: ActivityRecord) -> bool:
        """Determine if a record should be kept after transformation.
        
        Args:
            record: Transformed activity record
            
        Returns:
            True if record should be kept, False to filter out
        """
        # Keep all valid transformed records
        return record is not None
    
    def _normalize_steps(self, steps: Optional[int]) -> Optional[int]:
        """Normalize step count.
        
        Args:
            steps: Raw step count
            
        Returns:
            Normalized steps as integer
        """
        if steps is None:
            return None
        
        # Ensure it's an integer
        return int(round(steps))
    
    def _normalize_calories(self, calories: Optional[int]) -> Optional[int]:
        """Normalize calories.
        
        Args:
            calories: Raw calories value
            
        Returns:
            Normalized calories as integer
        """
        if calories is None:
            return None
        
        # Ensure it's an integer
        return int(round(calories))
