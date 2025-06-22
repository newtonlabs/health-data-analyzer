"""Utility functions for file operations."""

import json
import os
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from src.utils.date_utils import DateFormat, DateUtils


def save_dataframe_to_file(
    df: pd.DataFrame,
    name: str,
    subdir: str,
    filename: Optional[str] = None,
    data_dir: str = "data",
    date: Optional[datetime] = None,
) -> str:
    """Save a DataFrame to a file in a subdirectory of the data directory.

    Args:
        df: DataFrame to save
        name: Name of the DataFrame (used in filename if filename not provided)
        subdir: Subdirectory within data_dir (required, e.g., "processing", "aggregations")
        filename: Optional filename override (without extension)
        data_dir: Base directory to save the file in (default: "data")
        date: Optional date to use in the filename (default: yesterday)

    Returns:
        Path to the saved file
    """
    if df is None or df.empty:
        raise ValueError(f"Cannot save empty DataFrame: {name}")

    # Create data directory and subdirectory if they don't exist
    full_dir = os.path.join(data_dir, subdir)
    os.makedirs(full_dir, exist_ok=True)

    # Get yesterday's date if not provided
    if date is None:
        _, report_end, _, _ = DateUtils.get_date_ranges()
        date = report_end

    # Format the date as YYYY-MM-DD
    date_str = date.strftime(DateFormat.STANDARD)

    # Generate filename if not provided
    if filename is None:
        filename = f"{date_str}-{name.lower().replace(' ', '-')}"

    # Add .csv extension if not present
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"

    # Full path to the file
    file_path = os.path.join(full_dir, filename)

    # Save DataFrame to CSV
    df.to_csv(file_path, index=False)

    return file_path


def save_json_to_file(
    data: dict[str, Any],
    name: str,
    subdir: str = "json",
    filename: Optional[str] = None,
    data_dir: str = "data",
    date: Optional[datetime] = None,
    indent: int = 2,
) -> str:
    """Save JSON data to a file in a subdirectory of the data directory.

    Args:
        data: Dictionary to save as JSON
        name: Name of the data (used in filename if filename not provided)
        subdir: Subdirectory within data_dir (default: "json")
        filename: Optional filename override (without extension)
        data_dir: Base directory to save the file in (default: "data")
        date: Optional date to use in the filename (default: yesterday)
        indent: Number of spaces for JSON indentation (default: 2)

    Returns:
        Path to the saved file
    """
    if data is None:
        raise ValueError(f"Cannot save empty data: {name}")

    # Create data directory and subdirectory if they don't exist
    full_dir = os.path.join(data_dir, subdir)
    os.makedirs(full_dir, exist_ok=True)

    # Get yesterday's date if not provided
    if date is None:
        _, report_end, _, _ = DateUtils.get_date_ranges()
        date = report_end

    # Format the date as YYYY-MM-DD
    date_str = date.strftime(DateFormat.STANDARD)

    # Generate filename if not provided
    if filename is None:
        filename = f"{date_str}-{name.lower().replace(' ', '-')}"

    # Add .json extension if not present
    if not filename.endswith(".json"):
        filename = f"{filename}.json"

    # Full path to the file
    file_path = os.path.join(full_dir, filename)

    # Save data to JSON file
    with open(file_path, "w") as f:
        json.dump(data, f, indent=indent)

    return file_path
