"""Health data models for structured data representation.

This module provides both raw data models (direct API representations)
and aggregation models (purpose-built for analysis and reporting).
"""

# Raw data models (from APIs)
from .raw_data import (
    ActivityRecord,
    ExerciseRecord,
    NutritionRecord,
    RecoveryRecord,
    ResilienceRecord,
    SleepRecord,
    WeightRecord,
    WorkoutRecord,
)

# Aggregation models (for analysis)
from .aggregations import (
    MacrosAndActivityRecord,
    RecoveryMetricsRecord,
    TrainingMetricsRecord,
)

# Enums
from .enums import DataSource, SportType, RecoveryLevel, SleepStage

__all__ = [
    # Raw data models
    "ActivityRecord",
    "ExerciseRecord",
    "NutritionRecord", 
    "RecoveryRecord",
    "ResilienceRecord",
    "SleepRecord",
    "WeightRecord",
    "WorkoutRecord",
    # Aggregation models
    "MacrosAndActivityRecord",
    "RecoveryMetricsRecord",
    "TrainingMetricsRecord",
    # Enums
    "DataSource",
    "SportType", 
    "RecoveryLevel",
    "SleepStage",
]
