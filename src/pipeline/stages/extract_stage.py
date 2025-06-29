"""Extract stage for converting raw data to structured records."""

from .base_stage import PipelineStage, PipelineContext, StageResult
from src.processing.extractors.whoop_extractor import WhoopExtractor
from src.processing.extractors.oura_extractor import OuraExtractor
from src.processing.extractors.withings_extractor import WithingsExtractor
from src.processing.extractors.hevy_extractor import HevyExtractor
from src.processing.extractors.nutrition_extractor import NutritionExtractor


class ExtractStage(PipelineStage):
    """Stage 2: Extract structured records from raw API data."""
    
    def __init__(self):
        """Initialize the extract stage."""
        super().__init__('extract')
        
        # Initialize service-specific extractors
        self.extractors = {
            'whoop': WhoopExtractor(),
            'oura': OuraExtractor(),
            'withings': WithingsExtractor(),
            'hevy': HevyExtractor(),
            'nutrition': NutritionExtractor()
        }
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the extract stage.
        
        Args:
            context: Pipeline context with raw data
            
        Returns:
            StageResult with extracted structured data
        """
        self.logger.info(f"🔄 Extracting structured data from {len(context.raw_data)} services...")
        
        successful_services = []
        failed_services = []
        total_records = 0
        
        for service, raw_data in context.raw_data.items():
            if service not in self.extractors:
                self.logger.warning(f"No extractor for service: {service}")
                failed_services.append(service)
                continue
            
            self.logger.info(f"🔧 Extracting {service} data...")
            extractor = self.extractors[service]
            
            # Extract structured data from raw data
            extracted_data = extractor.extract_data(raw_data)
            context.extracted_data[service] = extracted_data
            
            # Count records
            service_records = sum(
                len(records) if isinstance(records, list) else 0
                for records in extracted_data.values()
            )
            total_records += service_records
            
            successful_services.append(service)
            self.logger.info(f"✅ {service} extraction completed: {service_records} records")
        
        # Determine stage result
        if successful_services and not failed_services:
            # All services succeeded
            return self._create_success_result(
                data={'services_extracted': successful_services},
                metrics={
                    'total_services': len(context.raw_data),
                    'successful_services': len(successful_services),
                    'failed_services': len(failed_services),
                    'total_records_extracted': total_records
                }
            )
        elif successful_services:
            # Some services succeeded
            return self._create_partial_result(
                data={'services_extracted': successful_services},
                metrics={
                    'total_services': len(context.raw_data),
                    'successful_services': len(successful_services),
                    'failed_services': len(failed_services),
                    'total_records_extracted': total_records
                },
                error=f"Failed to extract data from: {', '.join(failed_services)}"
            )
        else:
            # All services failed
            return self._create_error_result(
                error=f"Failed to extract data from all services: {', '.join(failed_services)}"
            )
