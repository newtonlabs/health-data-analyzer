"""Nutrition service for reading nutrition data from CSV files."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import os

from src.utils.logging_utils import HealthLogger


class NutritionService:
    """Service for reading nutrition data from CSV files.
    
    This service reads directly from CSV files without unnecessary client abstraction.
    """
    
    def __init__(self, data_dir: str = "data", filename: str = "dailysummary.csv"):
        """Initialize the nutrition service.
        
        Args:
            data_dir: Directory containing the nutrition CSV file
            filename: Name of the nutrition data CSV file
        """
        self.logger = HealthLogger(self.__class__.__name__)
        self.data_file = os.path.join(data_dir, filename)
    
    def get_nutrition_data(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get nutrition data from CSV file for specified date range.
        
        Args:
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            Dictionary containing nutrition data in a format similar to API responses
        """
        try:
            self.logger.info(f"Loading nutrition data from {start_date.date()} to {end_date.date()}")
            
            # Load full CSV data directly to get all micronutrients
            if not self.data_file or not os.path.exists(self.data_file):
                raise FileNotFoundError(f"Nutrition data file not found: {self.data_file}")
            
            # Load full CSV with all columns
            df = pd.read_csv(self.data_file, parse_dates=["Date"])
            
            # Filter by date range
            if start_date:
                df = df[df["Date"] >= start_date]
            if end_date:
                df = df[df["Date"] <= end_date]
            
            if df.empty:
                self.logger.warning("No nutrition data found for specified date range")
                return {"data": []}
            
            # Convert DataFrame to list of dictionaries with all micronutrients
            records = []
            for _, row in df.iterrows():
                record = {
                    "date": row["Date"].strftime("%Y-%m-%d") if pd.notna(row["Date"]) else None,
                    "calories": int(row["Energy (kcal)"]) if pd.notna(row["Energy (kcal)"]) else 0,
                    "protein": float(row["Protein (g)"]) if pd.notna(row["Protein (g)"]) else 0.0,
                    "carbs": float(row["Carbs (g)"]) if pd.notna(row["Carbs (g)"]) else 0.0,
                    "fat": float(row["Fat (g)"]) if pd.notna(row["Fat (g)"]) else 0.0,
                    "alcohol": float(row["Alcohol (g)"]) if pd.notna(row["Alcohol (g)"]) else 0.0,
                    # Additional macronutrients
                    "fiber": float(row["Fiber (g)"]) if pd.notna(row["Fiber (g)"]) else None,
                    "sugar": float(row["Sugars (g)"]) if pd.notna(row["Sugars (g)"]) else None,
                    "sodium": float(row["Sodium (mg)"]) if pd.notna(row["Sodium (mg)"]) else None,
                    # Vitamins
                    "vitamin_a": float(row["Vitamin A (µg)"]) if pd.notna(row["Vitamin A (µg)"]) else None,
                    "vitamin_c": float(row["Vitamin C (mg)"]) if pd.notna(row["Vitamin C (mg)"]) else None,
                    "vitamin_d": float(row["Vitamin D (IU)"]) if pd.notna(row["Vitamin D (IU)"]) else None,
                    "vitamin_e": float(row["Vitamin E (mg)"]) if pd.notna(row["Vitamin E (mg)"]) else None,
                    "vitamin_k": float(row["Vitamin K (µg)"]) if pd.notna(row["Vitamin K (µg)"]) else None,
                    # B Vitamins
                    "b1_thiamine": float(row["B1 (Thiamine) (mg)"]) if pd.notna(row["B1 (Thiamine) (mg)"]) else None,
                    "b2_riboflavin": float(row["B2 (Riboflavin) (mg)"]) if pd.notna(row["B2 (Riboflavin) (mg)"]) else None,
                    "b3_niacin": float(row["B3 (Niacin) (mg)"]) if pd.notna(row["B3 (Niacin) (mg)"]) else None,
                    "b6_pyridoxine": float(row["B6 (Pyridoxine) (mg)"]) if pd.notna(row["B6 (Pyridoxine) (mg)"]) else None,
                    "b12_cobalamin": float(row["B12 (Cobalamin) (µg)"]) if pd.notna(row["B12 (Cobalamin) (µg)"]) else None,
                    "folate": float(row["Folate (µg)"]) if pd.notna(row["Folate (µg)"]) else None,
                    # Minerals
                    "calcium": float(row["Calcium (mg)"]) if pd.notna(row["Calcium (mg)"]) else None,
                    "iron": float(row["Iron (mg)"]) if pd.notna(row["Iron (mg)"]) else None,
                    "magnesium": float(row["Magnesium (mg)"]) if pd.notna(row["Magnesium (mg)"]) else None,
                    "potassium": float(row["Potassium (mg)"]) if pd.notna(row["Potassium (mg)"]) else None,
                    "zinc": float(row["Zinc (mg)"]) if pd.notna(row["Zinc (mg)"]) else None,
                    # Fat breakdown
                    "cholesterol": float(row["Cholesterol (mg)"]) if pd.notna(row["Cholesterol (mg)"]) else None,
                    "saturated_fat": float(row["Saturated (g)"]) if pd.notna(row["Saturated (g)"]) else None,
                    "monounsaturated_fat": float(row["Monounsaturated (g)"]) if pd.notna(row["Monounsaturated (g)"]) else None,
                    "polyunsaturated_fat": float(row["Polyunsaturated (g)"]) if pd.notna(row["Polyunsaturated (g)"]) else None,
                    "omega3": float(row["Omega-3 (g)"]) if pd.notna(row["Omega-3 (g)"]) else None,
                    "omega6": float(row["Omega-6 (g)"]) if pd.notna(row["Omega-6 (g)"]) else None,
                    # Other nutrients
                    "caffeine": float(row["Caffeine (mg)"]) if pd.notna(row["Caffeine (mg)"]) else None,
                    "water": float(row["Water (g)"]) if pd.notna(row["Water (g)"]) else None
                }
                records.append(record)
            
            self.logger.info(f"Loaded {len(records)} nutrition records")
            
            # Return in API-like format
            return {
                "data": records,
                "count": len(records),
                "source": "csv_file"
            }
            
        except FileNotFoundError as e:
            self.logger.error(f"Nutrition file not found: {e}")
            return {"data": [], "error": str(e)}
        except Exception as e:
            self.logger.error(f"Error loading nutrition data: {e}")
            return {"data": [], "error": str(e)}
    
    def is_authenticated(self) -> bool:
        """Check if nutrition data source is available.
        
        For file-based sources, this checks if the file exists and is readable.
        
        Returns:
            True if nutrition file exists and is readable, False otherwise
        """
        try:
            return self.data_file is not None and os.path.exists(self.data_file)
        except Exception:
            return False
