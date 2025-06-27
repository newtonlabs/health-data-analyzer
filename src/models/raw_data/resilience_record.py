"""Resilience record model for structured resilience data."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..enums import DataSource


@dataclass
class ResilienceRecord:
    """Structured resilience data record."""
    timestamp: Optional[str] = None  # Raw timestamp from API for timezone handling
    date: Optional[date] = None
    source: Optional[DataSource] = None
    
    # Resilience metrics
    sleep_recovery: Optional[float] = None
    daytime_recovery: Optional[float] = None
    stress: Optional[float] = None
    level: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
