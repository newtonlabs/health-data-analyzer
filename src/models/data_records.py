"""Data record models for structured health data.

This module contains dataclass definitions for all health data record types
used throughout the processing pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from .enums import DataSource, SportType, WorkoutIntensity, RecoveryLevel, SleepStage


@dataclass
class WorkoutRecord:
    """Structured workout/exercise record."""
    timestamp: datetime
    source: DataSource
    sport: SportType
    duration_minutes: int
    
    # Optional metrics (vary by source)
    strain_score: Optional[float] = None
    calories: Optional[int] = None
    average_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    intensity: Optional[WorkoutIntensity] = None
    
    # Hevy-specific fields
    exercise_count: Optional[int] = None
    set_count: Optional[int] = None
    volume_kg: Optional[float] = None
    
    # Raw data for debugging/analysis
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
        if isinstance(self.sport, str):
            try:
                self.sport = SportType(self.sport)
            except ValueError:
                self.sport = SportType.UNKNOWN
        if isinstance(self.intensity, str):
            self.intensity = WorkoutIntensity(self.intensity)


@dataclass
class RecoveryRecord:
    """Structured recovery/readiness record."""
    date: date
    source: DataSource
    
    # Core recovery metrics
    recovery_score: Optional[int] = None
    recovery_level: Optional[RecoveryLevel] = None
    
    # Heart rate variability
    hrv_rmssd: Optional[float] = None
    hrv_score: Optional[int] = None
    
    # Heart rate metrics
    resting_hr: Optional[int] = None
    hr_variability: Optional[float] = None
    
    # Sleep-related recovery metrics
    sleep_performance: Optional[float] = None
    sleep_consistency: Optional[float] = None
    
    # Raw data for debugging/analysis
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
        if isinstance(self.recovery_level, str):
            self.recovery_level = RecoveryLevel(self.recovery_level)
        
        # Auto-calculate recovery level if not provided
        if self.recovery_level is None and self.recovery_score is not None:
            if self.recovery_score >= 70:
                self.recovery_level = RecoveryLevel.HIGH
            elif self.recovery_score >= 50:
                self.recovery_level = RecoveryLevel.MODERATE
            else:
                self.recovery_level = RecoveryLevel.LOW


@dataclass
class SleepRecord:
    """Structured sleep data record."""
    date: date
    source: DataSource
    
    # Sleep duration
    total_sleep_minutes: Optional[int] = None
    time_in_bed_minutes: Optional[int] = None
    sleep_efficiency: Optional[float] = None  # Percentage
    
    # Sleep stages (in minutes)
    light_sleep_minutes: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    
    # Sleep quality metrics
    sleep_score: Optional[int] = None
    sleep_need_minutes: Optional[int] = None
    sleep_debt_minutes: Optional[int] = None
    
    # Sleep timing
    bedtime: Optional[datetime] = None
    wake_time: Optional[datetime] = None
    
    # Raw data for debugging/analysis
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)


@dataclass
class WeightRecord:
    """Structured weight measurement record."""
    timestamp: datetime
    source: DataSource
    weight_kg: float
    
    # Optional body composition metrics
    body_fat_percentage: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    water_percentage: Optional[float] = None
    
    # Raw data for debugging/analysis
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)


@dataclass
class NutritionRecord:
    """Structured nutrition data record."""
    date: date
    source: DataSource
    
    # Macronutrients
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    
    # Optional micronutrients
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    
    # Meal timing and context
    meal_count: Optional[int] = None
    is_strength_day: Optional[bool] = None
    
    # Raw data for debugging/analysis
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
    
    @property
    def protein_percentage(self) -> float:
        """Calculate protein percentage of total calories."""
        if self.calories == 0:
            return 0.0
        return (self.protein_g * 4) / self.calories * 100
    
    @property
    def carbs_percentage(self) -> float:
        """Calculate carbohydrate percentage of total calories."""
        if self.calories == 0:
            return 0.0
        return (self.carbs_g * 4) / self.calories * 100
    
    @property
    def fat_percentage(self) -> float:
        """Calculate fat percentage of total calories."""
        if self.calories == 0:
            return 0.0
        return (self.fat_g * 9) / self.calories * 100


@dataclass
class ActivityRecord:
    """Structured general activity record (steps, calories, etc.)."""
    date: date
    source: DataSource
    
    # Activity metrics
    steps: Optional[int] = None
    active_calories: Optional[int] = None
    total_calories: Optional[int] = None
    distance_meters: Optional[float] = None
    
    # Activity time
    active_minutes: Optional[int] = None
    sedentary_minutes: Optional[int] = None
    
    # Activity intensity zones (in minutes)
    low_intensity_minutes: Optional[int] = None
    moderate_intensity_minutes: Optional[int] = None
    high_intensity_minutes: Optional[int] = None
    
    # Raw data for debugging/analysis
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
