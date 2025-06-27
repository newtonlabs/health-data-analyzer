"""Recovery data transformer for cleaning and normalizing recovery records."""

from typing import List, Optional
from datetime import date

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import RecoveryRecord
from src.models.enums import DataSource


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
            self.logger.warning(f"Invalid recovery record filtered out: {record.timestamp}")
            return None
        
        # Calculate date from timestamp if needed
        final_date = record.date
        if record.timestamp and record.date is None:
            try:
                from src.utils.date_utils import DateUtils
                # Parse timestamp with timezone conversion
                recovery_datetime = DateUtils.parse_timestamp(record.timestamp, to_local=True)
                if recovery_datetime:
                    final_date = recovery_datetime.date()
                    self.logger.debug(f"Converted timestamp {record.timestamp} to date {final_date}")
                else:
                    self.logger.warning(f"Failed to parse timestamp: {record.timestamp}")
            except Exception as e:
                self.logger.warning(f"Error parsing timestamp {record.timestamp}: {e}")
        
        # Create a cleaned copy of the record
        cleaned_record = RecoveryRecord(
            timestamp=record.timestamp,  # Preserve timestamp
            date=final_date,
            source=record.source,
            recovery_score=self._normalize_recovery_score(record.recovery_score),
            hrv_rmssd=self._normalize_hrv(record.hrv_rmssd),
            resting_hr=self._normalize_heart_rate(record.resting_hr)
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
        if not record.date and not record.timestamp:
            return False
        
        # Check source
        if record.source != DataSource.WHOOP:
            return False
        
        # Must have at least one recovery metric
        has_recovery_data = any([
            record.recovery_score is not None,
            record.hrv_rmssd is not None,
            record.resting_hr is not None
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
    
    def _normalize_recovery_score(self, score: Optional[float]) -> Optional[float]:
        """Normalize recovery score value.
        
        Args:
            score: Raw recovery score
            
        Returns:
            Normalized recovery score
        """
        if score is None:
            return None
        
        # Implement normalization logic here
        return score
