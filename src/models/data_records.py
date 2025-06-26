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
    timestamp: Optional[str] = None  # Raw timestamp from API for timezone handling
    date: Optional[date] = None
    source: Optional[DataSource] = None
    
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
    timestamp: Optional[str] = None  # Raw timestamp from API for timezone handling
    date: Optional[date] = None
    source: Optional[DataSource] = None
    
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
    
    # Meal timing and context
    meal_count: Optional[int] = None
    
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
    source: DataSource
    workout_id: str
    exercise_name: str
    
    # Set details
    set_number: int
    set_type: str  # normal, warmup, failure, etc.
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    distance_meters: Optional[float] = None
    duration_seconds: Optional[int] = None
    rpe: Optional[int] = None  # Rate of Perceived Exertion
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
