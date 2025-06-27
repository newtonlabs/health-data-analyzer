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
