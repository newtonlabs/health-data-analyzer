"""Recovery record model for structured recovery data."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..enums import DataSource


@dataclass
class RecoveryRecord:
    """Structured recovery data record."""
    timestamp: Optional[str] = None  # Raw timestamp from API for timezone handling
    date: Optional[date] = None
    source: Optional[DataSource] = None
    
    # Recovery metrics
    recovery_score: Optional[int] = None
    
    # Heart rate variability
    hrv_rmssd: Optional[float] = None
    
    # Heart rate metrics
    resting_hr: Optional[int] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
