"""Aggregate stage for creating daily health data summaries."""

from datetime import date, timedelta, datetime
from .base_stage import PipelineStage, PipelineContext, StageResult
from src.processing.registry import ProcessorRegistry
from src.utils.pipeline_persistence import PipelinePersistence


class AggregateStage(PipelineStage):
    """Stage 4: Create daily aggregated health data summaries."""
    
    def __init__(self):
        """Initialize the aggregate stage with processor registry."""
        super().__init__('aggregate')
        
        # Initialize processor registry
        self.registry = ProcessorRegistry()
        
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
            # Process all registered aggregators
            for aggregator_name in self.registry.get_all_aggregator_names():
                # Collect data required by this aggregator
                aggregator_data = self.registry.collect_data_for_aggregator(
                    aggregator_name, context.transformed_data
                )
                
                # Get aggregator instance
                aggregator_info = self.registry.get_aggregator(aggregator_name)
                if not aggregator_info:
                    continue
                
                aggregator = aggregator_info['instance']
                
                # Call appropriate aggregation method based on aggregator type
                if aggregator_name == 'macros':
                    self.logger.info(f"🔍 Processing macros for {current_date}: {len(aggregator_data.get('workouts', []))} workouts")
                    self.logger.info(f"  Nutrition records: {len(aggregator_data.get('nutrition', []))}")
                    self.logger.info(f"  Activity records: {len(aggregator_data.get('activity', []))}")
                    self.logger.info(f"  Weight records: {len(aggregator_data.get('weight', []))}")
                    self.logger.info(f"  Available data keys: {list(aggregator_data.keys())}")
                    result = aggregator.aggregate_daily_data(
                        current_date, 
                        aggregator_data.get('nutrition', []),
                        aggregator_data.get('activity', []),
                        aggregator_data.get('weight', []),
                        aggregator_data.get('workouts', [])
                    )
                    self.logger.info(f"🎯 Macros result for {current_date}: {result.sport_type if result else 'None'}")
                    if result:
                        aggregated_data['macros_activity'].append(result)
                    else:
                        self.logger.warning(f"⚠️ No macros result for {current_date}")
                
                elif aggregator_name == 'recovery':
                    result = aggregator.aggregate_daily_recovery(
                        current_date,
                        aggregator_data.get('recovery', []),
                        aggregator_data.get('sleep', []),
                        aggregator_data.get('resilience', [])
                    )
                    if result:
                        aggregated_data['recovery_metrics'].append(result)
                
                elif aggregator_name == 'training':
                    results = aggregator.aggregate_daily_training(
                        current_date,
                        aggregator_data.get('workouts', [])
                    )
                    if results:
                        # Training aggregator now returns a list of records (one per sport)
                        aggregated_data['training_metrics'].extend(results)
            
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
        
        # Save each aggregation type to a consolidated CSV file
        for agg_type, records in aggregated_data.items():
            if records:
                file_path = self._save_consolidated_aggregation(agg_type, records, timestamp)
                file_paths[f"{agg_type}_aggregated"] = file_path
        
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
        
        # Convert records to dictionaries with proper enum serialization
        data_dicts = []
        for record in records:
            record_dict = asdict(record)
            # Convert enum values to their string values for CSV export
            for key, value in record_dict.items():
                if hasattr(value, 'value'):  # Check if it's an enum
                    record_dict[key] = value.value
            data_dicts.append(record_dict)
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(data_dicts)
        filename = f"{aggregation_type}_{timestamp.strftime('%Y-%m-%d')}.csv"
        file_path = os.path.join(agg_dir, filename)
        
        df.to_csv(file_path, index=False)
        
        self.logger.info(f"Saved {len(records)} {aggregation_type} records to {file_path}")
        
        return file_path
