"""Aggregate stage for creating daily health data summaries."""

from datetime import date, timedelta
from .base_stage import PipelineStage, PipelineContext, StageResult
from src.processing.aggregators import (
    MacrosActivityAggregator, RecoveryAggregator, TrainingAggregator
)
from src.utils.pipeline_persistence import PipelinePersistence
from datetime import datetime


class AggregateStage(PipelineStage):
    """Stage 4: Create daily aggregated health data summaries."""
    
    def __init__(self):
        """Initialize the aggregate stage."""
        super().__init__('aggregate')
        
        # Initialize aggregators
        self.macros_aggregator = MacrosActivityAggregator()
        self.recovery_aggregator = RecoveryAggregator()
        self.training_aggregator = TrainingAggregator()
        
        # Initialize persistence for CSV writing
        self.persistence = PipelinePersistence()
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the aggregate stage.
        
        Args:
            context: Pipeline context with transformed data
            
        Returns:
            StageResult with aggregated data
        """
        self.logger.info(f"🔄 Creating daily aggregations for {context.get_days_count()} days...")
        
        try:
            # Create aggregations for the date range
            aggregated_data = self._create_aggregations(context)
            context.aggregated_data = aggregated_data
            
            file_paths = {}
            total_records = 0
            
            # Generate CSV files if enabled
            if context.enable_csv:
                file_paths = self._generate_aggregation_files(aggregated_data)
            
            # Count total records
            for aggregation_type, records in aggregated_data.items():
                if isinstance(records, list):
                    total_records += len(records)
            
            return self._create_success_result(
                data={'aggregation_types': list(aggregated_data.keys())},
                file_paths=file_paths,
                metrics={
                    'days_processed': context.get_days_count(),
                    'aggregation_types': len(aggregated_data),
                    'total_aggregated_records': total_records,
                    'csv_files_generated': len(file_paths)
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to create aggregations: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_result(error=error_msg)
    
    def _create_aggregations(self, context: PipelineContext) -> dict:
        """Create daily aggregations from transformed data.
        
        Args:
            context: Pipeline context with transformed data
            
        Returns:
            Dictionary with aggregated data by type
        """
        aggregated_data = {
            'macros_activity': [],
            'recovery_metrics': [],
            'training_metrics': []
        }
        
        # Process each day in the date range
        current_date = context.start_date
        while current_date <= context.end_date:
            try:
                # Create macros and activity aggregation
                macros_activity = self._create_macros_activity_aggregation(
                    current_date, context.transformed_data
                )
                if macros_activity:
                    aggregated_data['macros_activity'].append(macros_activity)
                
                # Create recovery metrics aggregation
                recovery_metrics = self._create_recovery_aggregation(
                    current_date, context.transformed_data
                )
                if recovery_metrics:
                    aggregated_data['recovery_metrics'].append(recovery_metrics)
                
                # Create training metrics aggregation
                training_metrics = self._create_training_aggregation(
                    current_date, context.transformed_data
                )
                if training_metrics:
                    aggregated_data['training_metrics'].append(training_metrics)
                
            except Exception as e:
                self.logger.warning(f"Failed to create aggregations for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        # Log aggregation results
        for agg_type, records in aggregated_data.items():
            self.logger.info(f"Created {len(records)} {agg_type} records")
        
        return aggregated_data
    
    def _generate_aggregation_files(self, aggregated_data: dict) -> dict:
        """Generate CSV files for aggregated data.
        
        Args:
            aggregated_data: Dictionary with aggregated records
            
        Returns:
            Dictionary of generated file paths
        """
        file_paths = {}
        timestamp = datetime.now()
        
        try:
            # Save each aggregation type to a consolidated CSV file
            for agg_type, records in aggregated_data.items():
                if records:
                    file_path = self._save_consolidated_aggregation(agg_type, records, timestamp)
                    file_paths[f"{agg_type}_aggregated"] = file_path
                    
        except Exception as e:
            self.logger.warning(f"Failed to generate aggregation CSV files: {e}")
        
        return file_paths
    
    def _save_consolidated_aggregation(self, aggregation_type: str, records: list, timestamp: datetime) -> str:
        """Save aggregated records to a consolidated CSV file.
        
        Args:
            aggregation_type: Type of aggregation (e.g., 'macros_activity')
            records: List of aggregated records
            timestamp: Timestamp for file naming
            
        Returns:
            Path to the saved CSV file
        """
        import os
        import pandas as pd
        from dataclasses import asdict
        
        # Create aggregated data directory
        agg_dir = "data/04_aggregated"
        os.makedirs(agg_dir, exist_ok=True)
        
        # Convert records to dictionaries
        data_dicts = [asdict(record) for record in records]
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(data_dicts)
        filename = f"{aggregation_type}_{timestamp.strftime('%Y-%m-%d')}.csv"
        file_path = os.path.join(agg_dir, filename)
        
        df.to_csv(file_path, index=False)
        
        self.logger.info(f"Saved {len(records)} {aggregation_type} records to {file_path}")
        
        return file_path
    
    def _create_macros_activity_aggregation(self, target_date: date, transformed_data: dict):
        """Create macros and activity aggregation for a specific date."""
        # Collect data from all services
        nutrition_records = []
        activity_records = []
        weight_records = []
        
        for service, service_data in transformed_data.items():
            # Use simplified keys (no _records suffix)
            if 'nutrition' in service_data:
                nutrition_records.extend(service_data['nutrition'])
            if 'activity' in service_data:
                activity_records.extend(service_data['activity'])
            if 'weight' in service_data:
                weight_records.extend(service_data['weight'])
        
        return self.macros_aggregator.aggregate_daily_data(
            target_date, nutrition_records, activity_records, weight_records
        )
    
    def _create_recovery_aggregation(self, target_date: date, transformed_data: dict):
        """Create recovery aggregation for a specific date."""
        # Collect data from all services
        recovery_records = []
        sleep_records = []
        resilience_records = []
        
        for service, service_data in transformed_data.items():
            # Use simplified keys (no _records suffix)
            if 'recovery' in service_data:
                recovery_records.extend(service_data['recovery'])
            if 'sleep' in service_data:
                sleep_records.extend(service_data['sleep'])
            if 'resilience' in service_data:
                resilience_records.extend(service_data['resilience'])
        
        return self.recovery_aggregator.aggregate_daily_recovery(
            target_date, recovery_records, sleep_records, resilience_records
        )
    
    def _create_training_aggregation(self, target_date: date, transformed_data: dict):
        """Create training aggregation for a specific date."""
        # Collect workout data from all services
        workout_records = []
        
        for service, service_data in transformed_data.items():
            # Use simplified keys (no _records suffix)
            if 'workouts' in service_data:  # Whoop workouts
                workout_records.extend(service_data['workouts'])
            if 'workout' in service_data:  # Hevy/Oura workouts (simplified from workout_records)
                workout_records.extend(service_data['workout'])
        
        return self.training_aggregator.aggregate_daily_training(
            target_date, workout_records
        )
