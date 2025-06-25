"""Data models for health data records and collections.

This module contains type-safe data models used throughout the pipeline
for structured data representation.
"""

# Import all data record types
from .data_records import (
    WorkoutRecord,
    RecoveryRecord,
    SleepRecord,
    WeightRecord,
    NutritionRecord,
    ActivityRecord
)

# Import collection types
from .collections import (
    RawDataCollection,
    ProcessedDataCollection,
    AggregatedMetrics,
    PipelineResult
)

# Import enums
from .enums import (
    DataSource,
    SportType,
    WorkoutIntensity,
    RecoveryLevel,
    SleepStage
)

# Import user-configurable constants
from src.config import (
    UserConfig,
    default_config,
    STRENGTH_ACTIVITIES,
    CALORIC_TARGETS,
    RECOVERY_THRESHOLDS,
    MACRO_TARGETS,
    HR_ZONES,
    WHOOP_SPORT_MAPPINGS,
    OURA_ACTIVITY_MAPPINGS,
    WITHINGS_MEASUREMENT_TYPES
)

__all__ = [
    # Data records
    'WorkoutRecord',
    'RecoveryRecord', 
    'SleepRecord',
    'WeightRecord',
    'NutritionRecord',
    'ActivityRecord',
    
    # Collections
    'RawDataCollection',
    'ProcessedDataCollection',
    'AggregatedMetrics',
    'PipelineResult',
    
    # Enums
    'DataSource',
    'SportType',
    'WorkoutIntensity',
    'RecoveryLevel',
    'SleepStage',
    
    # Configuration
    'UserConfig',
    'default_config',
    
    # Constants
    'STRENGTH_ACTIVITIES',
    'CALORIC_TARGETS',
    'RECOVERY_THRESHOLDS',
    'MACRO_TARGETS',
    'HR_ZONES',
    'WHOOP_SPORT_MAPPINGS',
    'OURA_ACTIVITY_MAPPINGS',
    'WITHINGS_MEASUREMENT_TYPES'
]
