"""Configuration system for health-data-analyzer.

This module provides user-configurable settings that are used across
all stages of the data pipeline. Contains ONLY settings that exist
in the current codebase - no speculative features.
"""

from .user_config import (
    UserConfig,
    default_config,
    
    # Settings that actually exist in current app_config.py
    STRENGTH_ACTIVITIES,
    CALORIC_TARGETS,
    RECOVERY_THRESHOLDS,
    WHOOP_SPORT_MAPPINGS,
    WITHINGS_MEASUREMENT_TYPES
)

__all__ = [
    # Main configuration class
    'UserConfig',
    'default_config',
    
    # Settings that actually exist in current codebase
    'STRENGTH_ACTIVITIES',
    'CALORIC_TARGETS', 
    'RECOVERY_THRESHOLDS',
    'WHOOP_SPORT_MAPPINGS',
    'WITHINGS_MEASUREMENT_TYPES'
]
