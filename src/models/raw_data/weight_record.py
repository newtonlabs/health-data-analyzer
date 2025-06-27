"""Weight record model for structured weight measurement data."""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from ..enums import DataSource


@dataclass
class WeightRecord:
    """Structured weight measurement record."""
    timestamp: datetime
    date: date  # Date extracted from timestamp for easier filtering
    source: DataSource
    weight_kg: float
    
    # Optional body composition metrics
    body_fat_percentage: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    water_percentage: Optional[float] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
