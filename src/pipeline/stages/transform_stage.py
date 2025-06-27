"""Transform stage for cleaning and normalizing extracted data."""

from .base_stage import PipelineStage, PipelineContext, StageResult
from src.processing.transformers.workout_transformer import WorkoutTransformer
from src.processing.transformers.activity_transformer import ActivityTransformer
from src.processing.transformers.weight_transformer import WeightTransformer
from src.processing.transformers.recovery_transformer import RecoveryTransformer
from src.processing.transformers.sleep_transformer import SleepTransformer
from src.processing.transformers.exercise_transformer import ExerciseTransformer
from src.processing.transformers.nutrition_transformer import NutritionTransformer
from src.utils.pipeline_persistence import PipelinePersistence
from datetime import datetime


class TransformStage(PipelineStage):
    """Stage 3: Transform and clean extracted data."""
    
    def __init__(self):
        """Initialize the transform stage."""
        super().__init__('transform')
        
        # Initialize data-type-based transformers
        self.transformers = {
            'workout': WorkoutTransformer(),
            'activity': ActivityTransformer(),
            'weight': WeightTransformer(),
            'recovery': RecoveryTransformer(),
            'sleep': SleepTransformer(),
            'exercise': ExerciseTransformer(),
            'nutrition': NutritionTransformer()
        }
        
        # Initialize persistence for CSV writing
        self.persistence = PipelinePersistence()
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the transform stage.
        
        Args:
            context: Pipeline context with extracted data
            
        Returns:
            StageResult with transformed data
        """
        self.logger.info(f"🔄 Transforming data by data type from {len(context.extracted_data)} services...")
        
        successful_transformations = []
        failed_transformations = []
        total_records = 0
        file_paths = {}
        
        timestamp = datetime.now()
        
        # Process each service's extracted data
        for service, extracted_data in context.extracted_data.items():
            try:
                self.logger.info(f"🧹 Transforming {service} data by data type...")
                
                service_transformed_data = {}
                service_records = 0
                
                # Transform each data type using appropriate transformer
                for data_type, records in extracted_data.items():
                    if not records:
                        continue
                    
                    # Map data type to transformer
                    transformer_key = self._get_transformer_key(data_type)
                    if transformer_key not in self.transformers:
                        self.logger.warning(f"No transformer for data type: {data_type}")
                        continue
                    
                    try:
                        transformer = self.transformers[transformer_key]
                        transformed_records = transformer.transform(records)
                        service_transformed_data[data_type] = transformed_records
                        service_records += len(transformed_records)
                        
                        self.logger.info(f"✅ Transformed {len(transformed_records)} {data_type} records using {transformer_key}Transformer")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to transform {data_type}: {e}")
                        failed_transformations.append(f"{service}_{data_type}")
                
                # Store transformed data for this service
                if service_transformed_data:
                    context.transformed_data[service] = service_transformed_data
                    total_records += service_records
                    
                    # Generate CSV files if enabled
                    if context.enable_csv:
                        service_files = self._generate_csv_files(
                            service, extracted_data, service_transformed_data, timestamp
                        )
                        file_paths.update(service_files)
                    
                    successful_transformations.append(service)
                    self.logger.info(f"✅ {service} transformation completed: {service_records} records")
                else:
                    failed_transformations.append(service)
                    
            except Exception as e:
                error_msg = f"Failed to transform {service} data: {str(e)}"
                self.logger.error(error_msg)
                failed_transformations.append(service)
        
        # Determine stage result
        if successful_transformations and not failed_transformations:
            # All transformations succeeded
            return self._create_success_result(
                data={'services_transformed': successful_transformations},
                file_paths=file_paths,
                metrics={
                    'total_services': len(context.extracted_data),
                    'successful_services': len(successful_transformations),
                    'failed_services': len(failed_transformations),
                    'total_records_transformed': total_records,
                    'csv_files_generated': len(file_paths)
                }
            )
        elif successful_transformations:
            # Some transformations succeeded
            return self._create_partial_result(
                data={'services_transformed': successful_transformations},
                file_paths=file_paths,
                metrics={
                    'total_services': len(context.extracted_data),
                    'successful_services': len(successful_transformations),
                    'failed_services': len(failed_transformations),
                    'total_records_transformed': total_records,
                    'csv_files_generated': len(file_paths)
                },
                error=f"Failed to transform data from: {', '.join(failed_transformations)}"
            )
        else:
            # All transformations failed
            return self._create_error_result(
                error=f"Failed to transform data from all services: {', '.join(failed_transformations)}"
            )
    
    def _generate_csv_files(self, service: str, extracted_data: dict, 
                           transformed_data: dict, timestamp: datetime) -> dict:
        """Generate CSV files for extracted and transformed data.
        
        Args:
            service: Service name
            extracted_data: Extracted data records
            transformed_data: Transformed data records
            timestamp: Timestamp for file naming
            
        Returns:
            Dictionary of generated file paths
        """
        file_paths = {}
        
        try:
            # Generate extracted CSV files
            for data_type, records in extracted_data.items():
                if records:
                    # Remove '_records' suffix for file naming
                    clean_type = data_type.replace('_records', '')
                    file_path = self.persistence.save_extracted_data(
                        service, clean_type, records, timestamp
                    )
                    file_paths[f"{service}_{clean_type}_extracted"] = file_path
            
            # Generate transformed CSV files
            for data_type, records in transformed_data.items():
                if records:
                    # Remove '_records' suffix for file naming
                    clean_type = data_type.replace('_records', '')
                    file_path = self.persistence.save_transformed_data(
                        service, clean_type, records, timestamp
                    )
                    file_paths[f"{service}_{clean_type}_transformed"] = file_path
                    
        except Exception as e:
            self.logger.warning(f"Failed to generate CSV files for {service}: {e}")
        
        return file_paths
    
    def _get_transformer_key(self, data_type: str) -> str:
        """Map data type to transformer key.
        
        Args:
            data_type: Data type from extracted data (e.g., 'workout_records')
            
        Returns:
            Transformer key (e.g., 'workout')
        """
        # Map data types to transformer keys
        mapping = {
            'workout_records': 'workout',
            'workouts': 'workout',
            'activity_records': 'activity',
            'activities': 'activity',
            'weight_records': 'weight',
            'weights': 'weight',
            'recovery_records': 'recovery',
            'recovery': 'recovery',
            'sleep_records': 'sleep',
            'sleep': 'sleep',
            'exercise_records': 'exercise',
            'exercises': 'exercise',
            'nutrition_records': 'nutrition',
            'nutrition': 'nutrition',
            'resilience_records': 'recovery',
            'resilience': 'recovery'
        }
        
        return mapping.get(data_type, data_type.replace('_records', ''))
