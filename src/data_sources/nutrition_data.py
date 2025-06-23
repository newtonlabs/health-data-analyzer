"""Module for handling nutrition data from CSV file."""

import os
from datetime import datetime
from typing import Optional

import pandas as pd

from src.data_sources.base import DataSource


class NutritionData(DataSource):
    def __init__(self, data_dir: str = "data", filename: str = "dailysummary.csv"):
        """Initialize NutritionData.

        Args:
            data_dir: Directory containing the dailysummary.csv file
            filename: Name of the nutrition data CSV file
        """
        super().__init__(data_dir)
        self.data_file = self.get_file_path(filename)

    def load_data(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Load nutrition data from CSV file for a specified date range.

        Args:
            start_date: Optional start date for data range
            end_date: Optional end date for data range

        Returns:
            DataFrame with daily nutrition data including:
            - date: Date of the summary
            - calories: Total calories consumed
            - protein: Protein in grams
            - carbs: Carbohydrates in grams
            - fat: Fat in grams

        Raises:
            FileNotFoundError: If nutrition data file is not found
        """
        # Check if file exists
        if not self.data_file or not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Nutrition data file not found: {self.data_file}")

        # Load CSV with proper date parsing
        data = pd.read_csv(self.data_file, parse_dates=["Date"])

        # Create new columns with our naming convention
        data["calories"] = pd.to_numeric(data["Energy (kcal)"], errors="coerce")
        data["protein"] = pd.to_numeric(data["Protein (g)"], errors="coerce")
        data["carbs"] = pd.to_numeric(data["Carbs (g)"], errors="coerce")
        data["fat"] = pd.to_numeric(data["Fat (g)"], errors="coerce")
        data["date"] = data["Date"]

        # Fill missing values with zeros
        numeric_cols = ["calories", "protein", "carbs", "fat"]
        for col in numeric_cols:
            data[col] = data[col].fillna(0)

        # Select and round relevant columns
        summary = data[["date", "calories", "protein", "carbs", "fat"]].copy()
        summary = summary.round({"calories": 0, "protein": 1, "carbs": 1, "fat": 1})

        # Filter by date range if provided
        if start_date:
            summary = summary[summary["date"] >= start_date]
        if end_date:
            summary = summary[summary["date"] <= end_date]

        return summary
    
    def save_processed_data(self, df: pd.DataFrame, date: datetime = None) -> str:
        """Save processed nutrition data to a CSV file.
        
        Args:
            df: DataFrame with nutrition data
            date: Date to use in filename (default: current date)
            
        Returns:
            Path to the saved file
        """
        from src.utils.file_utils import save_dataframe_to_file
        
        # Use current date if not provided
        if date is None:
            date = datetime.now()
        
        # Save nutrition dataframe
        file_path = save_dataframe_to_file(
            df,
            name="nutrition-data",
            subdir="processing",
            date=date
        )
        
        return file_path
