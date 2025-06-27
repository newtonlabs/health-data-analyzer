"""Raw data models for structured health data from APIs.

These models represent direct API responses converted to structured formats.
They contain minimal business logic and focus on data validation and normalization.
"""

from .activity_record import ActivityRecord
from .exercise_record import ExerciseRecord
from .nutrition_record import NutritionRecord
from .recovery_record import RecoveryRecord
from .resilience_record import ResilienceRecord
from .sleep_record import SleepRecord
from .weight_record import WeightRecord
from .workout_record import WorkoutRecord

__all__ = [
    "ActivityRecord",
    "ExerciseRecord", 
    "NutritionRecord",
    "RecoveryRecord",
    "ResilienceRecord",
    "SleepRecord",
    "WeightRecord",
    "WorkoutRecord",
]
