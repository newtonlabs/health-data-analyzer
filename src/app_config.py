"""Central application configuration.

This module provides a centralized configuration for the entire application.
It consolidates all constants and configuration values from various modules
into a single location for easier maintenance and consistency.
"""

import os


class AppConfig:
    """Central application configuration.

    This class serves as a single source of truth for all configuration values
    used throughout the application. It combines settings from:
    - Analysis configuration (analyzer_config.py)
    - Reporting configuration (reporting_config.py)
    - Data source client constants (hevy_constants.py, whoop_constants.py, withings_constants.py)

    Using a flat structure with consistent prefixing to maintain organization.
    """

    # ===== Analysis Configuration =====

    # Numeric precision for rounding
    ANALYSIS_NUMERIC_PRECISION: dict[str, int] = {
        "calories": 0,
        "protein": 1,
        "carbs": 1,
        "fat": 1,
        "strain": 1,
        "avg_hr": 0,
        "max_hr": 0,
        "kilojoules": 0,
        "altitude_gain": 0,
        "hrv_rmssd": 1,
        "resting_hr": 1,
        "spo2": 1,
        "sleep_need": 1,
        "sleep_actual": 1,
        "weight": 1,  # Weight with 1 decimal place
        "alcohol": 1,  # Alcohol with 1 decimal place
    }

    # Excluded sports from analysis (used by metrics aggregation)
    ANALYSIS_EXCLUDED_SPORTS: list[str] = [
        "Walking",  # Common background activity
        "Other",  # Too generic
        "Rest",  # Not a workout
    ]

    # Strength activities (prioritized in weekly macros)
    ANALYSIS_STRENGTH_ACTIVITIES: list[str] = [
        "Strength",  # Weight training
        "Weightlifting",  # Weight training
        "Strength Training",  # From SportType.STRENGTH_TRAINING formatting
    ]

    # Mapping of Oura resilience levels to numeric scores (equal zones)
    ANALYSIS_RESILIENCE_LEVEL_SCORES: dict[str, int] = {
        "exceptional": 80,  # Exceptional resilience (80-100)
        "strong": 60,  # Strong resilience (60-80)
        "solid": 40,  # Solid resilience (40-60)
        "adequate": 20,  # Adequate resilience (20-40)
        "limited": 0,  # Limited resilience (0-20)
    }

    # ===== Reporting Configuration =====

    # Charts directory - within reports directory for easier PDF generation
    REPORTING_CHARTS_DIR = os.path.join("data", "05_reports", "charts")

    # Chart colors
    REPORTING_COLORS = {
        # Recovery chart colors
        "recovery_high": "#2ecc71",  # Green for high recovery (≥70)
        "recovery_medium": "#f1c40f",  # Yellow for moderate recovery (50-69)
        "recovery_low": "#e74c3c",  # Red for low recovery scores (<50)
        # Sleep line colors
        "sleep_need": "#1E88E5",  # Blue for sleep need line
        "sleep_actual": "#7B1F1F",  # Dark red for sleep actual line
        # Resilience chart colors
        "resilience_strong": "#007BFF",  # Blue for strong resilience target line
        # Macro ratio colors
        "protein": "#7B1F1F",  # Dark red for protein
        "carbs": "#333333",  # Black for carbs
        "fat": "#999999",  # Gray for fat
        "alcohol": "#FF8C00",  # Dark orange for alcohol
        # Text and UI colors
        "text": "#666666",  # Gray for text elements
        "grid": "#cccccc",  # Light gray for grid lines
        "chart_border": "#A9A9A9",  # Darker gray for chart borders/spines
        "resilience_x_grid": "#EDEDED",  # Very light gray for resilience x-axis grid
    }

    # Chart thresholds
    REPORTING_THRESHOLDS = {
        # Recovery thresholds
        "recovery_high": 66,  # High recovery threshold (≥66)
        "recovery_medium": 34,  # Medium recovery threshold (34-65)
        "recovery_low": 33,  # Low recovery threshold (≤33)
        # Macro ratio label thresholds
        "macro_label_full": 15,  # Show full label if segment ≥15%
        "macro_label_percent": 8,  # Show percentage only if segment between 8-15%
    }

    # Chart styling
    REPORTING_STYLING = {
        "bar_alpha": 0.7,  # Transparency for bars
        "line_thickness": 1.5,  # Line thickness for sleep lines (default)
        "default_line_width": 1.5,  # Default line width for plots
        "grid_line_width": 0.7,  # Line width for grid lines
        "default_marker_size": 4,  # Default marker size for plots
        "chart_height": 4.8,  # Standard chart height for recovery and nutrition charts
        "chart_height_compact": 2.0,  # Compact chart height for minimalist design
        "grid_opacity": 0.5,  # Grid line opacity
        "default_font_size": 9,  # Default font size for labels and legends
        "tick_font_size": 8,  # Font size for axis ticks
        "weight_line_alpha": 0.3,  # Alpha for weight line
        "weight_trend_alpha": 0.9,  # Alpha for weight trend line
        "macro_bar_alpha": 1.0,  # Alpha for macro bars and their legends
        "resilience_band_font_size": 8,  # Font size for resilience band labels
        "weight_line_width": 2,  # Line width for weight line
        "legend_font_size": 9,  # Default font size for legends
        "legend_columns": 4,  # Default number of columns for legends
        "legend_vertical_offset": -0.18,  # Vertical offset for legends (negative moves it up)
    }

    # Caloric targets by activity type
    REPORTING_CALORIC_TARGETS = {
        "strength": 1800,  # Target calories for strength training days
        "rest": 1545,  # Target calories for rest days
    }

    # Calorie conversion factors for macronutrients
    REPORTING_CALORIE_FACTORS = {
        "protein": 4.1,  # 4.1 calories per gram
        "carbs": 4.1,  # 4.1 calories per gram
        "fat": 9.44,  # 9.44 calories per gram
        "alcohol": 6.93,  # 6.93 calories per gram
    }

    # ===== Data Source Client Configuration =====

    # Hevy API configuration
    HEVY_DEFAULT_PAGE_SIZE = 10

    # Whoop Sport ID Mappings
    WHOOP_SPORT_MAPPINGS = {
        0: {"name": "Running"}, 
        18: {"name": "Rowing"},
        63: {"name": "Walking"},
        65: {"name": "Elliptical"},
        66: {"name": "Stairmaster"},
        45: {"name": "Weightlifting"},
        123: {"name": "Strength"},
    }

    # Sport Type Classification Arrays
    STRENGTH_SPORTS = [
        "weightlifting", "strength training", "weight training", 
        "resistance training", "lifting", "strength", "weights",
        "powerlifting", "bodybuilding", "crossfit", "functional training"
    ]

    CARDIO_SPORTS = [
        "running", "jogging", "cycling", "biking", "swimming", 
        "rowing", "elliptical", "stairmaster", "treadmill",
        "spinning", "cardio", "aerobic", "hiit", "interval training"
    ]

    WALKING_SPORTS = [
        "walking", "walk", "hiking", "trekking", "stroll", "housework"
    ]

    # ===== Helper Methods =====

    @staticmethod
    def get_whoop_sport_info(sport_id: int) -> dict[str, str]:
        """Get sport information from Whoop sport ID.
        
        Args:
            sport_id: Whoop API sport ID
            
        Returns:
            Dictionary with 'name' key
        """
        return AppConfig.WHOOP_SPORT_MAPPINGS.get(sport_id, {
            "name": f"Unknown Sport {sport_id}"
        })

    @staticmethod
    def get_sport_type_from_name(sport_name: str) -> 'SportType':
        """Map sport name to SportType enum with configurable fallback logic.
        
        Args:
            sport_name: Human-readable sport name (e.g., "Walking", "Weightlifting")
            
        Returns:
            SportType enum value
        """
        from src.models.enums import SportType
        
        if not sport_name:
            return SportType.UNKNOWN  # Default fallback
        
        # Convert to lowercase for case-insensitive matching
        name_lower = sport_name.lower()
        
        # Check strength sports
        if any(pattern in name_lower for pattern in AppConfig.STRENGTH_SPORTS):
            return SportType.STRENGTH_TRAINING
        
        # Check walking sports
        if any(pattern in name_lower for pattern in AppConfig.WALKING_SPORTS):
            return SportType.WALKING
        
        # Check cardio sports
        if any(pattern in name_lower for pattern in AppConfig.CARDIO_SPORTS):
            return SportType.CARDIO
        
        # Final fallback for unrecognized activities
        return SportType.UNKNOWN
