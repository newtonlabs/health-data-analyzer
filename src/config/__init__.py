"""Configuration system for health-data-analyzer.

This module provides user-configurable settings that are used across
all stages of the data pipeline: API services, extractors, transformers,
aggregators, and reporting.
"""

from .user_config import (
    UserConfig,
    default_config,
    
    # Activity and target settings
    STRENGTH_ACTIVITIES,
    CALORIC_TARGETS,
    RECOVERY_THRESHOLDS,
    MACRO_TARGETS,
    HR_ZONES,
    
    # API ID mappings
    WHOOP_SPORT_MAPPINGS,
    OURA_ACTIVITY_MAPPINGS,
    WITHINGS_MEASUREMENT_TYPES
)

__all__ = [
    # Main configuration class
    'UserConfig',
    'default_config',
    
    # Activity and target settings
    'STRENGTH_ACTIVITIES',
    'CALORIC_TARGETS', 
    'RECOVERY_THRESHOLDS',
    'MACRO_TARGETS',
    'HR_ZONES',
    
    # API ID mappings
    'WHOOP_SPORT_MAPPINGS',
    'OURA_ACTIVITY_MAPPINGS',
    'WITHINGS_MEASUREMENT_TYPES'
]
