"""Resilience data transformer for cleaning and normalizing resilience records."""

from typing import List, Optional
from datetime import datetime

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.raw_data import ResilienceRecord
from src.models.enums import DataSource


class ResilienceTransformer(RecordListTransformer[ResilienceRecord]):
    """Transformer for resilience data records."""
    
    def __init__(self):
        """Initialize the resilience transformer."""
        super().__init__()
    
    def transform_record(self, record: ResilienceRecord) -> Optional[ResilienceRecord]:
        """Transform a single resilience record.
        
        Args:
            record: Raw resilience record from extractor
            
        Returns:
            Cleaned and normalized resilience record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid resilience record filtered out: {record.timestamp}")
            return None
        
        # Date is now calculated in extractor, just use the provided date
        final_date = record.date
        
        # Create a cleaned copy of the record (pass-through for now)
        cleaned_record = ResilienceRecord(
            timestamp=record.timestamp,  # Preserve timestamp
            date=final_date,
            source=record.source,
            sleep_recovery=record.sleep_recovery,
            daytime_recovery=record.daytime_recovery,
            stress=record.stress,
            level=record.level
        )
        
        self.logger.debug(f"Transformed resilience record: {cleaned_record.date}")
        return cleaned_record
    
    def validate_record(self, record: ResilienceRecord) -> bool:
        """Validate a resilience record.
        
        Args:
            record: Resilience record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        if not record:
            return False
        
        # Must have timestamp or date
        if not record.timestamp and not record.date:
            self.logger.warning("Resilience record missing both timestamp and date")
            return False
        
        # Must have at least one resilience metric
        has_resilience_data = any([
            record.sleep_recovery is not None,
            record.daytime_recovery is not None,
            record.stress is not None,
            record.level is not None
        ])
        
        if not has_resilience_data:
            self.logger.warning("Resilience record has no resilience metrics")
            return False
        
        return True
    
    def should_include_record(self, record: ResilienceRecord) -> bool:
        """Determine if a record should be included in the final output.
        
        Args:
            record: Transformed resilience record
            
        Returns:
            True if record should be included
        """
        # Keep all valid transformed records
        return record is not None
