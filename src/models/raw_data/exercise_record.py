"""Exercise record model for structured exercise data with sets and reps."""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from ..enums import DataSource


@dataclass
class ExerciseRecord:
    """Structured exercise record with sets and reps."""
    timestamp: datetime
    date: date  # Date extracted from timestamp for easier filtering
    source: DataSource
    workout_id: str
    exercise_name: str
    
    # Set details
    set_number: int
    set_type: str  # normal, warmup, failure, etc.
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
