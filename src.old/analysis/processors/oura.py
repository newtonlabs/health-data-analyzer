"""Processor for Oura data.

This module provides functionality to process and analyze data from the Oura API.
"""

from datetime import datetime
from typing import Any

import pandas as pd

from src.analysis.processors.base import BaseProcessor
from src.app_config import AppConfig


class OuraProcessor(BaseProcessor):
    """Processor for Oura data."""

    def __init__(self):
        """Initialize OuraProcessor."""
        super().__init__()

    def process_data(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> dict[str, pd.DataFrame]:
        """Process Oura data into DataFrames.

        Steps:
        1. Process activity data
        2. Process resilience data
        3. Return combined results

        Args:
            raw_data: Raw Oura API response containing activity and resilience data
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            Dictionary of DataFrames with processed data
        """
        result = {}

        # Process activity data
        if "activity" in raw_data:
            result["activity"] = self._process_oura_activity(
                raw_data["activity"], start_date, end_date
            )

        # Process resilience data
        if "resilience" in raw_data:
            result["resilience"] = self._process_oura_resilience(
                raw_data["resilience"], start_date, end_date
            )

        return result

    def _process_oura_activity(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Process activity data from Oura API.

        Args:
            raw_data: Raw Oura activity data
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with daily activity metrics
        """
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=["date", "steps", "active_calories", "calories_total"])

        # Return empty DataFrame if no data
        if not raw_data or "data" not in raw_data:
            self.logger.logger.debug("Invalid Oura activity data structure")
            return df

        # Extract activity data
        activity_data = []

        for activity in raw_data.get("data", []):
            if "day" in activity:
                # Extract available fields with defaults
                record = {
                    "date": activity["day"],
                    "steps": round(activity.get("steps", 0)),
                    "active_calories": activity.get("active_calories", 0),
                    "calories_total": activity.get("total_calories", 0),
                }
                activity_data.append(record)

        # Create DataFrame if we have data
        if activity_data:
            df = pd.DataFrame(activity_data)

        return df

    def _process_oura_resilience(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Process resilience data from Oura API.

        Args:
            raw_data: Raw Oura resilience data
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with daily resilience metrics
        """
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=["date", "resilience_score", "resilience_level"])

        # Return empty DataFrame if no data
        if not raw_data or "data" not in raw_data:
            self.logger.logger.debug("Invalid Oura resilience data structure")
            return df

        # Extract resilience data
        resilience_data = []
        for item in raw_data["data"]:
            # Extract date from the ID (format: YYYY-MM-DD)
            try:
                date_str = item.get("day")
                if not date_str:
                    continue

                # Convert to datetime for filtering
                # Since this is just a date without time, we don't need timezone conversion
                day_date = datetime.strptime(date_str, "%Y-%m-%d")

                # Skip if outside date range
                if (
                    day_date.date() < start_date.date()
                    or day_date.date() > end_date.date()
                ):
                    continue

                # Extract resilience level and convert to score
                resilience_level = item.get("level")
                if resilience_level is None:
                    continue

                # Get score from AppConfig mapping or use default of 0
                resilience_score = AppConfig.ANALYSIS_RESILIENCE_LEVEL_SCORES.get(
                    resilience_level.lower(), 0
                )

                # Add to data list
                resilience_data.append(
                    {
                        "date": date_str,
                        "resilience_score": round(resilience_score, 1),
                        "resilience_level": resilience_level.lower(),
                    }
                )
            except Exception as e:
                self.logger.logger.debug(f"Error processing Oura resilience data: {e}")
                continue

        # Create DataFrame if we have data
        if resilience_data:
            df = pd.DataFrame(resilience_data)

        return df

    def save_processed_data(self, data: dict[str, pd.DataFrame]) -> dict[str, str]:
        """Save processed Oura data to CSV files.

        Args:
            data: Dictionary of DataFrames with processed data

        Returns:
            Dictionary of paths to the saved files
        """
        from src.utils.file_utils import save_dataframe_to_file

        result = {}

        # Save activity data
        if "activity" in data and not data["activity"].empty:
            activity_path = save_dataframe_to_file(
                data["activity"], name="oura-activity-data", subdir="processing"
            )
            result["activity"] = activity_path

        # Save resilience data
        if "resilience" in data and not data["resilience"].empty:
            resilience_path = save_dataframe_to_file(
                data["resilience"], name="oura-resilience-data", subdir="processing"
            )
            result["resilience"] = resilience_path

        return result
