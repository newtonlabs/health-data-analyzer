"""Base class for data sources."""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from src.utils.date_utils import DateFormat, DateUtils


class DataSource(ABC):
    def __init__(self, data_dir: str = "data"):
        """Initialize data source.

        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def get_file_path(self, filename: str) -> str:
        """Get full path for a file."""
        return os.path.join(self.data_dir, filename)

    def get_dated_file_path(self, base_name: str, date: datetime) -> str:
        """Get path for a dated file."""
        return self.get_file_path(
            f"{DateUtils.format_date(date, DateFormat.STANDARD)}-{base_name}"
        )

    @abstractmethod
    def load_data(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Load data for the specified date range.

        Args:
            start_date: Start date for data range
            end_date: End date for data range

        Returns:
            DataFrame with data for the specified range
        """
        pass
