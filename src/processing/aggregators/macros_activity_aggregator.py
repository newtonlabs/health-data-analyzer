"""Macros and Activity aggregator for combining nutrition and activity data."""

from datetime import date
from typing import List, Optional

from src.models.raw_data import NutritionRecord, ActivityRecord, WeightRecord
from src.models.aggregations import MacrosAndActivityRecord


class MacrosActivityAggregator:
    """Aggregator for combining nutrition, activity, and weight data into daily summaries."""
    
    def aggregate_daily_data(
        self,
        target_date: date,
        nutrition_records: List[NutritionRecord],
        activity_records: List[ActivityRecord], 
        weight_records: List[WeightRecord]
    ) -> MacrosAndActivityRecord:
        """Aggregate daily nutrition, activity, and weight data.
        
        Args:
            target_date: Date to aggregate data for
            nutrition_records: Nutrition data for the date
            activity_records: Activity data for the date
            weight_records: Weight measurements for the date
            
        Returns:
            Aggregated daily macros and activity record
        """
        # Find records for target date
        nutrition = self._find_nutrition_for_date(nutrition_records, target_date)
        activity = self._find_activity_for_date(activity_records, target_date)
        weight = self._find_weight_for_date(weight_records, target_date)
        
        return MacrosAndActivityRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            # Nutrition metrics
            calories=nutrition.calories if nutrition else None,
            protein=nutrition.protein if nutrition else None,
            carbs=nutrition.carbs if nutrition else None,
            fat=nutrition.fat if nutrition else None,
            alcohol=nutrition.alcohol if nutrition else None,
            # Activity metrics
            activity=activity.total_calories if activity else None,  # Using total_calories as activity score
            steps=activity.steps if activity else None,
            # Weight metrics
            weight=weight.weight_kg if weight else None,
        )
    
    def _find_nutrition_for_date(self, records: List[NutritionRecord], target_date: date) -> Optional[NutritionRecord]:
        """Find nutrition record for specific date."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    def _find_activity_for_date(self, records: List[ActivityRecord], target_date: date) -> Optional[ActivityRecord]:
        """Find activity record for specific date."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    def _find_weight_for_date(self, records: List[WeightRecord], target_date: date) -> Optional[WeightRecord]:
        """Find weight record for specific date (closest to date)."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    

