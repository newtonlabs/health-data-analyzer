"""Sleep record model for structured sleep data."""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from ..enums import DataSource


@dataclass
class SleepRecord:
    """Structured sleep data record."""
    timestamp: Optional[str] = None  # Raw timestamp from API for timezone handling
    date: Optional[date] = None
    source: Optional[DataSource] = None
    
    # Sleep duration
    total_sleep_minutes: Optional[int] = None
    time_in_bed_minutes: Optional[int] = None
    
    # Sleep stages (in minutes)
    light_sleep_minutes: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    
    # Sleep quality metrics
    sleep_score: Optional[int] = None
    sleep_need_minutes: Optional[int] = None
    
    # Sleep timing
    bedtime: Optional[datetime] = None
    wake_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
