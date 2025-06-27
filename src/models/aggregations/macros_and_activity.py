"""Macros and Activity aggregation model for nutrition and movement analysis."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class MacrosAndActivityRecord:
    """Daily aggregation combining nutrition macros with activity metrics.
    
    This model combines data from multiple sources:
    - Nutrition: Cronometer/manual entry (calories, protein, carbs, fat, alcohol)
    - Activity: Oura Ring (activity score, steps)
    - Weight: Withings scale (daily weight measurement)
    
    Perfect for:
    - Daily nutrition vs activity correlation analysis
    - Weight management tracking
    - Macro balance optimization
    - Energy balance calculations
    """
    
    # Core identifiers
    date: date
    day: str  # Day of week (Mon, Tue, etc.)
    
    # Nutrition metrics (from Cronometer/manual entry)
    calories: Optional[int] = None
    protein: Optional[float] = None  # grams
    carbs: Optional[float] = None    # grams  
    fat: Optional[float] = None      # grams
    alcohol: Optional[float] = None  # grams
    
    # Activity metrics (from Oura)
    activity: Optional[int] = None   # Oura activity score (0-100)
    steps: Optional[int] = None      # Daily step count
    
    # Body metrics (from Withings)
    weight: Optional[float] = None   # kg
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        # Calculate day of week from date
        if not self.day:
            self.day = self.date.strftime("%a")  # Mon, Tue, Wed, etc.
