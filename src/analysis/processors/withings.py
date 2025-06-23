"""Processor for Withings data.

This module provides functionality to process and analyze data from the Withings API.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import pytz

from src.app_config import AppConfig


class WithingsProcessor:
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
            DataFrame with processed weight data
        """
        # Import and define timezone early to avoid NameError
        local_tz = pytz.timezone("America/New_York")

        # Extract weight data
        weight_records = []

        if "measuregrps" in weight_data:
            # Process each measurement group from the Withings API
            measuregrps = weight_data.get("measuregrps", [])

            for group in measuregrps:
                timestamp = group.get("date")
                if not timestamp:
                    continue

                # Convert timestamp from UTC to local time
                dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                dt_local = dt_utc.astimezone(local_tz)

                # Skip if outside date range
                if start_date and dt_local.date() < start_date.date():
                    continue
                if end_date and dt_local.date() > end_date.date():
                    continue

                # Process weight measurements (type 1)
                for measure in group.get("measures", []):
                    if measure.get("type") == 1:
                        # Convert value using unit multiplier (e.g., -3 means ×10^-3)
                        value = measure.get("value", 0) * (10 ** measure.get("unit", 0))
                        weight_records.append(
                            {
                                "date": dt_local.date(),
                                "weight": value,
                                "timestamp": timestamp,
                            }
                        )

        # Create DataFrame
        if not weight_records:
            return pd.DataFrame(columns=["date", "day", "weight"])

        # Create DataFrame with both date and timestamp
        df = pd.DataFrame(weight_records, columns=["date", "weight", "timestamp"])

        # Sort by timestamp so the latest measurement per day is always kept
        df_sorted = df.sort_values("timestamp")
        df_latest = df_sorted.groupby("date", as_index=True).last()

        # Build full 7-day index (yesterday to 6 days prior) to ensure all days are included
        today = datetime.now(local_tz).date()
        yesterday = today - timedelta(days=1)
        week_start = yesterday - timedelta(days=6)
        full_index = [week_start + timedelta(days=i) for i in range(7)]

        # Reindex to include all days in the reporting window
        df_latest = df_latest.reindex(full_index)

        # Format date as MM-DD to match other DataFrames
        df_latest["date"] = [
            d.strftime("%m-%d") if d is not None else "" for d in df_latest.index
        ]

        # Add day of week for better readability
        df_latest["day"] = [
            d.strftime("%a") if d is not None else "" for d in df_latest.index
        ]

        # Convert weight from kg to pounds and round to the configured precision
        KG_TO_LB = 2.20462
        weight_precision = AppConfig.ANALYSIS_NUMERIC_PRECISION.get("weight", 1)
        df_latest["weight"] = (df_latest["weight"] * KG_TO_LB).round(weight_precision)

        # Reorder columns for consistency with other DataFrames
        df_latest = df_latest[["date", "day", "weight"]]

        return df_latest

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
