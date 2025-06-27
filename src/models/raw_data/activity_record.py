"""Activity record model for structured general activity data."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..enums import DataSource


@dataclass
class ActivityRecord:
    """Structured general activity record (steps, calories, etc.)."""
    timestamp: Optional[str] = None  # Raw timestamp from API for timezone handling
    date: Optional[date] = None
    source: Optional[DataSource] = None
    
    # Core activity metrics
    steps: Optional[int] = None
    active_calories: Optional[int] = None
    total_calories: Optional[int] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
