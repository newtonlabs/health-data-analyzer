"""Transform stage for cleaning and normalizing extracted data."""

from .base_stage import PipelineStage, PipelineContext, StageResult
from src.processing.registry import ProcessorRegistry
from src.utils.pipeline_persistence import PipelinePersistence
from datetime import datetime


class TransformStage(PipelineStage):
    """Stage 3: Transform and clean extracted data."""
    
    def __init__(self):
        """Initialize transform stage with processor registry."""
        super().__init__('transform')
        
        # Initialize processor registry
        self.registry = ProcessorRegistry()
        
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
            self.logger.info(f"🧹 Transforming {service} data by data type...")
            
            service_transformed_data = {}
            service_records = 0
            
            # Transform each data type using registry
            for data_type, records in extracted_data.items():
                if not records:
                    continue
                
                # Find transformer for this data type
                transformer_info = self.registry.get_transformer_for_data_type(data_type)
                if not transformer_info:
                    self.logger.warning(f"No transformer for data type: {data_type}")
                    continue
                
                transformer = transformer_info['instance']
                output_key = transformer_info['output_key']
                transformed_records = transformer.transform(records)
                
                # Store with transformer's preferred output key
                service_transformed_data[output_key] = transformed_records
                service_records += len(transformed_records)
                
                self.logger.info(f"✅ Transformed {len(transformed_records)} {data_type} records to {output_key}")
            
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
    

