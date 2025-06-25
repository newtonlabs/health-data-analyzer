"""User-configurable constants for health data models.

This module contains ONLY values that exist in the current codebase
and are actually used. No speculative or future features.
"""

from typing import Dict, List


# === EXISTING CONFIGURATION FROM APP_CONFIG.PY ===

# Activity Classifications (from ANALYSIS_STRENGTH_ACTIVITIES)
STRENGTH_ACTIVITIES: List[str] = [
    "Strength",      # From current app_config.py
    "Weightlifting", # From current app_config.py
]

# Caloric Targets (from REPORTING_CALORIC_TARGETS)
CALORIC_TARGETS: Dict[str, int] = {
    "strength_day": 2400,  # Renamed from "strength" in app_config.py
    "rest_day": 1800       # Renamed from "rest" in app_config.py
}

# Recovery Score Thresholds (from ANALYSIS_RESILIENCE_LEVEL_SCORES)
RECOVERY_THRESHOLDS: Dict[str, int] = {
    "low": 50,      # Threshold for low recovery
    "moderate": 70  # Threshold for moderate recovery (above this is high)
}

# Whoop Sport ID Mappings (from WHOOP_SPORT_NAMES)
WHOOP_SPORT_MAPPINGS: Dict[int, Dict[str, str]] = {
    18: {"name": "Rowing", "sport_type": "rowing"},
    63: {"name": "Walking", "sport_type": "walking"},
    65: {"name": "Elliptical", "sport_type": "other"},
    66: {"name": "Stairmaster", "sport_type": "other"},
    45: {"name": "Weightlifting", "sport_type": "strength_training"},
    123: {"name": "Strength", "sport_type": "strength_training"},
}

# Withings Measurement Types (from app_config.py constants)
WITHINGS_MEASUREMENT_TYPES: Dict[int, str] = {
    1: "weight",
    4: "height",
    5: "fat_free_mass",
    6: "fat_ratio",
    8: "fat_mass_weight",
    9: "diastolic_bp",
    10: "systolic_bp",
    11: "heart_rate",
    12: "temperature",
    54: "spo2",
    71: "body_temperature",
    73: "skin_temperature",
    76: "muscle_mass",
    88: "bone_mass",
    91: "pulse_wave_velocity"
}


class UserConfig:
    """Container for user-configurable settings.
    
    Contains ONLY settings that are actually used in the current codebase.
    """
    
    def __init__(self):
        """Initialize with current app_config.py values."""
        self.strength_activities = STRENGTH_ACTIVITIES.copy()
        self.caloric_targets = CALORIC_TARGETS.copy()
        self.recovery_thresholds = RECOVERY_THRESHOLDS.copy()
        self.whoop_sport_mappings = WHOOP_SPORT_MAPPINGS.copy()
        self.withings_measurement_types = WITHINGS_MEASUREMENT_TYPES.copy()
    
    def is_strength_activity(self, sport: str) -> bool:
        """Check if a sport is considered a strength activity.
        
        Args:
            sport: Sport name to check
            
        Returns:
            True if sport is a strength activity
        """
        return sport in [s.lower() for s in self.strength_activities]
    
    def get_caloric_target(self, is_strength_day: bool) -> int:
        """Get caloric target for the day type.
        
        Args:
            is_strength_day: Whether this is a strength training day
            
        Returns:
            Target calories for the day
        """
        key = "strength_day" if is_strength_day else "rest_day"
        return self.caloric_targets.get(key, 2000)
    
    def get_recovery_level(self, score: int) -> str:
        """Get recovery level based on score.
        
        Args:
            score: Recovery score (0-100)
            
        Returns:
            Recovery level string
        """
        if score >= self.recovery_thresholds["moderate"]:
            return "high"
        elif score >= self.recovery_thresholds["low"]:
            return "moderate"
        else:
            return "low"
    
    def get_whoop_sport_info(self, sport_id: int) -> Dict[str, str]:
        """Get sport information from Whoop sport ID.
        
        Args:
            sport_id: Whoop API sport ID
            
        Returns:
            Dictionary with 'name' and 'sport_type' keys, or default values
        """
        return self.whoop_sport_mappings.get(sport_id, {
            "name": f"Unknown Sport {sport_id}",
            "sport_type": "unknown"
        })
    
    def get_whoop_sport_name(self, sport_id: int) -> str:
        """Get human-friendly sport name from Whoop sport ID.
        
        Replaces AppConfig.get_whoop_sport_name() method.
        
        Args:
            sport_id: Whoop API sport ID
            
        Returns:
            Human-friendly sport name
        """
        return self.get_whoop_sport_info(sport_id)["name"]
    
    def get_withings_measurement_name(self, measurement_type: int) -> str:
        """Get measurement name from Withings measurement type ID.
        
        Args:
            measurement_type: Withings API measurement type ID
            
        Returns:
            Measurement name string
        """
        return self.withings_measurement_types.get(measurement_type, f"unknown_type_{measurement_type}")


# Default global configuration instance
default_config = UserConfig()
