"""Configuration for data analyzer."""

from typing import Dict, List


class AnalyzerConfig:
    """Configuration for data analyzer."""

    # Numeric precision for rounding
    NUMERIC_PRECISION: Dict[str, int] = {
        "calories": 0,
        "protein": 1,
        "carbs": 1,
        "fat": 1,
        "strain": 1,
        "avg_hr": 0,
        "max_hr": 0,
        "kilojoules": 0,
        "distance_meters": 0,
        "altitude_gain": 0,
        "hrv_rmssd": 1,
        "resting_hr": 1,
        "spo2": 1,
        "sleep_need": 1,
        "sleep_actual": 1,
        "weight": 1,  # Weight with 1 decimal place
    }

    # Excluded sports from analysis (used by metrics aggregation)
    EXCLUDED_SPORTS: List[str] = [
        "Walking",  # Common background activity
        "Other",  # Too generic
        "Rest",  # Not a workout
    ]

    # Strength activities (prioritized in weekly macros)
    STRENGTH_ACTIVITIES: List[str] = [
        "Strength",  # Weight training
    ]

    # Mapping of Oura resilience levels to numeric scores (equal zones)
    RESILIENCE_LEVEL_SCORES: Dict[str, int] = {
        "exceptional": 80,  # Exceptional resilience (80-100)
        "strong": 60,  # Strong resilience (60-80)
        "solid": 40,  # Solid resilience (40-60)
        "adequate": 20,  # Adequate resilience (20-40)
        "limited": 0,  # Limited resilience (0-20)
    }
