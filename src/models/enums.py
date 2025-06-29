"""Enumerations for health data models.

This module contains only fixed enumeration values that are actually used
in the current codebase. No speculative or unused enum values.
"""

from enum import Enum


class DataSource(Enum):
    """Enumeration of supported data sources."""
    WHOOP = "whoop"
    OURA = "oura"
    WITHINGS = "withings"
    HEVY = "hevy"
    NUTRITION_FILE = "nutrition_file"


class SportType(Enum):
    """Enumeration of sport/activity types.
    
    Categories with configurable mapping:
    - STRENGTH_TRAINING: weightlifting, strength training, etc.
    - WALKING: walking activities
    - CARDIO: running, cycling, etc.
    - REST: rest days with no significant activity
    - UNKNOWN: fallback for unrecognized activities
    """
    STRENGTH_TRAINING = "strength_training"
    WALKING = "walking"
    CARDIO = "cardio"
    REST = "rest"
    UNKNOWN = "unknown"


class WorkoutIntensity(Enum):
    """Enumeration of workout intensity levels.
    
    Currently used in WorkoutRecord but not populated by extractors yet.
    Keeping minimal set for future use.
    """
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RecoveryLevel(Enum):
    """Enumeration of recovery levels.
    
    Used by recovery threshold calculations in config.
    """
    LOW = "low"          # < 50
    MODERATE = "moderate"  # 50-69
    HIGH = "high"        # >= 70


class SleepStage(Enum):
    """Enumeration of sleep stages.
    
    Currently used in SleepRecord but not populated by extractors yet.
    Keeping for future sleep data processing.
    """
    AWAKE = "awake"
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"
