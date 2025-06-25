"""Hevy data transformer for cleaning and normalizing workout records."""

from typing import List, Optional
from datetime import datetime

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import WorkoutRecord
from src.models.enums import DataSource


class HevyTransformer(RecordListTransformer[WorkoutRecord]):
    """Transformer for cleaning and normalizing Hevy workout records.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Workout metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Hevy transformer."""
        super().__init__()
        
        # No strict validation thresholds needed for Hevy data - it's reliable
        # Focus on data cleaning and normalization only
    
    def transform_record(self, record: WorkoutRecord) -> Optional[WorkoutRecord]:
        """Transform a single Hevy workout record.
        
        Args:
            record: Raw workout record from extractor
            
        Returns:
            Cleaned and normalized workout record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid workout record filtered out: {record.timestamp}")
            return None
        
        # Create a cleaned copy of the record
        cleaned_record = WorkoutRecord(
            timestamp=record.timestamp,
            source=record.source,
            sport=record.sport,
            duration_minutes=self._normalize_duration(record.duration_minutes),
            calories=self._normalize_calories(record.calories),
            exercise_count=self._normalize_count(record.exercise_count),
            set_count=self._normalize_count(record.set_count),
            volume_kg=self._normalize_volume(record.volume_kg)
        )
        
        self.logger.debug(f"Transformed workout record: {cleaned_record.timestamp}")
        return cleaned_record
    
    def validate_record(self, record: WorkoutRecord) -> bool:
        """Validate a workout record for basic requirements.
        
        Args:
            record: Workout record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Only check essential fields - no value validation needed for Hevy
        if not record.timestamp:
            return False
        
        # Check source
        if record.source != DataSource.HEVY:
            return False
        
        # Must have some workout data
        if (record.exercise_count is None or record.exercise_count <= 0) and \
           (record.set_count is None or record.set_count <= 0):
            return False
        
        # Hevy data is reliable - no need for extensive validation
        return True
    
    def filter_record(self, record: WorkoutRecord) -> bool:
        """Determine if a record should be kept after transformation.
        
        Args:
            record: Transformed workout record
            
        Returns:
            True if record should be kept, False to filter out
        """
        # Keep all valid transformed records
        return record is not None
    
    def _normalize_duration(self, duration: Optional[int]) -> Optional[int]:
        """Normalize workout duration.
        
        Args:
            duration: Raw duration in minutes
            
        Returns:
            Normalized duration as integer
        """
        if duration is None:
            return None
        
        # Ensure it's an integer
        return int(round(duration))
    
    def _normalize_calories(self, calories: Optional[int]) -> Optional[int]:
        """Normalize calories burned.
        
        Args:
            calories: Raw calories value
            
        Returns:
            Normalized calories as integer
        """
        if calories is None:
            return None
        
        # Ensure it's an integer
        return int(round(calories))
    
    def _normalize_count(self, count: Optional[int]) -> Optional[int]:
        """Normalize count values (exercises, sets).
        
        Args:
            count: Raw count value
            
        Returns:
            Normalized count as integer
        """
        if count is None:
            return None
        
        # Ensure it's an integer
        return int(count)
    
    def _normalize_volume(self, volume: Optional[float]) -> Optional[float]:
        """Normalize volume in kg.
        
        Args:
            volume: Raw volume in kg
            
        Returns:
            Normalized volume, rounded to 2 decimal places
        """
        if volume is None:
            return None
        
        # Round to 2 decimal places
        return round(volume, 2)
