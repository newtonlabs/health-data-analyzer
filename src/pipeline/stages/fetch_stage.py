"""Fetch stage for retrieving raw data from health services."""

from .base_stage import PipelineStage, PipelineContext, StageResult
from src.api.services.whoop_service import WhoopService
from src.api.services.oura_service import OuraService
from src.api.services.withings_service import WithingsService
from src.api.services.hevy_service import HevyService
from src.api.services.nutrition_service import NutritionService
from src.utils.pipeline_persistence import PipelinePersistence
from datetime import datetime


class FetchStage(PipelineStage):
    """Stage 1: Fetch raw data from all configured health services."""
    
    def __init__(self):
        """Initialize the fetch stage."""
        super().__init__('fetch')
        
        # Initialize services directly (no processor wrapper layer)
        self.services = {
            'whoop': WhoopService(),
            'oura': OuraService(),
            'withings': WithingsService(),
            'hevy': HevyService(),
            'nutrition': NutritionService()
        }
        
        # Initialize persistence for raw data writing
        self.persistence = PipelinePersistence()
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the fetch stage.
        
        Args:
            context: Pipeline context with configuration
            
        Returns:
            StageResult with fetched raw data
        """
        self.logger.info(f"🔄 Fetching data from {len(context.services)} services...")
        
        successful_services = []
        failed_services = []
        file_paths = {}
        timestamp = datetime.now()
        
        for service in context.services:
            if service not in self.services:
                self.logger.warning(f"Unknown service: {service}")
                failed_services.append(service)
                continue
            
            try:
                self.logger.info(f"📡 Fetching {service} data...")
                service_instance = self.services[service]
                
                # Fetch raw data directly from service (no processor wrapper)
                raw_data = self._fetch_service_data(service, service_instance, context.start_date, context.end_date)
                context.raw_data[service] = raw_data
                
                # Generate raw data files if enabled
                if context.enable_csv:
                    service_files = self._generate_raw_data_files(
                        service, raw_data, timestamp
                    )
                    file_paths.update(service_files)
                
                successful_services.append(service)
                self.logger.info(f"✅ {service} data fetched successfully")
                
            except Exception as e:
                error_msg = f"Failed to fetch {service} data: {str(e)}"
                self.logger.error(error_msg)
                failed_services.append(service)
        
        # Determine stage result
        if successful_services and not failed_services:
            # All services succeeded
            return self._create_success_result(
                data={'services_fetched': successful_services},
                file_paths=file_paths,
                metrics={
                    'total_services': len(context.services),
                    'successful_services': len(successful_services),
                    'failed_services': len(failed_services),
                    'raw_files_generated': len(file_paths)
                }
            )
        elif successful_services:
            # Some services succeeded
            return self._create_partial_result(
                data={'services_fetched': successful_services},
                file_paths=file_paths,
                metrics={
                    'total_services': len(context.services),
                    'successful_services': len(successful_services),
                    'failed_services': len(failed_services),
                    'raw_files_generated': len(file_paths)
                },
                error=f"Failed to fetch data from: {', '.join(failed_services)}"
            )
        else:
            # All services failed
            return self._create_error_result(
                error=f"Failed to fetch data from all services: {', '.join(failed_services)}"
            )
    
    def _generate_raw_data_files(self, service: str, raw_data: dict, timestamp: datetime) -> dict:
        """Generate raw data JSON files.
        
        Args:
            service: Service name
            raw_data: Raw API data
            timestamp: Timestamp for file naming
            
        Returns:
            Dictionary of generated file paths
        """
        file_paths = {}
        
        try:
            # Save raw data as JSON files - combine all data types into single file
            if raw_data:
                file_path = self.persistence.save_raw_data(
                    service, raw_data, timestamp
                )
                file_paths[f"{service}_raw"] = file_path
                    
        except Exception as e:
            self.logger.warning(f"Failed to generate raw data files for {service}: {e}")
        
        return file_paths
    
    def _fetch_service_data(self, service_name: str, service_instance, start_date, end_date) -> dict:
        """Fetch data from a specific service, handling different service interfaces.
        
        Args:
            service_name: Name of the service
            service_instance: The service instance
            start_date: Start date for data fetching (date or datetime)
            end_date: End date for data fetching (date or datetime)
            
        Returns:
            Raw data dictionary from the service
        """
        # Convert date objects to datetime objects when needed
        if hasattr(start_date, 'date'):
            # It's already a datetime
            start_dt = start_date
            end_dt = end_date
        else:
            # It's a date, convert to datetime
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
        if service_name == 'whoop':
            # Whoop service has multiple data types (expects datetime objects)
            return {
                'workouts': service_instance.get_workouts_data(start_dt, end_dt),
                'recovery': service_instance.get_recovery_data(start_dt, end_dt),
                'sleep': service_instance.get_sleep_data(start_dt, end_dt)
            }
        elif service_name == 'oura':
            # Oura service has multiple data types (now expects datetime objects for consistency)
            return {
                'activities': service_instance.get_activity_data(start_dt, end_dt),
                'resilience': service_instance.get_resilience_data(start_dt, end_dt),
                'workouts': service_instance.get_workouts_data(start_dt, end_dt)
            }
        elif service_name == 'withings':
            # Withings service has weight data (expects datetime objects)
            return service_instance.get_weight_data(start_dt, end_dt)
        elif service_name == 'hevy':
            # Hevy service has workout data (no date parameters)
            return service_instance.get_workouts_data()
        elif service_name == 'nutrition':
            # Nutrition service has nutrition data (expects datetime objects)
            return service_instance.get_nutrition_data(start_dt, end_dt)
        else:
            raise ValueError(f"Unknown service: {service_name}")
