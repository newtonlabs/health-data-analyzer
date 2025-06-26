"""Weight data transformer for cleaning and normalizing weight records."""

from typing import List, Optional
from datetime import datetime

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import WeightRecord
from src.models.enums import DataSource


class WeightTransformer(RecordListTransformer[WeightRecord]):
    """Transformer for cleaning and normalizing weight records.
    
    This transformer handles WeightRecord objects from any source (Withings, etc.)
    and focuses on data type-specific cleaning rather than source-specific logic.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Weight and body composition metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Weight transformer."""
        super().__init__()
        
        # No strict validation thresholds needed for Weight data - it's reliable
        # Focus on data cleaning and normalization only
    
    def transform_record(self, record: WeightRecord) -> Optional[WeightRecord]:
        """Transform a single Weight record.
        
        Args:
            record: Raw weight record from extractor
            
        Returns:
            Cleaned and normalized weight record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid weight record filtered out: {record.timestamp}")
            return None
        
        # Create a cleaned copy of the record
        cleaned_record = WeightRecord(
            timestamp=record.timestamp,
            source=record.source,
            weight_kg=self._normalize_weight(record.weight_kg),
            body_fat_percentage=self._normalize_percentage(record.body_fat_percentage),
            muscle_mass_kg=self._normalize_mass(record.muscle_mass_kg),
            bone_mass_kg=self._normalize_mass(record.bone_mass_kg),
            water_percentage=self._normalize_percentage(record.water_percentage)
        )
        
        self.logger.debug(f"Transformed weight record: {cleaned_record.timestamp}")
        return cleaned_record
    
    def validate_record(self, record: WeightRecord) -> bool:
        """Validate a weight record for basic requirements.
        
        Args:
            record: Weight record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Only check essential fields - no value validation needed for Weight
        if not record.timestamp:
            return False
        
        # Check source
        if record.source != DataSource.WITHINGS:
            return False
        
        # Must have weight data
        if record.weight_kg is None or record.weight_kg <= 0:
            return False
        
        # Weight data is reliable - no need for extensive validation
        return True
    
    def filter_record(self, record: WeightRecord) -> bool:
        """Determine if a record should be kept after transformation.
        
        Args:
            record: Transformed weight record
            
        Returns:
            True if record should be kept, False to filter out
        """
        # Keep all valid transformed records
        return record is not None
    
    def _normalize_weight(self, weight: Optional[float]) -> Optional[float]:
        """Normalize weight value.
        
        Args:
            weight: Raw weight in kg
            
        Returns:
            Normalized weight, rounded to 3 decimal places
        """
        if weight is None:
            return None
        
        # Round to 3 decimal places for precision
        return round(weight, 3)
    
    def _normalize_mass(self, mass: Optional[float]) -> Optional[float]:
        """Normalize mass values (muscle, bone).
        
        Args:
            mass: Raw mass in kg
            
        Returns:
            Normalized mass, rounded to 2 decimal places
        """
        if mass is None:
            return None
        
        # Round to 2 decimal places
        return round(mass, 2)
    
    def _normalize_percentage(self, percentage: Optional[float]) -> Optional[float]:
        """Normalize percentage values (body fat, water).
        
        Args:
            percentage: Raw percentage value
            
        Returns:
            Normalized percentage, rounded to 2 decimal places
        """
        if percentage is None:
            return None
        
        # Round to 2 decimal places and ensure reasonable range
        normalized = round(percentage, 2)
        
        # Basic sanity check (but don't reject - just log)
        if normalized < 0 or normalized > 100:
            self.logger.warning(f"Unusual percentage value: {normalized}%")
        
        return normalized
