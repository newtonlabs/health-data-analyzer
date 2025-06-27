"""Workout data transformer for cleaning and normalizing workout records."""

from typing import List, Optional
from datetime import datetime

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import WorkoutRecord
from src.models.enums import DataSource


class WorkoutTransformer(RecordListTransformer[WorkoutRecord]):
    """Transformer for cleaning and normalizing workout records.
    
    This transformer handles WorkoutRecord objects from any source (Whoop, Hevy, etc.)
    and focuses on data type-specific cleaning rather than source-specific logic.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Workout metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Workout transformer."""
        super().__init__()
        
        # Validation thresholds
        self.min_duration_minutes = 0  # Allow 0 duration workouts (Whoop sometimes reports these)
        self.max_duration_minutes = 480  # Maximum workout duration (8 hours)
        self.min_calories = 0  # Allow 0 calories (some workouts may not burn calories)
        self.max_calories = 2000  # Maximum calories burned
        self.min_strain = 0.0  # Minimum strain score
        self.max_strain = 21.0  # Maximum strain score
    
    def transform_record(self, record: WorkoutRecord) -> Optional[WorkoutRecord]:
        """Transform a single workout record.
        
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
            date=record.timestamp.date(),  # Calculate date from timestamp
            source=record.source,
            sport=record.sport,
            duration_minutes=self._normalize_duration(record.duration_minutes),
            calories=self._normalize_calories(record.calories),
            strain_score=self._normalize_strain(record.strain_score),
            average_heart_rate=self._normalize_heart_rate(record.average_heart_rate),
            max_heart_rate=self._normalize_heart_rate(record.max_heart_rate),
            zone_0_minutes=self._normalize_zone_duration(record.zone_0_minutes),
            zone_1_minutes=self._normalize_zone_duration(record.zone_1_minutes),
            zone_2_minutes=self._normalize_zone_duration(record.zone_2_minutes),
            zone_3_minutes=self._normalize_zone_duration(record.zone_3_minutes),
            zone_4_minutes=self._normalize_zone_duration(record.zone_4_minutes),
            zone_5_minutes=self._normalize_zone_duration(record.zone_5_minutes),
            set_count=record.set_count,
            volume_kg=record.volume_kg
        )
        
        self.logger.debug(f"Transformed workout record: {cleaned_record.timestamp}")
        return cleaned_record
    
    def validate_record(self, record: WorkoutRecord) -> bool:
        """Validate a workout record for data quality.
        
        Args:
            record: Workout record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Check required fields
        if not record.timestamp:
            return False
        
        # Validate duration
        if (record.duration_minutes is not None and 
            (record.duration_minutes < self.min_duration_minutes or 
             record.duration_minutes > self.max_duration_minutes)):
            return False
        
        # Validate calories
        if (record.calories is not None and 
            (record.calories < self.min_calories or 
             record.calories > self.max_calories)):
            return False
        
        # Validate strain score
        if (record.strain_score is not None and 
            (record.strain_score < self.min_strain or 
             record.strain_score > self.max_strain)):
            return False
        
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
    
    def _normalize_duration(self, duration: Optional[float]) -> Optional[float]:
        """Normalize workout duration.
        
        Args:
            duration: Raw duration in minutes
            
        Returns:
            Normalized duration, rounded to 1 decimal place
        """
        if duration is None:
            return None
        
        # Round to 1 decimal place
        return round(duration, 1)
    
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
    
    def _normalize_strain(self, strain: Optional[float]) -> Optional[float]:
        """Normalize strain score.
        
        Args:
            strain: Raw strain score
            
        Returns:
            Normalized strain score, rounded to 2 decimal places
        """
        if strain is None:
            return None
        
        # Round to 2 decimal places and clamp to valid range
        normalized = round(strain, 2)
        return max(self.min_strain, min(self.max_strain, normalized))
    
    def _normalize_heart_rate(self, heart_rate: Optional[int]) -> Optional[int]:
        """Normalize heart rate.
        
        Args:
            heart_rate: Raw heart rate value
            
        Returns:
            Normalized heart rate as integer
        """
        if heart_rate is None:
            return None
        
        # Ensure it's an integer
        return int(round(heart_rate))
    
    def _normalize_zone_duration(self, duration: Optional[float]) -> Optional[float]:
        """Normalize heart rate zone duration.
        
        Args:
            duration: Raw duration in minutes
            
        Returns:
            Normalized duration, rounded to 1 decimal place
        """
        if duration is None:
            return None
        
        # Round to 1 decimal place
        return round(duration, 1)
