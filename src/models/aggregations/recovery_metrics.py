"""Recovery Metrics aggregation model for comprehensive recovery analysis."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class RecoveryMetricsRecord:
    """Daily aggregation combining all recovery-related metrics.
    
    This model combines data from multiple sources:
    - Recovery: Whoop (recovery score, HRV, resting HR)
    - Sleep: Whoop (sleep need, actual sleep)
    - Resilience: Oura (resilience level/score)
    
    Perfect for:
    - Comprehensive recovery trend analysis
    - Sleep debt tracking
    - HRV and heart rate monitoring
    - Cross-platform recovery validation
    - Recovery vs training load correlation
    """
    
    # Core identifiers
    date: date
    day: str  # Day of week (Mon, Tue, etc.)
    
    # Recovery metrics (from Whoop)
    recovery: Optional[float] = None      # Whoop recovery score (0-100)
    hrv: Optional[float] = None           # HRV RMSSD (ms) - from recovery.hrv_rmssd
    hr: Optional[int] = None              # Resting heart rate (bpm) - from recovery.resting_hr
    
    # Sleep metrics (from Whoop)
    sleep_need: Optional[int] = None      # Sleep need (minutes) - from sleep.sleep_need_minutes
    sleep_actual: Optional[int] = None    # Actual sleep (minutes) - from sleep.total_sleep_minutes
    
    # Resilience metrics (from Oura)
    resilience_level: Optional[str] = None  # Oura resilience level (limited/adequate/solid/strong)
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        # Calculate day of week from date
        if not self.day:
            self.day = self.date.strftime("%a")  # Mon, Tue, Wed, etc.
