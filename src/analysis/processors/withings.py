"""Processor for Withings data.

This module provides functionality to process and analyze data from the Withings API.
"""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from src.analysis.processors.base import BaseProcessor
from src.app_config import AppConfig


class WithingsProcessor(BaseProcessor):
    def __init__(self):
        """Initialize the WithingsProcessor."""
        super().__init__()
    """Processor for Withings data."""

    def process_data(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> dict[str, pd.DataFrame]:
        """Process Withings data into DataFrames.

        Args:
            raw_data: Raw data from the Withings API
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            Dictionary of DataFrames with processed data
        """
        result = {}

        # Process weight data
        if "weight" in raw_data:
            result["weight"] = self.process_weight_data(
                raw_data["weight"], start_date, end_date
            )

        return result

    def process_weight_data(
        self, weight_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Process Withings weight data.

        Args:
            weight_data: Raw weight data from the Withings API
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with processed weight data including body composition
        """
        # Extract weight data with body composition
        weight_records = []

        if "measuregrps" in weight_data:
            # Process each measurement group from the Withings API
            measuregrps = weight_data.get("measuregrps", [])

            for group in measuregrps:
                timestamp = group.get("date")
                if not timestamp:
                    continue

                # Convert timestamp from UTC to local time using our utility
                dt_local = self.parse_timestamp(timestamp)
                if not dt_local:
                    continue

                # Skip if outside date range
                if start_date and dt_local.date() < start_date.date():
                    continue
                if end_date and dt_local.date() > end_date.date():
                    continue

                # Initialize record with basic info
                record = {
                    "date": dt_local.date(),
                    "timestamp": timestamp,
                    "weight": None,
                    "body_fat_percentage": None,
                    "muscle_mass_kg": None,
                    "bone_mass_kg": None,
                    "water_percentage": None,
                }

                # Process all measurements in this group
                for measure in group.get("measures", []):
                    measure_type = measure.get("type")
                    value = measure.get("value", 0)
                    unit = measure.get("unit", 0)
                    
                    # Convert value using unit multiplier (e.g., -3 means ×10^-3)
                    actual_value = value * (10 ** unit) if value is not None else None
                    
                    # Map measurement types to record fields
                    if measure_type == AppConfig.WITHINGS_MEASUREMENT_TYPE_WEIGHT:
                        record["weight"] = actual_value
                    elif measure_type == AppConfig.WITHINGS_MEASUREMENT_TYPE_FAT_RATIO:
                        record["body_fat_percentage"] = actual_value
                    elif measure_type == AppConfig.WITHINGS_MEASUREMENT_TYPE_MUSCLE_MASS:
                        record["muscle_mass_kg"] = actual_value
                    elif measure_type == AppConfig.WITHINGS_MEASUREMENT_TYPE_BONE_MASS:
                        record["bone_mass_kg"] = actual_value
                    elif measure_type == AppConfig.WITHINGS_MEASUREMENT_TYPE_WATER_PERCENTAGE:
                        record["water_percentage"] = actual_value
                    elif measure_type == AppConfig.WITHINGS_MEASUREMENT_TYPE_FAT_FREE_MASS:
                        # Fat-free mass can be used to calculate water percentage
                        # Water % ≈ (Fat-free mass - Muscle mass - Bone mass) / Weight * 100
                        # For now, we'll store it as a separate field if needed
                        pass

                # Only add record if we have at least weight data
                if record["weight"] is not None:
                    weight_records.append(record)

        # Create DataFrame
        if not weight_records:
            return pd.DataFrame(columns=["date", "weight", "body_fat_percentage", "muscle_mass_kg", "bone_mass_kg", "water_percentage", "timestamp"])

        # Create DataFrame with all body composition fields
        df = pd.DataFrame(weight_records)

        # Sort by timestamp so the latest measurement per day is always kept
        df = df.sort_values("timestamp").drop_duplicates(subset=["date"], keep="last")

        return df

    def save_processed_data(self, data: dict[str, pd.DataFrame]) -> dict[str, str]:
        """Save processed Withings data to CSV files.

        Args:
            data: Dictionary of DataFrames with processed data

        Returns:
            Dictionary of paths to the saved files
        """
        from src.utils.file_utils import save_dataframe_to_file

        result = {}

        # Save weight data
        if "weight" in data and not data["weight"].empty:
            weight_path = save_dataframe_to_file(
                data["weight"], name="withings-weight-data", subdir="processing"
            )
            result["weight"] = weight_path

        return result
