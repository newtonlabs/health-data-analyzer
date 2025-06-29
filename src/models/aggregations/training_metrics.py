"""Training Metrics aggregation model for workout and training load analysis."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..enums import SportType


@dataclass
class TrainingMetricsRecord:
    """Daily aggregation combining all training-related metrics.
    
    This model combines data from multiple sources:
    - Workouts: Whoop, Oura, Hevy (sport, duration, strain)
    - Training Load: Cross-platform strain/intensity metrics
    
    Perfect for:
    - Training load progression tracking
    - Sport-specific analysis
    - Strain vs recovery correlation
    - Training volume optimization
    - Periodization planning
    """
    
    # Core identifiers
    date: date
    day: str  # Day of week (Mon, Tue, etc.)
    
    # Primary training metrics
    sport: Optional[SportType] = None     # Primary sport for the day
    duration: Optional[int] = None        # Total training duration (minutes)
    
    # Additional derived fields (calculated by aggregator)
    workout_count: Optional[int] = None   # Number of workouts this day
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        # Calculate day of week from date
        if not self.day:
            self.day = self.date.strftime("%a")  # Mon, Tue, Wed, etc.
