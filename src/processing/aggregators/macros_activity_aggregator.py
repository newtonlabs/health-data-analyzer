"""Macros and Activity aggregator for combining nutrition and activity data."""

import logging
from datetime import date
from typing import List, Optional

from src.models.raw_data import NutritionRecord, ActivityRecord, WeightRecord, WorkoutRecord
from src.models.aggregations import MacrosAndActivityRecord
from src.models.enums import SportType, DataSource


class MacrosActivityAggregator:
    """Aggregator for combining nutrition, activity, and weight data."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def aggregate_daily_data(
        self,
        target_date: date,
        nutrition_records: List[NutritionRecord],
        activity_records: List[ActivityRecord], 
        weight_records: List[WeightRecord],
        workout_records: List[WorkoutRecord] = None
    ) -> MacrosAndActivityRecord:
        """Aggregate daily nutrition, activity, and weight data.
        
        Args:
            target_date: Date to aggregate data for
            nutrition_records: Nutrition data for the date
            activity_records: Activity data for the date
            weight_records: Weight measurements for the date
            workout_records: Workout data for determining primary sport
            
        Returns:
            Aggregated daily macros and activity record
        """
        # Debug: Show what activity records we have
        self.logger.info(f"🔍 Activity records for {target_date}: {len(activity_records)} total")
        for i, record in enumerate(activity_records):  # Show all records
            self.logger.info(f"  Activity {i+1}: date={getattr(record, 'date', 'N/A')}, steps={getattr(record, 'steps', 'N/A')}, source={getattr(record, 'source', 'N/A')}")
        
        # Find records for target date
        nutrition = self._find_nutrition_for_date(nutrition_records, target_date)
        activity = self._find_activity_for_date(activity_records, target_date)
        weight = self._find_weight_for_date(weight_records, target_date)
        
        # Debug: Show what we found
        self.logger.info(f"🎯 Found for {target_date}: nutrition={'✅' if nutrition else '❌'}, activity={'✅' if activity else '❌'} (steps={getattr(activity, 'steps', 'N/A') if activity else 'N/A'}, source={getattr(activity, 'source', 'N/A') if activity else 'N/A'}), weight={'✅' if weight else '❌'}")
        
        # Debug logging for workout records
        self.logger.info(f"🔍 MacrosActivityAggregator for {target_date}: received {len(workout_records) if workout_records else 0} workout records")
        if workout_records:
            for i, w in enumerate(workout_records[:3]):  # Show first 3
                self.logger.info(f"  Workout {i+1}: date={getattr(w, 'date', 'N/A')}, source={getattr(w, 'source', 'N/A')}, sport_type={getattr(w, 'sport_type', 'N/A')}")
        
        # Determine primary sport for the day from workout records
        primary_sport = self._get_primary_sport(workout_records, target_date)
        self.logger.info(f"🎯 Primary sport determined for {target_date}: {primary_sport}")
        
        result = MacrosAndActivityRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            # Nutrition metrics
            calories=nutrition.calories if nutrition else None,
            protein=nutrition.protein if nutrition else None,
            carbs=nutrition.carbs if nutrition else None,
            fat=nutrition.fat if nutrition else None,
            alcohol=nutrition.alcohol if nutrition else None,
            # Activity metrics
            sport_type=primary_sport,  # Primary sport for the day
            steps=activity.steps if activity else None,
            # Weight metrics
            weight=weight.weight_kg if weight else None,
        )
        
        self.logger.info(f"✅ Successfully created record for {target_date} with sport_type={primary_sport}")
        return result
    
    def _find_nutrition_for_date(self, records: List[NutritionRecord], target_date: date) -> Optional[NutritionRecord]:
        """Find nutrition record for specific date."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    def _find_activity_for_date(self, records: List[ActivityRecord], target_date: date) -> Optional[ActivityRecord]:
        """Find activity record for specific date, prioritizing Oura over Whoop."""
        matching_records = [record for record in records if record.date == target_date]
        
        if not matching_records:
            return None
            
        # Always prefer Oura data over Whoop data
        oura_records = [record for record in matching_records if record.source == DataSource.OURA]
        if oura_records:
            return oura_records[0]  # Return first Oura record
            
        # Fallback to any matching record if no Oura data
        return matching_records[0]
    
    def _find_weight_for_date(self, records: List[WeightRecord], target_date: date) -> Optional[WeightRecord]:
        """Find weight record for specific date (closest to date)."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    def _get_primary_sport(self, workout_records: List[WorkoutRecord], target_date: date) -> Optional[SportType]:
        """Get primary sport for the day using prioritization logic.
        
        Priority order:
        1. Strength training (highest duration)
        2. Cardio
        3. Rest
        
        Args:
            workout_records: List of workout records
            target_date: Date to find workouts for
            
        Returns:
            Primary sport type for the day or None for rest day
        """
        if not workout_records:
            self.logger.debug(f"No workout records provided for {target_date}")
            return SportType.REST
            
        # Debug: Show first few workout records to understand the data structure
        if workout_records:
            self.logger.info(f"Sample workout records for debugging:")
            for i, w in enumerate(workout_records[:3]):
                self.logger.info(f"  Record {i}: date={getattr(w, 'date', 'N/A')} (type: {type(getattr(w, 'date', None))}), source={getattr(w, 'source', 'N/A')}, sport_type={getattr(w, 'sport_type', 'N/A')}")
        
        # Find workouts for target date - filter for Whoop workouts only
        self.logger.info(f"Target date: {target_date} (type: {type(target_date)})")
        all_daily_workouts = [w for w in workout_records if w.date == target_date]
        self.logger.info(f"After date filtering: {len(all_daily_workouts)} workouts for {target_date}")
        
        daily_workouts = [
            w for w in all_daily_workouts 
            if hasattr(w, 'source') and 'whoop' in str(w.source).lower()
        ]
        
        self.logger.info(f"Sport filtering for {target_date}: {len(all_daily_workouts)} total workouts, {len(daily_workouts)} Whoop workouts")
        if all_daily_workouts:
            sources = [str(getattr(w, 'source', 'N/A')) for w in all_daily_workouts]
            self.logger.info(f"  All workout sources: {sources}")
        
        if not daily_workouts:
            self.logger.info(f"No Whoop workouts found for {target_date}")
            return SportType.REST
        
        # Sort by duration (longest first)
        sorted_workouts = sorted(daily_workouts, key=lambda x: x.duration_minutes or 0, reverse=True)
        
        # Priority 1: If any strength training, return strength training
        strength_workouts = [
            w for w in sorted_workouts 
            if w.sport_type == SportType.STRENGTH_TRAINING
        ]
        
        if strength_workouts:
            return SportType.STRENGTH_TRAINING
        
        # Priority 2: If cardio but no strength training, return cardio
        cardio_workouts = [
            w for w in sorted_workouts 
            if w.sport_type == SportType.CARDIO
        ]
        
        if cardio_workouts:
            return SportType.CARDIO
        
        # Priority 3: Otherwise return rest
        return SportType.REST
