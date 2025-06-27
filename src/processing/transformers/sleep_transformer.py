"""Sleep data transformer for cleaning and normalizing sleep records."""

from typing import List, Optional
from datetime import date, datetime

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.raw_data import SleepRecord
from src.models.enums import DataSource


class SleepTransformer(RecordListTransformer[SleepRecord]):
    """Transformer for cleaning and normalizing sleep records.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Sleep metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Sleep transformer."""
        super().__init__()
        
        # No strict validation thresholds needed for Whoop data - it's reliable
        # Focus on data cleaning and normalization only
    
    def transform_record(self, record: SleepRecord) -> Optional[SleepRecord]:
        """Transform a single sleep record.
        
        Args:
            record: Raw sleep record from extractor
            
        Returns:
            Cleaned and normalized sleep record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid sleep record filtered out: {record.timestamp}")
            return None
        
        # Calculate date from timestamp if needed
        final_date = record.date
        if record.timestamp and record.date is None:
            try:
                from src.utils.date_utils import DateUtils
                # Parse timestamp with timezone conversion
                sleep_datetime = DateUtils.parse_timestamp(record.timestamp, to_local=True)
                if sleep_datetime:
                    final_date = sleep_datetime.date()
                    self.logger.debug(f"Converted timestamp {record.timestamp} to date {final_date}")
                else:
                    self.logger.warning(f"Failed to parse timestamp: {record.timestamp}")
            except Exception as e:
                self.logger.warning(f"Error parsing timestamp {record.timestamp}: {e}")
        
        # Create a cleaned copy of the record
        cleaned_record = SleepRecord(
            timestamp=record.timestamp,  # Preserve timestamp
            date=final_date,
            source=record.source,
            total_sleep_minutes=self._normalize_minutes(record.total_sleep_minutes),
            time_in_bed_minutes=self._normalize_minutes(record.time_in_bed_minutes),
            light_sleep_minutes=self._normalize_minutes(record.light_sleep_minutes),
            deep_sleep_minutes=self._normalize_minutes(record.deep_sleep_minutes),
            rem_sleep_minutes=self._normalize_minutes(record.rem_sleep_minutes),
            awake_minutes=self._normalize_minutes(record.awake_minutes),
            sleep_score=self._normalize_score(record.sleep_score),
            sleep_need_minutes=self._normalize_minutes(record.sleep_need_minutes),
            bedtime=record.bedtime,  # Keep original datetime
            wake_time=record.wake_time  # Keep original datetime
        )
        
        self.logger.debug(f"Transformed sleep record: {cleaned_record.date}")
        return cleaned_record
    
    def validate_record(self, record: SleepRecord) -> bool:
        """Validate a sleep record for basic requirements.
        
        Args:
            record: Sleep record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Only check essential fields
        if not record.date and not record.timestamp:
            return False
        
        # Check source
        if record.source != DataSource.WHOOP:
            return False
        
        # Must have at least one sleep metric
        has_sleep_data = any([
            record.total_sleep_minutes is not None,
            record.time_in_bed_minutes is not None,
            record.sleep_score is not None,
            record.bedtime is not None
        ])
        
        if not has_sleep_data:
            return False
        
        return True
    
    def filter_record(self, record: SleepRecord) -> bool:
        """Determine if a record should be kept after transformation.
        
        Args:
            record: Transformed sleep record
            
        Returns:
            True if record should be kept, False to filter out
        """
        # Keep all valid transformed records
        return record is not None
    
    def _normalize_minutes(self, minutes: Optional[int]) -> Optional[int]:
        """Normalize time duration in minutes.
        
        Args:
            minutes: Raw minutes value
            
        Returns:
            Normalized minutes as integer
        """
        if minutes is None:
            return None
        
        # Ensure it's an integer and non-negative
        normalized_minutes = int(minutes)
        if normalized_minutes < 0:
            self.logger.warning(f"Negative minutes value: {normalized_minutes}")
            return 0
        
        # Warn about unreasonable values (more than 24 hours)
        if normalized_minutes > 1440:
            self.logger.warning(f"Unusually high minutes value: {normalized_minutes}")
        
        return normalized_minutes
    
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
        if normalized < 0 or normalized > 100:
            self.logger.warning(f"Percentage {normalized} outside valid range (0-100)")
        
        return max(0.0, min(100.0, normalized))
    
    def _normalize_score(self, score: Optional[int]) -> Optional[int]:
        """Normalize sleep score (typically 0-100).
        
        Args:
            score: Raw sleep score
            
        Returns:
            Normalized sleep score as integer
        """
        if score is None:
            return None
        
        # Ensure it's an integer
        normalized_score = int(score)
        
        # Warn about values outside typical range
        if normalized_score < 0 or normalized_score > 100:
            self.logger.warning(f"Sleep score {normalized_score} outside typical range (0-100)")
        
        return normalized_score
