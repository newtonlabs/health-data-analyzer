"""Nutrition record model for structured nutrition data."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..enums import DataSource


@dataclass
class NutritionRecord:
    """Structured nutrition data record with comprehensive micronutrient tracking."""
    date: date
    source: DataSource
    
    # Macronutrients (required)
    calories: int
    protein: float
    carbs: float
    fat: float
    
    # Additional macronutrients
    alcohol: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    
    # Vitamins
    vitamin_a: Optional[float] = None  # Vitamin A (micrograms)
    vitamin_c: Optional[float] = None  # Vitamin C (milligrams)
    vitamin_d: Optional[float] = None  # Vitamin D (International Units)
    vitamin_e: Optional[float] = None  # Vitamin E (milligrams)
    vitamin_k: Optional[float] = None  # Vitamin K (micrograms)
    
    # B Vitamins
    b1_thiamine: Optional[float] = None     # B1 Thiamine (milligrams)
    b2_riboflavin: Optional[float] = None   # B2 Riboflavin (milligrams)
    b3_niacin: Optional[float] = None       # B3 Niacin (milligrams)
    b6_pyridoxine: Optional[float] = None   # B6 Pyridoxine (milligrams)
    b12_cobalamin: Optional[float] = None   # B12 Cobalamin (micrograms)
    folate: Optional[float] = None          # Folate (micrograms)
    
    # Essential Minerals
    calcium: Optional[float] = None    # Calcium (milligrams)
    iron: Optional[float] = None       # Iron (milligrams)
    magnesium: Optional[float] = None  # Magnesium (milligrams)
    potassium: Optional[float] = None  # Potassium (milligrams)
    sodium: Optional[float] = None     # Sodium (milligrams)
    zinc: Optional[float] = None       # Zinc (milligrams)
    
    # Fat Breakdown
    cholesterol: Optional[float] = None        # Cholesterol (milligrams)
    saturated_fat: Optional[float] = None       # Saturated fat (grams)
    monounsaturated_fat: Optional[float] = None # Monounsaturated fat (grams)
    polyunsaturated_fat: Optional[float] = None # Polyunsaturated fat (grams)
    omega3: Optional[float] = None              # Omega-3 fatty acids (grams)
    omega6: Optional[float] = None              # Omega-6 fatty acids (grams)
    
    # Other Nutrients
    caffeine: Optional[float] = None   # Caffeine (milligrams)
    water: Optional[float] = None       # Water content (grams)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.source, str):
            self.source = DataSource(self.source)
