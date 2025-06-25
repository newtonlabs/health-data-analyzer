"""Exercise data transformer for cleaning and normalizing exercise records."""

from typing import List, Optional
from datetime import datetime

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import ExerciseRecord
from src.models.enums import DataSource


class ExerciseTransformer(RecordListTransformer[ExerciseRecord]):
    """Transformer for cleaning and normalizing exercise records.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Exercise metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Exercise transformer."""
        super().__init__()
        
        # No strict validation thresholds needed for Hevy data - it's reliable
        # Focus on data cleaning and normalization only
    
    def transform_record(self, record: ExerciseRecord) -> Optional[ExerciseRecord]:
        """Transform a single exercise record.
        
        Args:
            record: Raw exercise record from extractor
            
        Returns:
            Cleaned and normalized exercise record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid exercise record filtered out: {record.exercise_name}")
            return None
        
        # Create a cleaned copy of the record
        cleaned_record = ExerciseRecord(
            timestamp=record.timestamp,
            source=record.source,
            workout_id=record.workout_id,
            exercise_name=self._normalize_exercise_name(record.exercise_name),
            set_number=record.set_number,
            set_type=record.set_type,
            weight_kg=self._normalize_weight(record.weight_kg),
            reps=self._normalize_reps(record.reps),
            distance_meters=self._normalize_distance(record.distance_meters),
            duration_seconds=self._normalize_duration(record.duration_seconds),
            rpe=self._normalize_rpe(record.rpe)
        )
        
        self.logger.debug(f"Transformed exercise record: {cleaned_record.exercise_name}")
        return cleaned_record
    
    def validate_record(self, record: ExerciseRecord) -> bool:
        """Validate an exercise record for basic requirements.
        
        Args:
            record: Exercise record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Only check essential fields
        if not record.timestamp:
            return False
        
        # Check source
        if record.source != DataSource.HEVY:
            return False
        
        # Must have exercise name and workout ID
        if not record.exercise_name or not record.workout_id:
            return False
        
        # Must have either weight/reps or distance/duration
        has_strength_data = record.weight_kg is not None and record.reps is not None
        has_cardio_data = record.distance_meters is not None or record.duration_seconds is not None
        
        if not (has_strength_data or has_cardio_data):
            return False
        
        return True
    
    def filter_record(self, record: ExerciseRecord) -> bool:
        """Determine if a record should be kept after transformation.
        
        Args:
            record: Transformed exercise record
            
        Returns:
            True if record should be kept, False to filter out
        """
        # Keep all valid transformed records
        return record is not None
    
    def _normalize_exercise_name(self, name: Optional[str]) -> Optional[str]:
        """Normalize exercise name.
        
        Args:
            name: Raw exercise name
            
        Returns:
            Normalized exercise name
        """
        if not name:
            return None
        
        # Clean up the name
        return name.strip().title()
    
    def _normalize_weight(self, weight: Optional[float]) -> Optional[float]:
        """Normalize weight value.
        
        Args:
            weight: Raw weight in kg
            
        Returns:
            Normalized weight, rounded to 2 decimal places
        """
        if weight is None:
            return None
        
        # Round to 2 decimal places
        return round(weight, 2)
    
    def _normalize_reps(self, reps: Optional[int]) -> Optional[int]:
        """Normalize reps count.
        
        Args:
            reps: Raw reps count
            
        Returns:
            Normalized reps as integer
        """
        if reps is None:
            return None
        
        # Ensure it's an integer
        return int(reps)
    
    def _normalize_distance(self, distance: Optional[float]) -> Optional[float]:
        """Normalize distance in meters.
        
        Args:
            distance: Raw distance in meters
            
        Returns:
            Normalized distance, rounded to 2 decimal places
        """
        if distance is None:
            return None
        
        # Round to 2 decimal places
        return round(distance, 2)
    
    def _normalize_duration(self, duration: Optional[int]) -> Optional[int]:
        """Normalize duration in seconds.
        
        Args:
            duration: Raw duration in seconds
            
        Returns:
            Normalized duration as integer
        """
        if duration is None:
            return None
        
        # Ensure it's an integer
        return int(duration)
    
    def _normalize_rpe(self, rpe: Optional[int]) -> Optional[int]:
        """Normalize RPE (Rate of Perceived Exertion).
        
        Args:
            rpe: Raw RPE value (1-10 scale)
            
        Returns:
            Normalized RPE as integer
        """
        if rpe is None:
            return None
        
        # Ensure it's an integer and within valid range
        normalized_rpe = int(rpe)
        if normalized_rpe < 1 or normalized_rpe > 10:
            self.logger.warning(f"RPE value {normalized_rpe} outside valid range (1-10)")
        
        return normalized_rpe
