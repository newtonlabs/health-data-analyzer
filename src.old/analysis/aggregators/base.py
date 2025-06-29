"""Base aggregator module for metrics aggregation."""

# Python 3.12 has built-in type annotations

import pandas as pd

from src.utils.logging_utils import HealthLogger


class BaseAggregator:
    """Base class for all aggregators.

    This class provides common functionality and utility methods
    that are shared across different aggregator implementations.
    """

    def __init__(self, processor):
        """Initialize the base aggregator.

        Args:
            processor: The processor instance that provides data
        """
        self.processor = processor
        self.logger = HealthLogger(__name__)

    def _format_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format date columns consistently.

        Args:
            df: DataFrame with date column

        Returns:
            DataFrame with formatted date columns
        """
        if df is None or len(df) == 0:
            return df

        if "date" in df.columns:
            # Add day of week as three-letter abbreviation
            if "day" not in df.columns:
                df["day"] = df["date"].dt.strftime("%a")

            # Format date as MM-DD
            df["date"] = df["date"].dt.strftime("%m-%d")

        return df

    def _round_numeric_columns(
        self, df: pd.DataFrame, columns: dict[str, int]
    ) -> pd.DataFrame:
        """Round numeric columns to specified precision.

        Args:
            df: DataFrame with numeric columns
            columns: Dictionary mapping column names to decimal places

        Returns:
            DataFrame with rounded numeric columns
        """
        if df is None or len(df) == 0:
            return df

        for col, precision in columns.items():
            if col in df.columns:
                df[col] = df[col].round(precision)

        return df
