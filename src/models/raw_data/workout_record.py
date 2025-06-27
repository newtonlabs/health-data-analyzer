"""Workout record model for structured workout/exercise data."""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from ..enums import DataSource, SportType


@dataclass
class WorkoutRecord:
    """Structured workout/exercise record."""
    timestamp: datetime
    date: date  # Date extracted from timestamp for easier filtering
    source: DataSource
    sport: SportType
    duration_minutes: int
    
    # Optional metrics (vary by source)
    strain_score: Optional[float] = None
    calories: Optional[int] = None
    average_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    
    # Heart rate zone durations (minutes in each zone)
    zone_0_minutes: Optional[float] = None  # Below Zone 1
    zone_1_minutes: Optional[float] = None  # 50-60% max HR
    zone_2_minutes: Optional[float] = None  # 60-70% max HR
    zone_3_minutes: Optional[float] = None  # 70-80% max HR
    zone_4_minutes: Optional[float] = None  # 80-90% max HR
    zone_5_minutes: Optional[float] = None  # 90-100% max HR
    
    # Hevy-specific fields
    set_count: Optional[int] = None
    volume_kg: Optional[float] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
        if isinstance(self.sport, str):
            try:
                self.sport = SportType(self.sport)
            except ValueError:
                self.sport = SportType.UNKNOWN
