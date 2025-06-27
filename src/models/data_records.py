"""Data record models for structured health data.

This module contains dataclass definitions for all health data record types
used throughout the processing pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from .enums import DataSource, SportType, RecoveryLevel, SleepStage


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


@dataclass
class RecoveryRecord:
    """Structured recovery data record."""
    timestamp: Optional[str] = None  # Raw timestamp from API for timezone handling
    date: Optional[date] = None
    source: Optional[DataSource] = None
    
    # Recovery metrics
    recovery_score: Optional[int] = None
    
    # Heart rate variability
    hrv_rmssd: Optional[float] = None
    
    # Heart rate metrics
    resting_hr: Optional[int] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)


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


@dataclass
class NutritionRecord:
    """Structured nutrition data record with comprehensive micronutrient tracking."""
    date: date
    source: DataSource
    
    # Macronutrients (required)
    calories: int
    protein: float
    carbs: float
    fat: float
    
    # Additional macronutrients
    alcohol: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    
    # Vitamins
    vitamin_a: Optional[float] = None  # Vitamin A (micrograms)
    vitamin_c: Optional[float] = None  # Vitamin C (milligrams)
    vitamin_d: Optional[float] = None  # Vitamin D (International Units)
    vitamin_e: Optional[float] = None  # Vitamin E (milligrams)
    vitamin_k: Optional[float] = None  # Vitamin K (micrograms)
    
    # B Vitamins
    b1_thiamine: Optional[float] = None     # B1 Thiamine (milligrams)
    b2_riboflavin: Optional[float] = None   # B2 Riboflavin (milligrams)
    b3_niacin: Optional[float] = None       # B3 Niacin (milligrams)
    b6_pyridoxine: Optional[float] = None   # B6 Pyridoxine (milligrams)
    b12_cobalamin: Optional[float] = None   # B12 Cobalamin (micrograms)
    folate: Optional[float] = None          # Folate (micrograms)
    
    # Essential Minerals
    calcium: Optional[float] = None    # Calcium (milligrams)
    iron: Optional[float] = None       # Iron (milligrams)
    magnesium: Optional[float] = None  # Magnesium (milligrams)
    potassium: Optional[float] = None  # Potassium (milligrams)
    sodium: Optional[float] = None     # Sodium (milligrams)
    zinc: Optional[float] = None       # Zinc (milligrams)
    
    # Fat Breakdown
    cholesterol: Optional[float] = None        # Cholesterol (milligrams)
    saturated_fat: Optional[float] = None       # Saturated fat (grams)
    monounsaturated_fat: Optional[float] = None # Monounsaturated fat (grams)
    polyunsaturated_fat: Optional[float] = None # Polyunsaturated fat (grams)
    omega3: Optional[float] = None              # Omega-3 fatty acids (grams)
    omega6: Optional[float] = None              # Omega-6 fatty acids (grams)
    
    # Other Nutrients
    caffeine: Optional[float] = None   # Caffeine (milligrams)
    water: Optional[float] = None       # Water content (grams)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
    
    @property
    def protein_percentage(self) -> float:
        """Calculate protein percentage of total calories."""
        if self.calories == 0:
            return 0.0
        return (self.protein * 4) / self.calories * 100
    
    @property
    def carbs_percentage(self) -> float:
        """Calculate carbohydrate percentage of total calories."""
        if self.calories == 0:
            return 0.0
        return (self.carbs * 4) / self.calories * 100
    
    @property
    def fat_percentage(self) -> float:
        """Calculate fat percentage of total calories."""
        if self.calories == 0:
            return 0.0
        return (self.fat * 9) / self.calories * 100


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
