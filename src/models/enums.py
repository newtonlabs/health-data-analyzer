"""Enumerations and constants for health data models."""

from enum import Enum


class DataSource(Enum):
    """Enumeration of supported data sources."""
    WHOOP = "whoop"
    OURA = "oura"
    WITHINGS = "withings"
    HEVY = "hevy"
    NUTRITION_FILE = "nutrition_file"


class SportType(Enum):
    """Enumeration of sport/activity types."""
    # Whoop sport IDs
    CYCLING = "cycling"
    RUNNING = "running"
    WALKING = "walking"
    STRENGTH_TRAINING = "strength_training"
    YOGA = "yoga"
    SWIMMING = "swimming"
    BASKETBALL = "basketball"
    SOCCER = "soccer"
    TENNIS = "tennis"
    GOLF = "golf"
    HIKING = "hiking"
    ROWING = "rowing"
    BOXING = "boxing"
    MARTIAL_ARTS = "martial_arts"
    DANCE = "dance"
    CLIMBING = "climbing"
    SKIING = "skiing"
    SNOWBOARDING = "snowboarding"
    SURFING = "surfing"
    OTHER = "other"
    UNKNOWN = "unknown"


class WorkoutIntensity(Enum):
    """Enumeration of workout intensity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RecoveryLevel(Enum):
    """Enumeration of recovery levels."""
    LOW = "low"          # < 50
    MODERATE = "moderate"  # 50-69
    HIGH = "high"        # >= 70


class SleepStage(Enum):
    """Enumeration of sleep stages."""
    AWAKE = "awake"
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"


# Constants
STRENGTH_ACTIVITIES = [
    "strength_training",
    "weightlifting",
    "powerlifting",
    "bodybuilding",
    "crossfit",
    "functional_fitness",
    "resistance_training"
]

# Caloric targets (can be moved to config later)
CALORIC_TARGETS = {
    "strength_day": 2400,
    "rest_day": 2000
}

# Recovery score thresholds
RECOVERY_THRESHOLDS = {
    "low": 50,
    "moderate": 70
}
