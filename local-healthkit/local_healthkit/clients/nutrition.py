"""Nutrition file client for reading CSV-based nutrition data."""

import os
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import pandas as pd


class NutritionClient:
    """Client for reading nutrition data from CSV files.
    
    This client handles file-based nutrition data reading, following the same
    architectural patterns as API clients but for local file access.
    """
    
    def __init__(self, data_dir: str = "data", filename: str = "dailysummary.csv"):
        """Initialize the nutrition client.
        
        Args:
            data_dir: Directory containing the nutrition CSV file
            filename: Name of the nutrition data CSV file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_dir = data_dir
        self.filename = filename
        self.data_file = self._get_file_path()
        
    def _get_file_path(self) -> Optional[str]:
        """Get the full path to the nutrition data file.
        
        Returns:
            Full path to the file if it exists, None otherwise
        """
        if os.path.exists(self.data_dir):
            file_path = os.path.join(self.data_dir, self.filename)
            if os.path.exists(file_path):
                return file_path
        return None
    
    def get_nutrition_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get nutrition data for the specified date range.
        
        Args:
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            List of nutrition records as dictionaries
            
        Raises:
            FileNotFoundError: If nutrition data file is not found
        """
        self.logger.info(f"Reading nutrition data from {self.data_file}")
        
        # Check if file exists
        if not self.data_file or not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Nutrition data file not found: {self.data_file}")

        try:
            # Load and process the CSV data
            df = self._load_and_process_csv()
            
            # Filter by date range if provided
            if start_date:
                df = df[df["date"] >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df["date"] <= pd.Timestamp(end_date)]
            
            # Convert DataFrame to list of dictionaries
            nutrition_records = []
            for _, row in df.iterrows():
                record = {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "calories": float(row["calories"]),
                    "protein": float(row["protein"]),
                    "carbs": float(row["carbs"]),
                    "fat": float(row["fat"]),
                    "alcohol": float(row["alcohol"])
                }
                nutrition_records.append(record)
            
            self.logger.info(f"Successfully loaded {len(nutrition_records)} nutrition records")
            return nutrition_records
            
        except Exception as e:
            self.logger.error(f"Error reading nutrition data: {e}")
            raise
    
    def _load_and_process_csv(self) -> pd.DataFrame:
        """Load and process nutrition data from CSV file.
        
        Returns:
            Processed DataFrame with nutrition data
        """
        # Load CSV with proper date parsing
        data = pd.read_csv(self.data_file, parse_dates=["Date"])

        # Create new columns with our naming convention
        data["calories"] = pd.to_numeric(data["Energy (kcal)"], errors="coerce")
        data["protein"] = pd.to_numeric(data["Protein (g)"], errors="coerce")
        data["carbs"] = pd.to_numeric(data["Carbs (g)"], errors="coerce")
        data["fat"] = pd.to_numeric(data["Fat (g)"], errors="coerce")
        data["alcohol"] = pd.to_numeric(data["Alcohol (g)"], errors="coerce")
        data["date"] = data["Date"]

        # Fill missing values with zeros
        numeric_cols = ["calories", "protein", "carbs", "fat", "alcohol"]
        for col in numeric_cols:
            data[col] = data[col].fillna(0)

        # Select and round relevant columns
        summary = data[
            ["date", "calories", "protein", "carbs", "fat", "alcohol"]
        ].copy()
        summary = summary.round(
            {"calories": 0, "protein": 1, "carbs": 1, "fat": 1, "alcohol": 1}
        )

        return summary
