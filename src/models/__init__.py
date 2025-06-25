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

# Import enums and constants
from .enums import (
    DataSource,
    SportType,
    WorkoutIntensity,
    RecoveryLevel,
    SleepStage,
    STRENGTH_ACTIVITIES,
    CALORIC_TARGETS,
    RECOVERY_THRESHOLDS
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
    
    # Constants
    'STRENGTH_ACTIVITIES',
    'CALORIC_TARGETS',
    'RECOVERY_THRESHOLDS'
]
