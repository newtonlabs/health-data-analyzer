"""Recovery aggregator module for metrics aggregation."""

from datetime import datetime

import pandas as pd

from src.utils.date_utils import DateUtils
from src.utils.file_utils import save_dataframe_to_file

from .base import BaseAggregator

# Python 3.12 has built-in type annotations


class RecoveryAggregator(BaseAggregator):
    """Aggregator for recovery metrics.

    Combines recovery data from Whoop and resilience data from Oura
    into a single DataFrame for reporting and visualization.
    """

    def get_recovery_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get recovery metrics for date range.

        Steps:
        1. Create base DataFrame with date range
        2. Get recovery data for date range
        3. Get resilience data from Oura
        4. Format recovery and resilience data into lookups
        5. Update base DataFrame with metrics

        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with columns:
            - date: Date of the metrics (MM-DD)
            - day: Three letter day name
            - recovery: Recovery score (0-100)
            - resilience_level: Resilience level from Oura (text)
            - hrv: Heart rate variability in ms
            - hr: Resting heart rate in bpm
            - sleep_need: Hours of sleep needed
            - sleep_actual: Actual hours of sleep
        """
        # Step 1: Create base DataFrame
        df = DateUtils.create_date_range_df(start_date, end_date)

        # Step 2: Get recovery data
        recovery_df = self._get_filtered_recovery_data(start_date, end_date)

        # Step 3: Get resilience data
        resilience_df = self._get_filtered_resilience_data(start_date, end_date)

        # Step 4: Format data into lookups
        recovery_by_date = {}
        if not recovery_df.empty:
            recovery_by_date = self._format_recovery_data(recovery_df)

        resilience_by_date = {}
        if not resilience_df.empty:
            resilience_by_date = self._format_resilience_data(resilience_df)

        # Step 5: Update metrics
        df = self._update_recovery_metrics(df, recovery_by_date)

        # Add resilience level data if available (only include level, not score)
        if resilience_by_date:
            df["resilience_level"] = df["date"].map(
                lambda x: resilience_by_date.get(x, {}).get("resilience_level")
            )

        # Save the final DataFrame to a file
        save_dataframe_to_file(df, "recovery-metrics", subdir="aggregations")

        return df

    def _get_filtered_recovery_data(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get recovery data filtered to date range.

        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with filtered recovery data
        """
        if (
            self.processor.whoop_data is None
            or "recovery" not in self.processor.whoop_data
        ):
            return pd.DataFrame()

        df = self.processor.whoop_data["recovery"][
            (self.processor.whoop_data["recovery"]["date"].dt.date >= start_date.date())
            & (self.processor.whoop_data["recovery"]["date"].dt.date <= end_date.date())
        ].copy()

        return df

    def _format_recovery_data(self, recovery_df: pd.DataFrame) -> dict:
        """Format recovery data into lookup by date.

        Args:
            recovery_df: DataFrame with recovery data

        Returns:
            Dictionary mapping dates to recovery metrics
        """
        recovery_df["date"] = recovery_df["date"].dt.strftime("%m-%d")

        recovery_by_date = {}
        for _, row in recovery_df.iterrows():
            recovery_by_date[row["date"]] = {
                "recovery": row["recovery_score"],
                "hrv": row["hrv_rmssd"],
                "hr": row["resting_hr"],
                "sleep_need": row["sleep_need"],
                "sleep_actual": row["sleep_actual"],
            }

        return recovery_by_date

    def _update_recovery_metrics(
        self, df: pd.DataFrame, recovery_by_date: dict
    ) -> pd.DataFrame:
        """Update DataFrame with recovery metrics.

        Args:
            df: DataFrame to update
            recovery_by_date: Dictionary mapping dates to recovery metrics

        Returns:
            Updated DataFrame with recovery metrics
        """
        # Set default values
        df["recovery"] = "-"
        df["hrv"] = "-"
        df["hr"] = "-"
        df["sleep_need"] = "-"
        df["sleep_actual"] = "-"

        # Update with actual values
        for date in df["date"]:
            if date in recovery_by_date:
                df.loc[df["date"] == date, "recovery"] = recovery_by_date[date][
                    "recovery"
                ]
                df.loc[df["date"] == date, "hrv"] = recovery_by_date[date]["hrv"]
                df.loc[df["date"] == date, "hr"] = recovery_by_date[date]["hr"]
                df.loc[df["date"] == date, "sleep_need"] = recovery_by_date[date][
                    "sleep_need"
                ]
                df.loc[df["date"] == date, "sleep_actual"] = recovery_by_date[date][
                    "sleep_actual"
                ]

        # Format numeric values
        for col in ["recovery", "hrv", "hr"]:
            df[col] = df[col].apply(
                lambda x: round(float(x), 1) if not pd.isna(x) and x != "-" else None
            )

        # Format sleep values to 1 decimal place
        for col in ["sleep_need", "sleep_actual"]:
            df[col] = df[col].apply(
                lambda x: round(float(x), 1) if not pd.isna(x) and x != "-" else None
            )

        return df

    def _get_filtered_resilience_data(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get resilience data filtered to date range.

        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with filtered resilience data
        """
        if (
            self.processor.oura_data is None
            or "resilience" not in self.processor.oura_data
        ):
            return pd.DataFrame()

        # Convert date strings to datetime objects for proper comparison
        resilience_df = self.processor.oura_data["resilience"].copy()
        if not resilience_df.empty and "date" in resilience_df.columns:
            resilience_df["date_obj"] = pd.to_datetime(resilience_df["date"])
            filtered_df = resilience_df[
                (resilience_df["date_obj"].dt.date >= start_date.date())
                & (resilience_df["date_obj"].dt.date <= end_date.date())
            ].copy()
            filtered_df.drop("date_obj", axis=1, inplace=True)
            return filtered_df

        return pd.DataFrame()

    def _format_resilience_data(self, resilience_df: pd.DataFrame) -> dict:
        """Format resilience data into lookup by date.

        Args:
            resilience_df: DataFrame with resilience data

        Returns:
            Dictionary mapping dates to resilience metrics
        """
        resilience_by_date = {}
        for _, row in resilience_df.iterrows():
            date_key = row["date"]
            # Convert YYYY-MM-DD to MM-DD format
            if len(date_key) == 10:  # YYYY-MM-DD format
                date_key = date_key[5:]  # Extract MM-DD part
            resilience_by_date[date_key] = {
                "resilience_score": row["resilience_score"],
                "resilience_level": row["resilience_level"],
            }

        return resilience_by_date
