"""Module for handling nutrition data from CSV file."""
import os
import pandas as pd
from src.data_sources.base import DataSource

class NutritionData(DataSource):
    def __init__(self, data_dir: str = 'data'):
        """Initialize NutritionData.
        
        Args:
            data_dir: Directory containing the dailysummary.csv file
        """
        super().__init__(data_dir)
        self.data_file = self.get_file_path('dailysummary.csv')
    
    def load_data(self) -> pd.DataFrame:
        """Load all nutrition data from CSV file.
        
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
        data = pd.read_csv(self.data_file, parse_dates=['Date'])
        
        # Create new columns with our naming convention
        data['calories'] = pd.to_numeric(data['Energy (kcal)'], errors='coerce')
        data['protein'] = pd.to_numeric(data['Protein (g)'], errors='coerce')
        data['carbs'] = pd.to_numeric(data['Carbs (g)'], errors='coerce')
        data['fat'] = pd.to_numeric(data['Fat (g)'], errors='coerce')
        data['date'] = data['Date']
        
        # Fill missing values with zeros
        numeric_cols = ['calories', 'protein', 'carbs', 'fat']
        for col in numeric_cols:
            data[col] = data[col].fillna(0)
        
        # Select and round relevant columns
        summary = data[['date', 'calories', 'protein', 'carbs', 'fat']].copy()
        summary = summary.round({
            'calories': 0,
            'protein': 1,
            'carbs': 1,
            'fat': 1
        })
        
        return summary
