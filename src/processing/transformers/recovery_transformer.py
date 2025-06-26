"""Recovery data transformer for cleaning and normalizing recovery records."""

from typing import List, Optional
from datetime import date

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import RecoveryRecord
from src.models.enums import DataSource, RecoveryLevel


class RecoveryTransformer(RecordListTransformer[RecoveryRecord]):
    """Transformer for cleaning and normalizing recovery records.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Recovery metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Recovery transformer."""
        super().__init__()
        
        # No strict validation thresholds needed for Whoop data - it's reliable
        # Focus on data cleaning and normalization only
    
    def transform_record(self, record: RecoveryRecord) -> Optional[RecoveryRecord]:
        """Transform a single recovery record.
        
        Args:
            record: Raw recovery record from extractor
            
        Returns:
            Cleaned and normalized recovery record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid recovery record filtered out: {record.date}")
            return None
        
        # Create a cleaned copy of the record
        cleaned_record = RecoveryRecord(
            date=record.date,
            source=record.source,
            recovery_score=self._normalize_recovery_score(record.recovery_score),
            recovery_level=record.recovery_level,  # Already enum, no normalization needed
            hrv_rmssd=self._normalize_hrv(record.hrv_rmssd),
            hrv_score=self._normalize_score(record.hrv_score),
            resting_hr=self._normalize_heart_rate(record.resting_hr),
            hr_variability=self._normalize_percentage(record.hr_variability),
            sleep_performance=self._normalize_percentage(record.sleep_performance),
            sleep_consistency=self._normalize_percentage(record.sleep_consistency)
        )
        
        self.logger.debug(f"Transformed recovery record: {cleaned_record.date}")
        return cleaned_record
    
    def validate_record(self, record: RecoveryRecord) -> bool:
        """Validate a recovery record for basic requirements.
        
        Args:
            record: Recovery record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Only check essential fields
        if not record.date:
            return False
        
        # Check source
        if record.source != DataSource.WHOOP:
            return False
        
        # Must have at least one recovery metric
        has_recovery_data = any([
            record.recovery_score is not None,
            record.hrv_rmssd is not None,
            record.resting_hr is not None,
            record.sleep_performance is not None
        ])
        
        if not has_recovery_data:
            return False
        
        return True
    
    def filter_record(self, record: RecoveryRecord) -> bool:
        """Determine if a record should be kept after transformation.
        
        Args:
            record: Transformed recovery record
            
        Returns:
            True if record should be kept, False to filter out
        """
        # Keep all valid transformed records
        return record is not None
    
    def _normalize_recovery_score(self, score: Optional[int]) -> Optional[int]:
        """Normalize recovery score (0-100).
        
        Args:
            score: Raw recovery score
            
        Returns:
            Normalized recovery score as integer
        """
        if score is None:
            return None
        
        # Ensure it's an integer and within valid range
        normalized_score = int(score)
        if normalized_score < 0 or normalized_score > 100:
            self.logger.warning(f"Recovery score {normalized_score} outside valid range (0-100)")
        
        return max(0, min(100, normalized_score))
    
    def _normalize_hrv(self, hrv: Optional[float]) -> Optional[float]:
        """Normalize HRV RMSSD value.
        
        Args:
            hrv: Raw HRV RMSSD in milliseconds
            
        Returns:
            Normalized HRV, rounded to 1 decimal place
        """
        if hrv is None:
            return None
        
        # Round to 1 decimal place
        return round(hrv, 1)
    
    def _normalize_score(self, score: Optional[int]) -> Optional[int]:
        """Normalize general score values.
        
        Args:
            score: Raw score value
            
        Returns:
            Normalized score as integer
        """
        if score is None:
            return None
        
        return int(score)
    
    def _normalize_heart_rate(self, hr: Optional[int]) -> Optional[int]:
        """Normalize heart rate value.
        
        Args:
            hr: Raw heart rate in BPM
            
        Returns:
            Normalized heart rate as integer
        """
        if hr is None:
            return None
        
        # Ensure reasonable heart rate range
        normalized_hr = int(hr)
        if normalized_hr < 30 or normalized_hr > 200:
            self.logger.warning(f"Heart rate {normalized_hr} outside typical range (30-200 BPM)")
        
        return normalized_hr
    
    def _normalize_percentage(self, percentage: Optional[float]) -> Optional[float]:
        """Normalize percentage values.
        
        Args:
            percentage: Raw percentage value
            
        Returns:
            Normalized percentage, rounded to 1 decimal place
        """
        if percentage is None:
            return None
        
        # Round to 1 decimal place and ensure 0-100 range
        normalized = round(percentage, 1)
        return max(0.0, min(100.0, normalized))
