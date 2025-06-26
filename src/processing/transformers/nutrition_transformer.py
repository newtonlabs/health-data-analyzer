"""Nutrition data transformer for cleaning and normalizing nutrition records."""

from typing import List, Optional
from datetime import date

from src.processing.transformers.base_transformer import RecordListTransformer
from src.models.data_records import NutritionRecord
from src.models.enums import DataSource


class NutritionTransformer(RecordListTransformer[NutritionRecord]):
    """Transformer for cleaning and normalizing nutrition records.
    
    This transformer handles NutritionRecord objects from any source (CSV files, etc.)
    and focuses on data type-specific cleaning rather than source-specific logic.
    
    This transformer handles:
    - Basic data validation
    - Data normalization and standardization
    - Nutrition metrics cleaning
    """
    
    def __init__(self):
        """Initialize the Nutrition transformer."""
        super().__init__()
        
        # Validation thresholds for reasonable nutrition values
        self.min_calories = 0
        self.max_calories = 10000  # Maximum reasonable daily calories
        self.min_macros = 0.0
        self.max_protein = 500.0  # Maximum reasonable daily protein
        self.max_carbs = 1000.0   # Maximum reasonable daily carbs
        self.max_fat = 500.0      # Maximum reasonable daily fat
    
    def transform_record(self, record: NutritionRecord) -> Optional[NutritionRecord]:
        """Transform a single nutrition record.
        
        Args:
            record: Raw nutrition record from extractor
            
        Returns:
            Cleaned and normalized nutrition record, or None if invalid
        """
        if not self.validate_record(record):
            self.logger.warning(f"Invalid nutrition record filtered out: {record.date}")
            return None
        
        # Create a cleaned copy of the record
        cleaned_record = NutritionRecord(
            date=record.date,
            source=record.source,
            calories=self._normalize_calories(record.calories),
            protein=self._normalize_macronutrient(record.protein, self.max_protein),
            carbs=self._normalize_macronutrient(record.carbs, self.max_carbs),
            fat=self._normalize_macronutrient(record.fat, self.max_fat),
            alcohol=self._normalize_optional_nutrient(record.alcohol),
            fiber=self._normalize_optional_nutrient(record.fiber),
            sugar=self._normalize_optional_nutrient(record.sugar),
            # Vitamins
            vitamin_a=self._normalize_optional_nutrient(record.vitamin_a),
            vitamin_c=self._normalize_optional_nutrient(record.vitamin_c),
            vitamin_d=self._normalize_optional_nutrient(record.vitamin_d),
            vitamin_e=self._normalize_optional_nutrient(record.vitamin_e),
            vitamin_k=self._normalize_optional_nutrient(record.vitamin_k),
            # B Vitamins
            b1_thiamine=self._normalize_optional_nutrient(record.b1_thiamine),
            b2_riboflavin=self._normalize_optional_nutrient(record.b2_riboflavin),
            b3_niacin=self._normalize_optional_nutrient(record.b3_niacin),
            b6_pyridoxine=self._normalize_optional_nutrient(record.b6_pyridoxine),
            b12_cobalamin=self._normalize_optional_nutrient(record.b12_cobalamin),
            folate=self._normalize_optional_nutrient(record.folate),
            # Essential Minerals
            calcium=self._normalize_optional_nutrient(record.calcium),
            iron=self._normalize_optional_nutrient(record.iron),
            magnesium=self._normalize_optional_nutrient(record.magnesium),
            potassium=self._normalize_optional_nutrient(record.potassium),
            sodium=self._normalize_optional_nutrient(record.sodium),
            zinc=self._normalize_optional_nutrient(record.zinc),
            # Fat Breakdown
            cholesterol=self._normalize_optional_nutrient(record.cholesterol),
            saturated_fat=self._normalize_optional_nutrient(record.saturated_fat),
            monounsaturated_fat=self._normalize_optional_nutrient(record.monounsaturated_fat),
            polyunsaturated_fat=self._normalize_optional_nutrient(record.polyunsaturated_fat),
            omega3=self._normalize_optional_nutrient(record.omega3),
            omega6=self._normalize_optional_nutrient(record.omega6),
            # Other Nutrients
            caffeine=self._normalize_optional_nutrient(record.caffeine),
            water=self._normalize_optional_nutrient(record.water),
            # Context
            meal_count=self._normalize_meal_count(record.meal_count)
        )
        
        self.logger.debug(f"Transformed nutrition record: {cleaned_record.date}")
        return cleaned_record
    
    def validate_record(self, record: NutritionRecord) -> bool:
        """Validate a nutrition record for basic requirements.
        
        Args:
            record: Nutrition record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        # Check essential fields
        if not record.date:
            return False
        
        # Check source
        if record.source != DataSource.NUTRITION_FILE:
            return False
        
        # Must have at least calories data
        if record.calories is None or record.calories < 0:
            return False
        
        # Basic sanity checks for macronutrients
        if record.calories > self.max_calories:
            self.logger.warning(f"Calories {record.calories} exceeds maximum {self.max_calories}")
            return False
        
        return True
    
    def filter_record(self, record: NutritionRecord) -> bool:
        """Determine if a record should be kept after transformation.
        
        Args:
            record: Transformed nutrition record
            
        Returns:
            True if record should be kept, False to filter out
        """
        # Keep all valid transformed records
        return record is not None
    
    def _normalize_calories(self, calories: int) -> int:
        """Normalize calorie values.
        
        Args:
            calories: Raw calorie value
            
        Returns:
            Normalized calories as integer
        """
        if calories is None:
            return 0
        
        # Ensure it's an integer and within reasonable range
        normalized_calories = int(calories)
        if normalized_calories < 0:
            self.logger.warning(f"Negative calories value: {normalized_calories}")
            return 0
        
        if normalized_calories > self.max_calories:
            self.logger.warning(f"Calories {normalized_calories} exceeds maximum {self.max_calories}")
            return self.max_calories
        
        return normalized_calories
    
    def _normalize_macronutrient(self, value: float, max_value: float) -> float:
        """Normalize macronutrient values (protein, carbs, fat).
        
        Args:
            value: Raw macronutrient value
            max_value: Maximum reasonable value for this macronutrient
            
        Returns:
            Normalized macronutrient value, rounded to 1 decimal place
        """
        if value is None:
            return 0.0
        
        # Round to 1 decimal place and ensure non-negative
        normalized_value = round(float(value), 1)
        if normalized_value < 0:
            self.logger.warning(f"Negative macronutrient value: {normalized_value}")
            return 0.0
        
        if normalized_value > max_value:
            self.logger.warning(f"Macronutrient {normalized_value} exceeds maximum {max_value}")
            return max_value
        
        return normalized_value
    
    def _normalize_optional_nutrient(self, value: Optional[float]) -> Optional[float]:
        """Normalize optional nutrient values (fiber, sugar, sodium).
        
        Args:
            value: Raw nutrient value
            
        Returns:
            Normalized nutrient value, rounded to 1 decimal place, or None
        """
        if value is None:
            return None
        
        # Round to 1 decimal place and ensure non-negative
        normalized_value = round(float(value), 1)
        if normalized_value < 0:
            self.logger.warning(f"Negative nutrient value: {normalized_value}")
            return 0.0
        
        return normalized_value
    
    def _normalize_meal_count(self, meal_count: Optional[int]) -> Optional[int]:
        """Normalize meal count values.
        
        Args:
            meal_count: Raw meal count
            
        Returns:
            Normalized meal count as integer, or None
        """
        if meal_count is None:
            return None
        
        # Ensure it's an integer and within reasonable range (1-10 meals per day)
        normalized_count = int(meal_count)
        if normalized_count < 1:
            self.logger.warning(f"Meal count {normalized_count} below minimum 1")
            return 1
        
        if normalized_count > 10:
            self.logger.warning(f"Meal count {normalized_count} exceeds maximum 10")
            return 10
        
        return normalized_count
