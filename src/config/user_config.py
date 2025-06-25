"""User-configurable constants and settings for health data models.

This module contains values that users might want to customize,
such as caloric targets, recovery thresholds, and activity classifications.
These can be moved to a YAML configuration file in the future.
"""

from typing import Dict, List


# Activity Classifications
# These determine how activities are categorized for analysis
STRENGTH_ACTIVITIES: List[str] = [
    "strength_training",
    "weightlifting",
    "powerlifting",
    "bodybuilding",
    "crossfit",
    "functional_fitness",
    "resistance_training"
]

# Caloric Targets
# Daily calorie targets based on activity type
CALORIC_TARGETS: Dict[str, int] = {
    "strength_day": 2400,  # Target calories on strength training days
    "rest_day": 2000       # Target calories on rest days
}

# Recovery Score Thresholds
# Thresholds for categorizing recovery levels
RECOVERY_THRESHOLDS: Dict[str, int] = {
    "low": 50,      # Below this is considered low recovery
    "moderate": 70  # Above this is considered high recovery
}

# Macro Ratio Targets (example of future configurable values)
MACRO_TARGETS: Dict[str, Dict[str, float]] = {
    "strength_day": {
        "protein_pct": 30.0,  # 30% protein
        "carbs_pct": 40.0,    # 40% carbs
        "fat_pct": 30.0       # 30% fat
    },
    "rest_day": {
        "protein_pct": 25.0,  # 25% protein
        "carbs_pct": 35.0,    # 35% carbs
        "fat_pct": 40.0       # 40% fat
    }
}

# Heart Rate Zones (example of user-specific configuration)
HR_ZONES: Dict[str, Dict[str, int]] = {
    "default": {
        "zone1_max": 140,  # Recovery zone
        "zone2_max": 160,  # Aerobic zone
        "zone3_max": 180,  # Anaerobic zone
        "zone4_max": 200   # Max effort zone
    }
}

# API ID Mappings
# These map API-specific IDs to human-friendly names and our internal sport types

# Whoop Sport ID Mappings
# Users can customize these based on their observed sport IDs
WHOOP_SPORT_MAPPINGS: Dict[int, Dict[str, str]] = {
    18: {"name": "Rowing", "sport_type": "rowing"},
    63: {"name": "Walking", "sport_type": "walking"},
    65: {"name": "Elliptical", "sport_type": "other"},
    66: {"name": "Stairmaster", "sport_type": "other"},
    45: {"name": "Weightlifting", "sport_type": "strength_training"},
    123: {"name": "Strength", "sport_type": "strength_training"},
    # Add more as users discover them in their data
}

# Oura Activity Class Mappings
# Oura uses different classification system
OURA_ACTIVITY_MAPPINGS: Dict[str, Dict[str, str]] = {
    "high": {"name": "High Intensity", "sport_type": "other"},
    "medium": {"name": "Medium Intensity", "sport_type": "other"},
    "low": {"name": "Low Intensity", "sport_type": "walking"},
    "rest": {"name": "Rest", "sport_type": "other"},
}

# Withings Measurement Type Mappings
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
    
    This class can be extended to load settings from YAML files
    or environment variables in the future.
    """
    
    def __init__(self):
        """Initialize with default values."""
        self.strength_activities = STRENGTH_ACTIVITIES.copy()
        self.caloric_targets = CALORIC_TARGETS.copy()
        self.recovery_thresholds = RECOVERY_THRESHOLDS.copy()
        self.macro_targets = MACRO_TARGETS.copy()
        self.hr_zones = HR_ZONES.copy()
        self.whoop_sport_mappings = WHOOP_SPORT_MAPPINGS.copy()
        self.oura_activity_mappings = OURA_ACTIVITY_MAPPINGS.copy()
        self.withings_measurement_types = WITHINGS_MEASUREMENT_TYPES.copy()
    
    def is_strength_activity(self, sport: str) -> bool:
        """Check if a sport is considered a strength activity.
        
        Args:
            sport: Sport name to check
            
        Returns:
            True if sport is a strength activity
        """
        return sport.lower() in [s.lower() for s in self.strength_activities]
    
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
        
        Args:
            sport_id: Whoop API sport ID
            
        Returns:
            Human-friendly sport name
        """
        return self.get_whoop_sport_info(sport_id)["name"]
    
    def get_whoop_sport_type(self, sport_id: int) -> str:
        """Get internal sport type from Whoop sport ID.
        
        Args:
            sport_id: Whoop API sport ID
            
        Returns:
            Internal sport type string
        """
        return self.get_whoop_sport_info(sport_id)["sport_type"]
    
    def get_oura_activity_info(self, activity_class: str) -> Dict[str, str]:
        """Get activity information from Oura activity class.
        
        Args:
            activity_class: Oura activity classification
            
        Returns:
            Dictionary with 'name' and 'sport_type' keys, or default values
        """
        return self.oura_activity_mappings.get(activity_class, {
            "name": f"Unknown Activity {activity_class}",
            "sport_type": "unknown"
        })
    
    def get_withings_measurement_name(self, measurement_type: int) -> str:
        """Get measurement name from Withings measurement type ID.
        
        Args:
            measurement_type: Withings API measurement type ID
            
        Returns:
            Measurement name string
        """
        return self.withings_measurement_types.get(measurement_type, f"unknown_type_{measurement_type}")
    
    def add_whoop_sport_mapping(self, sport_id: int, name: str, sport_type: str) -> None:
        """Add or update a Whoop sport mapping.
        
        Args:
            sport_id: Whoop API sport ID
            name: Human-friendly name
            sport_type: Internal sport type
        """
        self.whoop_sport_mappings[sport_id] = {
            "name": name,
            "sport_type": sport_type
        }

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'UserConfig':
        """Load configuration from YAML file (future implementation).
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            UserConfig instance with loaded settings
        """
        # TODO: Implement YAML loading
        # import yaml
        # with open(yaml_path, 'r') as f:
        #     config_data = yaml.safe_load(f)
        # return cls.from_dict(config_data)
        return cls()
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'UserConfig':
        """Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            UserConfig instance with provided settings
        """
        config = cls()
        
        if 'strength_activities' in config_dict:
            config.strength_activities = config_dict['strength_activities']
        
        if 'caloric_targets' in config_dict:
            config.caloric_targets.update(config_dict['caloric_targets'])
        
        if 'recovery_thresholds' in config_dict:
            config.recovery_thresholds.update(config_dict['recovery_thresholds'])
        
        if 'macro_targets' in config_dict:
            config.macro_targets.update(config_dict['macro_targets'])
        
        if 'hr_zones' in config_dict:
            config.hr_zones.update(config_dict['hr_zones'])
        
        if 'whoop_sport_mappings' in config_dict:
            config.whoop_sport_mappings.update(config_dict['whoop_sport_mappings'])
        
        if 'oura_activity_mappings' in config_dict:
            config.oura_activity_mappings.update(config_dict['oura_activity_mappings'])
        
        if 'withings_measurement_types' in config_dict:
            config.withings_measurement_types.update(config_dict['withings_measurement_types'])
        
        return config


# Default global configuration instance
# This can be replaced with user-specific configuration
default_config = UserConfig()
