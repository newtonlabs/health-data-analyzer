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
            date=record.timestamp.date(),  # Calculate date from timestamp
            source=record.source,
            workout_id=record.workout_id,
            exercise_name=self._normalize_exercise_name(record.exercise_name),
            set_number=record.set_number,
            set_type=record.set_type,
            weight_kg=self._normalize_weight(record.weight_kg),
            reps=self._normalize_reps(record.reps)
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
        
        # Must have reps, and optionally weight (for bodyweight vs weighted exercises)
        if record.reps is None:
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
