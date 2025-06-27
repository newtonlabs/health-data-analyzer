"""Aggregation pipeline for creating daily health data summaries.

This pipeline takes transformed CSV data and creates aggregated daily summaries
using the specialized aggregation models and business logic classes.
"""

import os
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Optional

from src.models.raw_data import (
    WorkoutRecord, RecoveryRecord, SleepRecord, WeightRecord, 
    NutritionRecord, ActivityRecord, ResilienceRecord
)
from src.models.aggregations import (
    MacrosAndActivityRecord, RecoveryMetricsRecord, TrainingMetricsRecord
)
from src.processing.aggregators import (
    MacrosActivityAggregator, RecoveryAggregator, TrainingAggregator
)
from src.models.enums import DataSource
from src.utils.logging_utils import HealthLogger


class AggregationPipeline:
    """Pipeline for creating daily aggregated health data summaries."""
    
    def __init__(self):
        """Initialize the aggregation pipeline."""
        self.logger = HealthLogger("AggregationPipeline")
        self.macros_aggregator = MacrosActivityAggregator()
        self.recovery_aggregator = RecoveryAggregator()
        self.training_aggregator = TrainingAggregator()
    
    def run_daily_aggregations(self, target_date: date, data_dir: str = "data/03_transformed") -> dict:
        """Run all daily aggregations for a specific date.
        
        Args:
            target_date: Date to create aggregations for
            data_dir: Directory containing transformed CSV files
            
        Returns:
            Dictionary with aggregation results
        """
        self.logger.info(f"🔄 Starting daily aggregations for {target_date}")
        
        # Load all transformed data
        data = self._load_transformed_data(target_date, data_dir)
        
        # Create aggregations
        results = {}
        
        # Macros & Activity aggregation
        macros_activity = self._create_macros_activity_aggregation(target_date, data)
        if macros_activity:
            results['macros_activity'] = macros_activity
            self.logger.info(f"✅ Created macros & activity aggregation for {target_date}")
        
        # Recovery aggregation
        recovery_metrics = self._create_recovery_aggregation(target_date, data)
        if recovery_metrics:
            results['recovery_metrics'] = recovery_metrics
            self.logger.info(f"✅ Created recovery metrics aggregation for {target_date}")
        
        # Training aggregation
        training_metrics = self._create_training_aggregation(target_date, data)
        if training_metrics:
            results['training_metrics'] = training_metrics
            self.logger.info(f"✅ Created training metrics aggregation for {target_date}")
        
        # Save aggregations to CSV
        self._save_aggregations(target_date, results)
        
        self.logger.info(f"🎉 Completed daily aggregations for {target_date}: {len(results)} aggregations created")
        return results
    
    def run_daily_aggregations_with_data(self, start_date: date, end_date: date, transformed_data: dict) -> dict:
        """Run daily aggregations using in-memory transformed data for a date range.
        
        Creates consolidated aggregation files with one row per day, similar to transformation stage.
        
        Args:
            start_date: Start date for aggregation range
            end_date: End date for aggregation range  
            transformed_data: Dictionary containing transformed data from all services
            
        Returns:
            Dictionary containing aggregation results and file paths
        """
        self.logger.info(f"🔄 Starting daily aggregations for {start_date} to {end_date} (in-memory data)")
        
        # Collect aggregations for all days in range
        all_macros_activity = []
        all_recovery_metrics = []
        all_training_metrics = []
        
        # Generate date range
        current_date = start_date
        while current_date <= end_date:
            # Create aggregations for this date
            macros_activity = self._create_macros_activity_from_data(current_date, transformed_data)
            recovery_metrics = self._create_recovery_from_data(current_date, transformed_data)
            training_metrics = self._create_training_from_data(current_date, transformed_data)
            
            # Add to collections (even if None - we'll filter later)
            if macros_activity:
                all_macros_activity.append(macros_activity)
            if recovery_metrics:
                all_recovery_metrics.append(recovery_metrics)
            if training_metrics:
                all_training_metrics.append(training_metrics)
                
            current_date += timedelta(days=1)
        
        # Save consolidated aggregation files
        results = {}
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        if all_macros_activity:
            macros_file = self._save_consolidated_aggregation("macros_activity", all_macros_activity, timestamp)
            results['macros_activity_file'] = macros_file
            self.logger.info(f"✅ Saved {len(all_macros_activity)} macros_activity records to {macros_file}")
            
        if all_recovery_metrics:
            recovery_file = self._save_consolidated_aggregation("recovery_metrics", all_recovery_metrics, timestamp)
            results['recovery_metrics_file'] = recovery_file
            self.logger.info(f"✅ Saved {len(all_recovery_metrics)} recovery_metrics records to {recovery_file}")
            
        if all_training_metrics:
            training_file = self._save_consolidated_aggregation("training_metrics", all_training_metrics, timestamp)
            results['training_metrics_file'] = training_file
            self.logger.info(f"✅ Saved {len(all_training_metrics)} training_metrics records to {training_file}")
        
        # Return aggregation data for in-memory use
        results.update({
            'macros_activity_records': all_macros_activity,
            'recovery_metrics_records': all_recovery_metrics,
            'training_metrics_records': all_training_metrics,
            'total_days': len(set([r.date for r in all_macros_activity + all_recovery_metrics + all_training_metrics]))
        })
        
        self.logger.info(f"🎉 Daily aggregations completed: {len(all_macros_activity + all_recovery_metrics + all_training_metrics)} total records")
        return results
    
    def _load_transformed_data(self, target_date: date, data_dir: str) -> dict:
        """Load all transformed CSV data for the target date."""
        data = {}
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Define file patterns
        file_patterns = {
            'workouts': ['whoop_workouts_transformed', 'oura_workouts_transformed', 'hevy_workouts_transformed'],
            'recovery': ['whoop_recovery_transformed'],
            'sleep': ['whoop_sleep_transformed'],
            'weights': ['withings_weights_transformed'],
            'nutrition': ['nutrition_transformed'],  # Placeholder for future
            'activities': ['oura_activities_transformed'],
            'resilience': ['oura_resilience_transformed'],
            'exercises': ['hevy_exercises_transformed']
        }
        
        for data_type, patterns in file_patterns.items():
            data[data_type] = []
            for pattern in patterns:
                file_path = os.path.join(data_dir, f"{pattern}_{date_str}.csv")
                if os.path.exists(file_path):
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            data[data_type].extend(self._df_to_records(df, data_type))
                            self.logger.debug(f"📄 Loaded {len(df)} records from {pattern}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to load {file_path}: {e}")
        
        return data
    
    def _df_to_records(self, df: pd.DataFrame, data_type: str) -> List:
        """Convert DataFrame to appropriate record objects."""
        records = []
        
        for _, row in df.iterrows():
            try:
                if data_type == 'workouts':
                    # Convert to WorkoutRecord - placeholder implementation
                    record = self._row_to_workout_record(row)
                elif data_type == 'recovery':
                    record = self._row_to_recovery_record(row)
                elif data_type == 'sleep':
                    record = self._row_to_sleep_record(row)
                elif data_type == 'weights':
                    record = self._row_to_weight_record(row)
                elif data_type == 'activities':
                    record = self._row_to_activity_record(row)
                elif data_type == 'resilience':
                    record = self._row_to_resilience_record(row)
                else:
                    continue  # Skip unknown data types
                
                if record:
                    records.append(record)
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to convert row to {data_type} record: {e}")
        
        return records
    
    def _row_to_workout_record(self, row) -> Optional[WorkoutRecord]:
        """Convert CSV row to WorkoutRecord - placeholder implementation."""
        # TODO: Implement proper CSV to WorkoutRecord conversion
        return None
    
    def _row_to_recovery_record(self, row) -> Optional[RecoveryRecord]:
        """Convert CSV row to RecoveryRecord - placeholder implementation."""
        # TODO: Implement proper CSV to RecoveryRecord conversion
        return None
    
    def _row_to_sleep_record(self, row) -> Optional[SleepRecord]:
        """Convert CSV row to SleepRecord - placeholder implementation."""
        # TODO: Implement proper CSV to SleepRecord conversion
        return None
    
    def _row_to_weight_record(self, row) -> Optional[WeightRecord]:
        """Convert CSV row to WeightRecord - placeholder implementation."""
        # TODO: Implement proper CSV to WeightRecord conversion
        return None
    
    def _row_to_activity_record(self, row) -> Optional[ActivityRecord]:
        """Convert CSV row to ActivityRecord - placeholder implementation."""
        # TODO: Implement proper CSV to ActivityRecord conversion
        return None
    
    def _row_to_resilience_record(self, row) -> Optional[ResilienceRecord]:
        """Convert CSV row to ResilienceRecord - placeholder implementation."""
        # TODO: Implement proper CSV to ResilienceRecord conversion
        return None
    
    def _create_macros_activity_aggregation(self, target_date: date, data: dict) -> Optional[MacrosAndActivityRecord]:
        """Create macros and activity aggregation for the target date."""
        # Placeholder implementation
        return MacrosAndActivityRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            # TODO: Extract actual data from loaded records
            calories=None,
            protein=None,
            carbs=None,
            fat=None,
            alcohol=None,
            activity=None,
            steps=None,
            weight=None,
        )
    
    def _create_recovery_aggregation(self, target_date: date, data: dict) -> Optional[RecoveryMetricsRecord]:
        """Create recovery metrics aggregation for the target date."""
        # Placeholder implementation
        return RecoveryMetricsRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            # TODO: Extract actual data from loaded records
            recovery=None,
            hrv=None,
            hr=None,
            sleep_need=None,
            sleep_actual=None,
            resilience_level=None,
        )
    
    def _create_training_aggregation(self, target_date: date, data: dict) -> Optional[TrainingMetricsRecord]:
        """Create training metrics aggregation for the target date."""
        # Use the training aggregator with placeholder data
        return self.training_aggregator.aggregate_daily_training(target_date, data.get('workouts', []))
    
    def _create_macros_activity_from_data(self, target_date: date, transformed_data: dict) -> Optional[MacrosAndActivityRecord]:
        """Create macros and activity aggregation from in-memory data."""
        # Collect nutrition data from all services
        nutrition_records = []
        
        # Get nutrition records from all services
        for service, service_data in transformed_data.items():
            if 'nutrition_records' in service_data:
                nutrition_records.extend(service_data['nutrition_records'])
        
        # Get activity records
        activity_records = []
        for service, service_data in transformed_data.items():
            if 'activity_records' in service_data:
                activity_records.extend(service_data['activity_records'])
        
        # Get weight records
        weight_records = []
        for service, service_data in transformed_data.items():
            if 'weight_records' in service_data:
                weight_records.extend(service_data['weight_records'])
        
        # Filter records for target date
        target_nutrition = [r for r in nutrition_records if r.date == target_date]
        target_activities = [r for r in activity_records if r.date == target_date]
        target_weights = [r for r in weight_records if r.date == target_date]
        
        # Calculate aggregated values using the aggregator
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_alcohol = 0
        
        # Sum up nutrition data for the day
        for nutrition in target_nutrition:
            if nutrition.calories:
                total_calories += nutrition.calories
            if nutrition.protein:
                total_protein += nutrition.protein
            if nutrition.carbs:
                total_carbs += nutrition.carbs
            if nutrition.fat:
                total_fat += nutrition.fat
            if nutrition.alcohol:
                total_alcohol += nutrition.alcohol
        
        # Get activity data - use correct field names from ActivityRecord
        total_activity = sum(a.active_calories or 0 for a in target_activities)  # Use active_calories instead of activity_score
        total_steps = sum(a.steps or 0 for a in target_activities)
        
        # Get weight data (latest for the day) - use correct field name
        latest_weight = target_weights[-1].weight_kg if target_weights else None
        
        return MacrosAndActivityRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            calories=total_calories if total_calories > 0 else None,
            protein=total_protein if total_protein > 0 else None,
            carbs=total_carbs if total_carbs > 0 else None,
            fat=total_fat if total_fat > 0 else None,
            alcohol=total_alcohol if total_alcohol > 0 else None,
            activity=total_activity if total_activity > 0 else None,
            steps=total_steps if total_steps > 0 else None,
            weight=latest_weight,
        )
    
    def _create_recovery_from_data(self, target_date: date, transformed_data: dict) -> Optional[RecoveryMetricsRecord]:
        """Create recovery metrics aggregation from in-memory data."""
        # Collect recovery data from all services
        recovery_records = []
        sleep_records = []
        resilience_records = []
        
        for service, service_data in transformed_data.items():
            if 'recovery_records' in service_data:
                recovery_records.extend(service_data['recovery_records'])
            if 'sleep_records' in service_data:
                sleep_records.extend(service_data['sleep_records'])
            if 'resilience_records' in service_data:
                resilience_records.extend(service_data['resilience_records'])
        
        # Filter records for target date
        target_recovery = [r for r in recovery_records if r.date == target_date]
        target_sleep = [r for r in sleep_records if r.date == target_date]
        target_resilience = [r for r in resilience_records if r.date == target_date]
        
        # Get latest values for the day
        recovery_score = target_recovery[-1].recovery_score if target_recovery else None
        hrv = target_recovery[-1].hrv_rmssd if target_recovery else None
        hr = target_recovery[-1].resting_hr if target_recovery else None
        
        # Fix field name mismatches for sleep data
        sleep_need = None
        sleep_actual = None
        if target_sleep:
            sleep_record = target_sleep[-1]
            # Handle different possible field names
            sleep_need = getattr(sleep_record, 'sleep_need', None) or getattr(sleep_record, 'need_minutes', None)
            sleep_actual = getattr(sleep_record, 'sleep_actual', None) or getattr(sleep_record, 'sleep_duration', None) or getattr(sleep_record, 'duration_minutes', None)
        
        resilience_level = target_resilience[-1].resilience_level if target_resilience else None
        
        return RecoveryMetricsRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            recovery=recovery_score,
            hrv=hrv,
            hr=hr,
            sleep_need=sleep_need,
            sleep_actual=sleep_actual,
            resilience_level=resilience_level,
        )
    
    def _create_training_from_data(self, target_date: date, transformed_data: dict) -> Optional[TrainingMetricsRecord]:
        """Create training metrics aggregation from in-memory data."""
        # Collect workout data from all services
        workout_records = []
        
        for service, service_data in transformed_data.items():
            if 'workout_records' in service_data:
                workout_records.extend(service_data['workout_records'])
        
        # Filter records for target date
        target_workouts = [r for r in workout_records if r.date == target_date]
        
        # Use the training aggregator with actual data
        return self.training_aggregator.aggregate_daily_training(target_date, target_workouts)
    
    def _save_consolidated_aggregation(self, agg_type: str, records: List, timestamp: str) -> str:
        """Save consolidated aggregation records to a single CSV file."""
        output_dir = "data/04_aggregated"
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert records to DataFrame
        df = pd.DataFrame([r.__dict__ for r in records])
        
        # Save to CSV
        output_file = os.path.join(output_dir, f"{agg_type}_{timestamp}.csv")
        df.to_csv(output_file, index=False)
        
        return output_file
    
    def _save_aggregations(self, target_date: date, results: dict):
        """Save aggregation results to CSV files."""
        date_str = target_date.strftime("%Y-%m-%d")
        output_dir = "data/04_aggregated"
        os.makedirs(output_dir, exist_ok=True)
        
        for agg_type, agg_data in results.items():
            try:
                # Convert aggregation to DataFrame
                df = pd.DataFrame([agg_data.__dict__])
                
                # Save to CSV
                output_file = os.path.join(output_dir, f"{agg_type}_{date_str}.csv")
                df.to_csv(output_file, index=False)
                self.logger.info(f"💾 Saved {agg_type} aggregation to {output_file}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to save {agg_type} aggregation: {e}")


def run_aggregation_pipeline(days: int = 1):
    """Run the aggregation pipeline for the specified number of days."""
    pipeline = AggregationPipeline()
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    print(f"🔄 Running aggregation pipeline for {days} day(s)")
    print(f"📅 Date range: {start_date} to {end_date}")
    
    total_aggregations = 0
    
    # Process each date
    current_date = start_date
    while current_date <= end_date:
        results = pipeline.run_daily_aggregations(current_date)
        total_aggregations += len(results)
        current_date += timedelta(days=1)
    
    print(f"🎉 Aggregation pipeline completed!")
    print(f"📊 Total aggregations created: {total_aggregations}")


if __name__ == "__main__":
    run_aggregation_pipeline(days=2)
