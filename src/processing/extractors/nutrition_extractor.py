"""Nutrition data extractor for converting CSV data to structured records."""

from datetime import datetime, date
from typing import Dict, Any, List

from .base_extractor import BaseExtractor
from src.models.raw_data import NutritionRecord
from src.models.enums import DataSource


class NutritionExtractor(BaseExtractor):
    """Extractor for nutrition data from CSV files.
    
    This extractor handles the conversion of CSV-based nutrition data into
    structured NutritionRecord objects using the same pattern as API extractors.
    """
    
    def __init__(self):
        """Initialize the nutrition extractor."""
        super().__init__(DataSource.NUTRITION_FILE)
    
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract nutrition records from CSV data.
        
        This is pure extraction - converts raw CSV data to basic NutritionRecord models
        without any business logic or date calculations.
        
        Args:
            raw_data: Raw nutrition data from CSV service
            
        Returns:
            Dictionary containing nutrition records
        """
        if not raw_data or "data" not in raw_data:
            self.logger.warning("No nutrition data found in response")
            return {}
        
        nutrition_records = []
        
        # Direct conversion from raw data to NutritionRecord objects
        for record in raw_data["data"]:
            try:
                # Parse date
                record_date_str = record.get("date")
                if not record_date_str:
                    continue
                
                record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()
                
                # Create NutritionRecord (pure extraction - no cleaning)
                nutrition_record = NutritionRecord(
                    date=record_date,
                    source=DataSource.NUTRITION_FILE,
                    calories=record.get("calories", 0),
                    protein=record.get("protein", 0.0),
                    carbs=record.get("carbs", 0.0),
                    fat=record.get("fat", 0.0),
                    alcohol=record.get("alcohol"),
                    fiber=record.get("fiber"),
                    sugar=record.get("sugar"),
                    # Vitamins
                    vitamin_a=record.get("vitamin_a"),
                    vitamin_c=record.get("vitamin_c"),
                    vitamin_d=record.get("vitamin_d"),
                    vitamin_e=record.get("vitamin_e"),
                    vitamin_k=record.get("vitamin_k"),
                    # B Vitamins
                    b1_thiamine=record.get("b1_thiamine"),
                    b2_riboflavin=record.get("b2_riboflavin"),
                    b3_niacin=record.get("b3_niacin"),
                    b6_pyridoxine=record.get("b6_pyridoxine"),
                    b12_cobalamin=record.get("b12_cobalamin"),
                    folate=record.get("folate"),
                    # Essential Minerals
                    calcium=record.get("calcium"),
                    iron=record.get("iron"),
                    magnesium=record.get("magnesium"),
                    potassium=record.get("potassium"),
                    sodium=record.get("sodium"),
                    zinc=record.get("zinc"),
                    # Fat Breakdown
                    cholesterol=record.get("cholesterol"),
                    saturated_fat=record.get("saturated_fat"),
                    monounsaturated_fat=record.get("monounsaturated_fat"),
                    polyunsaturated_fat=record.get("polyunsaturated_fat"),
                    omega3=record.get("omega3"),
                    omega6=record.get("omega6"),
                    # Other Nutrients
                    caffeine=record.get("caffeine"),
                    water=record.get("water")
                )
                
                nutrition_records.append(nutrition_record)
                
            except Exception as e:
                self.logger.warning(f"Error creating NutritionRecord from data: {e}")
                continue
        
        self.logger.info(f"Extracted {len(nutrition_records)} raw nutrition records")
        
        # Return dictionary format like other extractors
        extracted_data = {}
        if nutrition_records:
            extracted_data['nutrition'] = nutrition_records
        
        return extracted_data
