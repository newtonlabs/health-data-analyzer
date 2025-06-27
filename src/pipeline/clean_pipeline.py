"""Clean 3-stage health data pipeline implementation.

This module implements the clean pipeline architecture:
1. API Service    → Raw JSON response     → data/01_raw/
2. Extractor      → Raw Data Models       → data/02_extracted/  
3. Transformer    → Clean Data Models     → data/03_transformed/
4. Aggregator     → Daily Aggregations    → data/04_aggregated/
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dateutil import parser

from src.api.services.whoop_service import WhoopService
from src.api.services.oura_service import OuraService
from src.api.services.withings_service import WithingsService
from src.api.services.hevy_service import HevyService
from src.api.services.nutrition_service import NutritionService
from src.processing.extractors.whoop_extractor import WhoopExtractor
from src.processing.extractors.oura_extractor import OuraExtractor
from src.processing.extractors.withings_extractor import WithingsExtractor
from src.processing.extractors.hevy_extractor import HevyExtractor
from src.processing.extractors.nutrition_extractor import NutritionExtractor
from src.processing.transformers.workout_transformer import WorkoutTransformer
from src.processing.transformers.activity_transformer import ActivityTransformer
from src.processing.transformers.weight_transformer import WeightTransformer
from src.processing.transformers.exercise_transformer import ExerciseTransformer
from src.processing.transformers.recovery_transformer import RecoveryTransformer
from src.processing.transformers.sleep_transformer import SleepTransformer
from src.processing.transformers.resilience_transformer import ResilienceTransformer
from src.processing.transformers.nutrition_transformer import NutritionTransformer
from src.utils.pipeline_persistence import PipelinePersistence
from src.utils.logging_utils import HealthLogger
from src.pipeline.aggregation_pipeline import AggregationPipeline


class CleanHealthPipeline:
    """Clean 4-stage health data pipeline."""
    
    def __init__(self):
        """Initialize the clean pipeline."""
        self.logger = HealthLogger(self.__class__.__name__)
        self.persistence = PipelinePersistence()
        self.aggregation_pipeline = AggregationPipeline()
        
        # Initialize services
        self.whoop_service = WhoopService()
        self.oura_service = OuraService()
        self.withings_service = WithingsService()
        self.hevy_service = HevyService()
        self.nutrition_service = NutritionService()
        
        # Initialize extractors
        self.whoop_extractor = WhoopExtractor()
        self.oura_extractor = OuraExtractor()
        self.withings_extractor = WithingsExtractor()
        self.hevy_extractor = HevyExtractor()
        self.nutrition_extractor = NutritionExtractor()
        
        # Initialize transformers
        self.workout_transformer = WorkoutTransformer()
        self.activity_transformer = ActivityTransformer()
        self.weight_transformer = WeightTransformer()
        self.exercise_transformer = ExerciseTransformer()
        self.recovery_transformer = RecoveryTransformer()
        self.sleep_transformer = SleepTransformer()
        self.resilience_transformer = ResilienceTransformer()
        self.nutrition_transformer = NutritionTransformer()
    
    def process_whoop_data(self, days: int = 2) -> Dict[str, str]:
        """Process Whoop data through the complete 3-stage pipeline.
        
        Extracts all 3 Whoop data types: workouts, recovery, and sleep.
        
        Args:
            days: Number of days of data to process
            
        Returns:
            Dictionary with file paths for each stage and data type
        """
        self.logger.info(f"🚀 Starting clean pipeline for Whoop data ({days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timestamp = datetime.now()
        file_paths = {}
        
        try:
            # STAGE 1: API Service → Raw JSON (All 3 data types)
            self.logger.info("📡 Stage 1: Fetching raw data from Whoop API...")
            
            workouts_raw = self.whoop_service.get_workouts_data(start_date, end_date)
            recovery_raw = self.whoop_service.get_recovery_data(start_date, end_date)
            sleep_raw = self.whoop_service.get_sleep_data(start_date, end_date)
            
            # Combine all raw data
            combined_raw = {
                "workouts": workouts_raw,
                "recovery": recovery_raw,
                "sleep": sleep_raw
            }
            
            # Save raw data
            raw_file = self.persistence.save_raw_data("whoop", combined_raw, timestamp)
            file_paths["01_raw"] = raw_file
            self.logger.info(f"✅ Stage 1 complete: {raw_file}")
            
            # STAGE 2: Extractor → Raw Data Models
            self.logger.info("🔄 Stage 2: Extracting raw data models...")
            
            # Extract all 3 data types using the existing extract_data method
            extracted_data = self.whoop_extractor.extract_data(combined_raw)
            
            extracted_workouts = extracted_data.get('workouts', [])
            extracted_recovery = extracted_data.get('recovery', [])
            extracted_sleep = extracted_data.get('sleep', [])
            
            if not any([extracted_workouts, extracted_recovery, extracted_sleep]):
                self.logger.warning("No data extracted from any Whoop data type")
                return file_paths
            
            # Save extracted data for each type
            if extracted_workouts:
                workouts_file = self.persistence.save_extracted_data(
                    "whoop", "workouts", extracted_workouts, timestamp
                )
                file_paths["02_extracted_workouts"] = workouts_file
            
            if extracted_recovery:
                recovery_file = self.persistence.save_extracted_data(
                    "whoop", "recovery", extracted_recovery, timestamp
                )
                file_paths["02_extracted_recovery"] = recovery_file
            
            if extracted_sleep:
                sleep_file = self.persistence.save_extracted_data(
                    "whoop", "sleep", extracted_sleep, timestamp
                )
                file_paths["02_extracted_sleep"] = sleep_file
            
            self.logger.info(f"✅ Stage 2 complete: {len([k for k in file_paths.keys() if k.startswith('02_')])} data types extracted")
            
            # STAGE 3: Transformer → Clean Data Models
            self.logger.info("🧹 Stage 3: Transforming and cleaning data...")
            
            # Transform each data type
            transformed_workouts = []
            transformed_recovery = []
            transformed_sleep = []
            
            if extracted_workouts:
                transformed_workouts = self.workout_transformer.transform(extracted_workouts)
                if transformed_workouts:
                    workouts_transformed_file = self.persistence.save_transformed_data(
                        "whoop", "workouts", transformed_workouts, timestamp
                    )
                    file_paths["03_transformed_workouts"] = workouts_transformed_file
            
            if extracted_recovery:
                transformed_recovery = self.recovery_transformer.transform(extracted_recovery)
                if transformed_recovery:
                    recovery_transformed_file = self.persistence.save_transformed_data(
                        "whoop", "recovery", transformed_recovery, timestamp
                    )
                    file_paths["03_transformed_recovery"] = recovery_transformed_file
            
            if extracted_sleep:
                transformed_sleep = self.sleep_transformer.transform(extracted_sleep)
                if transformed_sleep:
                    sleep_transformed_file = self.persistence.save_transformed_data(
                        "whoop", "sleep", transformed_sleep, timestamp
                    )
                    file_paths["03_transformed_sleep"] = sleep_transformed_file
            
            self.logger.info(f"✅ Stage 3 complete: {len([k for k in file_paths.keys() if k.startswith('03_')])} data types transformed")
            
            # Pipeline summary
            self.logger.info("🎉 Clean pipeline completed successfully!")
            self.logger.info(f"   Raw workouts: {len(workouts_raw.get('data', []))}")
            self.logger.info(f"   Raw recovery: {len(recovery_raw.get('data', []))}")
            self.logger.info(f"   Raw sleep: {len(sleep_raw.get('data', []))}")
            self.logger.info(f"   Extracted workouts: {len(extracted_workouts)}")
            self.logger.info(f"   Extracted recovery: {len(extracted_recovery)}")
            self.logger.info(f"   Extracted sleep: {len(extracted_sleep)}")
            self.logger.info(f"   Transformed workouts: {len(transformed_workouts)}")
            self.logger.info(f"   Transformed recovery: {len(transformed_recovery)}")
            self.logger.info(f"   Transformed sleep: {len(transformed_sleep)}")
            
            return file_paths
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    def process_oura_data(self, days: int = 2) -> Dict[str, str]:
        """Process Oura data through the complete 3-stage pipeline.
        
        Args:
            days: Number of days of data to process
            
        Returns:
            Dictionary with file paths for each stage
        """
        self.logger.info(f"🚀 Starting clean pipeline for Oura data ({days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timestamp = datetime.now()
        file_paths = {}
        
        try:
            # STAGE 1: API Service → Raw JSON for all Oura data types
            self.logger.info("📡 Stage 1: Fetching raw data from Oura API...")
            
            # Fetch activity data (full pipeline)
            activity_data = self.oura_service.get_activity_data(start_date.date(), end_date.date())
            
            # Fetch resilience data (API stage only)
            resilience_data = self.oura_service.get_resilience_data(start_date.date(), end_date.date())
            
            # Fetch workout data (API stage only)  
            workout_data = self.oura_service.get_workouts_data(start_date.date(), end_date.date())
            
            # Save all raw data
            if activity_data:
                activity_raw_file = self.persistence.save_raw_data("oura_activity", activity_data, timestamp)
                file_paths["01_raw_activity"] = activity_raw_file
                self.logger.info(f"✅ Activity raw data saved: {activity_raw_file}")
            
            if resilience_data:
                resilience_raw_file = self.persistence.save_raw_data("oura_resilience", resilience_data, timestamp)
                file_paths["01_raw_resilience"] = resilience_raw_file
                self.logger.info(f"✅ Resilience raw data saved: {resilience_raw_file}")
                self.logger.info(f"📊 Resilience records: {len(resilience_data.get('data', []))}")
            
            if workout_data:
                workout_raw_file = self.persistence.save_raw_data("oura_workouts", workout_data, timestamp)
                file_paths["01_raw_workouts"] = workout_raw_file
                self.logger.info(f"✅ Workout raw data saved: {workout_raw_file}")
                self.logger.info(f"📊 Workout records: {len(workout_data.get('data', []))}")
            
            # Continue with full pipeline only for activity data
            if not activity_data:
                self.logger.warning("No activity data retrieved from Oura API")
                return file_paths
            
            # STAGE 2: Extractor → Raw Data Models (Activity + Resilience + Workouts)
            self.logger.info("🔄 Stage 2: Extracting data models...")
            
            # Extract activity data
            extracted_activities = self.oura_extractor.extract_activity_data(activity_data, start_date, end_date)
            
            # Extract resilience data if available
            extracted_resilience = []
            if resilience_data:
                extracted_resilience = self.oura_extractor.extract_resilience_data(resilience_data, start_date, end_date)
            
            # Extract workout data if available
            extracted_workouts = []
            if workout_data:
                extracted_workouts = self.oura_extractor.extract_workout_data(workout_data, start_date, end_date)
            
            if not extracted_activities and not extracted_resilience and not extracted_workouts:
                self.logger.warning("No records extracted from any data type")
                return file_paths
            
            # Save extracted data
            if extracted_activities:
                activities_extracted_file = self.persistence.save_extracted_data(
                    "oura", "activities", extracted_activities, timestamp
                )
                file_paths["02_extracted_activities"] = activities_extracted_file
                self.logger.info(f"✅ Activities extracted: {activities_extracted_file}")
            
            if extracted_resilience:
                resilience_extracted_file = self.persistence.save_extracted_data(
                    "oura", "resilience", extracted_resilience, timestamp
                )
                file_paths["02_extracted_resilience"] = resilience_extracted_file
                self.logger.info(f"✅ Resilience extracted: {resilience_extracted_file}")
            
            if extracted_workouts:
                workouts_extracted_file = self.persistence.save_extracted_data(
                    "oura", "workouts", extracted_workouts, timestamp
                )
                file_paths["02_extracted_workouts"] = workouts_extracted_file
                self.logger.info(f"✅ Workouts extracted: {workouts_extracted_file}")
            
            # STAGE 3: Transformer → Clean Data Models (Activity + Resilience + Workouts)
            self.logger.info("🧹 Stage 3: Transforming and cleaning data...")
            
            # Transform activity data
            transformed_activities = []
            if extracted_activities:
                transformed_activities = self.activity_transformer.transform(extracted_activities)
            
            # Transform resilience data
            transformed_resilience = []
            if extracted_resilience:
                transformed_resilience = self.resilience_transformer.transform(extracted_resilience)
            
            # Transform workout data
            transformed_workouts = []
            if extracted_workouts:
                transformed_workouts = self.workout_transformer.transform(extracted_workouts)
            
            if not transformed_activities and not transformed_resilience and not transformed_workouts:
                self.logger.warning("No records after transformation")
                return file_paths
            
            # Save transformed data
            if transformed_activities:
                activities_transformed_file = self.persistence.save_transformed_data(
                    "oura", "activities", transformed_activities, timestamp
                )
                file_paths["03_transformed_activities"] = activities_transformed_file
                self.logger.info(f"✅ Activities transformed: {activities_transformed_file}")
            
            if transformed_resilience:
                resilience_transformed_file = self.persistence.save_transformed_data(
                    "oura", "resilience", transformed_resilience, timestamp
                )
                file_paths["03_transformed_resilience"] = resilience_transformed_file
                self.logger.info(f"✅ Resilience transformed: {resilience_transformed_file}")
            
            if transformed_workouts:
                workouts_transformed_file = self.persistence.save_transformed_data(
                    "oura", "workouts", transformed_workouts, timestamp
                )
                file_paths["03_transformed_workouts"] = workouts_transformed_file
                self.logger.info(f"✅ Workouts transformed: {workouts_transformed_file}")
            
            # Pipeline summary
            self.logger.info("🎉 Clean pipeline completed successfully!")
            if activity_data:
                self.logger.info(f"   Activity raw records: {len(activity_data.get('data', []))}")
                self.logger.info(f"   Activity extracted records: {len(extracted_activities)}")
                self.logger.info(f"   Activity transformed records: {len(transformed_activities)}")
            if resilience_data:
                self.logger.info(f"   Resilience raw records: {len(resilience_data.get('data', []))}")
                self.logger.info(f"   Resilience extracted records: {len(extracted_resilience)}")
                self.logger.info(f"   Resilience transformed records: {len(transformed_resilience)}")
            if workout_data:
                self.logger.info(f"   Workout raw records: {len(workout_data.get('data', []))}")
                self.logger.info(f"   Workout extracted records: {len(extracted_workouts)}")
                self.logger.info(f"   Workout transformed records: {len(transformed_workouts)}")
            
            return file_paths
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    def process_withings_data(self, days: int = 2) -> Dict[str, str]:
        """Process Withings data through the complete 3-stage pipeline.
        
        Args:
            days: Number of days of data to process
            
        Returns:
            Dictionary with file paths for each stage
        """
        self.logger.info(f"🚀 Starting clean pipeline for Withings data ({days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timestamp = datetime.now()
        file_paths = {}
        
        try:
            # STAGE 1: API Service → Raw JSON
            self.logger.info("📡 Stage 1: Fetching raw data from Withings API...")
            raw_data = self.withings_service.get_weight_data(start_date, end_date)
            
            if not raw_data:
                self.logger.warning("No raw data retrieved from Withings API")
                return file_paths
            
            # Save raw data
            raw_file = self.persistence.save_raw_data("withings", raw_data, timestamp)
            file_paths["01_raw"] = raw_file
            self.logger.info(f"✅ Stage 1 complete: {raw_file}")
            
            # STAGE 2: Extractor → Raw Data Models
            self.logger.info("🔄 Stage 2: Extracting raw data models...")
            
            extracted_data = self.withings_extractor.extract_weight_data(raw_data, start_date, end_date)
            
            if not extracted_data:
                self.logger.warning("No weight records extracted")
                return file_paths
            
            # Save extracted data
            extracted_file = self.persistence.save_extracted_data(
                "withings", "weights", extracted_data, timestamp
            )
            file_paths["02_extracted"] = extracted_file
            self.logger.info(f"✅ Stage 2 complete: {extracted_file}")
            
            # STAGE 3: Transformer → Clean Data Models
            self.logger.info("🧹 Stage 3: Transforming and cleaning data...")
            
            transformed_weights = self.weight_transformer.transform(extracted_data)
            
            if not transformed_weights:
                self.logger.warning("No weight records after transformation")
                return file_paths
            
            # Save transformed data
            transformed_file = self.persistence.save_transformed_data(
                "withings", "weights", transformed_weights, timestamp
            )
            file_paths["03_transformed"] = transformed_file
            self.logger.info(f"✅ Stage 3 complete: {transformed_file}")
            
            # Pipeline summary
            self.logger.info("🎉 Clean pipeline completed successfully!")
            self.logger.info(f"   Raw records: {len(raw_data.get('body', {}).get('measuregrps', []))}")
            self.logger.info(f"   Extracted records: {len(extracted_data)}")
            self.logger.info(f"   Transformed records: {len(transformed_weights)}")
            
            return file_paths
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    def process_hevy_data(self, days: int = 2) -> Dict[str, str]:
        """Process Hevy data through the complete 3-stage pipeline.
        
        Args:
            days: Number of days of data to process
            
        Returns:
            Dictionary with file paths for each stage
        """
        self.logger.info(f"🚀 Starting clean pipeline for Hevy data ({days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timestamp = datetime.now()
        file_paths = {}
        
        try:
            # STAGE 1: API Service → Raw JSON
            self.logger.info("📡 Stage 1: Fetching raw data from Hevy API...")
            raw_data = self.hevy_service.get_workouts_data(page_size=10)  # Use default page size
            
            if not raw_data:
                self.logger.warning("No raw data retrieved from Hevy API")
                return file_paths
            
            # Save raw data
            raw_file = self.persistence.save_raw_data("hevy", raw_data, timestamp)
            file_paths["01_raw"] = raw_file
            self.logger.info(f"✅ Stage 1 complete: {raw_file}")
            
            # STAGE 2: Extractor → Raw Data Models
            self.logger.info("🔄 Stage 2: Extracting raw data models...")
            
            extracted_workouts = self.hevy_extractor.extract_workouts(raw_data, end_date)
            extracted_exercises = self.hevy_extractor.extract_exercises(raw_data, end_date)
            
            if not extracted_workouts:
                self.logger.warning("No workout records extracted")
                return file_paths
            
            if not extracted_exercises:
                self.logger.warning("No exercise records extracted")
                return file_paths
            
            # Save extracted data
            extracted_workouts_file = self.persistence.save_extracted_data(
                "hevy", "workouts", extracted_workouts, timestamp
            )
            extracted_exercises_file = self.persistence.save_extracted_data(
                "hevy", "exercises", extracted_exercises, timestamp
            )
            file_paths["02_extracted_workouts"] = extracted_workouts_file
            file_paths["02_extracted_exercises"] = extracted_exercises_file
            self.logger.info(f"✅ Stage 2 complete: {extracted_workouts_file}, {extracted_exercises_file}")
            
            # STAGE 3: Transformer → Clean Data Models
            self.logger.info("🧹 Stage 3: Transforming and cleaning data...")
            
            transformed_workouts = self.workout_transformer.transform(extracted_workouts)
            transformed_exercises = self.exercise_transformer.transform(extracted_exercises)
            
            if not transformed_workouts:
                self.logger.warning("No workout records after transformation")
                return file_paths
            
            if not transformed_exercises:
                self.logger.warning("No exercise records after transformation")
                return file_paths
            
            # Save transformed data
            transformed_workouts_file = self.persistence.save_transformed_data(
                "hevy", "workouts", transformed_workouts, timestamp
            )
            transformed_exercises_file = self.persistence.save_transformed_data(
                "hevy", "exercises", transformed_exercises, timestamp
            )
            file_paths["03_transformed_workouts"] = transformed_workouts_file
            file_paths["03_transformed_exercises"] = transformed_exercises_file
            self.logger.info(f"✅ Stage 3 complete: {transformed_workouts_file}, {transformed_exercises_file}")
            
            # Pipeline summary
            self.logger.info("🎉 Clean pipeline completed successfully!")
            self.logger.info(f"   Raw records: {len(raw_data.get('workouts', []))}")
            self.logger.info(f"   Extracted workout records: {len(extracted_workouts)}")
            self.logger.info(f"   Extracted exercise records: {len(extracted_exercises)}")
            self.logger.info(f"   Transformed workout records: {len(transformed_workouts)}")
            self.logger.info(f"   Transformed exercise records: {len(transformed_exercises)}")
            
            return file_paths
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    def process_nutrition_data(self, days: int = 7) -> Dict[str, str]:
        """Process nutrition data through the complete 3-stage pipeline.
        
        Extracts nutrition data from CSV files using the same clean architecture
        as API-based services.
        
        Args:
            days: Number of days of data to process
            
        Returns:
            Dictionary with file paths for each stage
        """
        self.logger.info(f"🚀 Starting clean pipeline for Nutrition data ({days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timestamp = datetime.now()
        file_paths = {}
        
        try:
            # STAGE 1: File Service → Raw Data (CSV converted to JSON-like format)
            self.logger.info("📁 Stage 1: Loading raw data from nutrition CSV...")
            raw_data = self.nutrition_service.get_nutrition_data(start_date, end_date)
            
            if not raw_data or not raw_data.get("data"):
                self.logger.warning("No raw nutrition data retrieved")
                return file_paths
            
            # Save raw data (CSV data converted to JSON format)
            raw_file = self.persistence.save_raw_data("nutrition", raw_data, timestamp)
            file_paths["01_raw"] = raw_file
            self.logger.info(f"✅ Stage 1 complete: {raw_file}")
            
            # STAGE 2: Extractor → Raw Data Models
            self.logger.info("🔄 Stage 2: Extracting raw data models...")
            extracted_data = self.nutrition_extractor.extract_nutrition(raw_data, start_date, end_date)
            
            if not extracted_data:
                self.logger.warning("No nutrition records extracted")
                return file_paths
            
            # Save extracted data
            extracted_file = self.persistence.save_extracted_data(
                "nutrition", "nutrition", extracted_data, timestamp
            )
            file_paths["02_extracted"] = extracted_file
            self.logger.info(f"✅ Stage 2 complete: {extracted_file}")
            
            # STAGE 3: Transformer → Clean Data Models
            self.logger.info("🧹 Stage 3: Transforming and cleaning data...")
            transformed_nutrition = self.nutrition_transformer.transform(extracted_data)
            
            if not transformed_nutrition:
                self.logger.warning("No nutrition records after transformation")
                return file_paths
            
            # Save transformed data
            transformed_file = self.persistence.save_transformed_data(
                "nutrition", "nutrition", transformed_nutrition, timestamp
            )
            file_paths["03_transformed"] = transformed_file
            self.logger.info(f"✅ Stage 3 complete: {transformed_file}")
            
            # Pipeline summary
            self.logger.info("🎉 Clean pipeline completed successfully!")
            self.logger.info(f"   Raw records: {len(raw_data.get('data', []))}")
            self.logger.info(f"   Extracted records: {len(extracted_data)}")
            self.logger.info(f"   Transformed records: {len(transformed_nutrition)}")
            
            return file_paths
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    def get_pipeline_summary(self, file_paths: Dict[str, str]) -> Dict[str, Any]:
        """Get summary of pipeline execution.
        
        Args:
            file_paths: File paths from pipeline execution
            
        Returns:
            Summary dictionary with statistics
        """
        summary = {
            "stages_completed": len(file_paths),
            "files_generated": file_paths,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add file sizes if files exist
        import os
        for stage, filepath in file_paths.items():
            if os.path.exists(filepath):
                size_bytes = os.path.getsize(filepath)
                summary[f"{stage}_size_bytes"] = size_bytes
        
        return summary

    def run_full_pipeline(self, days: int = 7) -> dict:
        """Run the complete 4-stage health data pipeline.
        
        Stages:
        1. Raw data fetch (APIs)
        2. Data extraction (API → structured records)
        3. Data transformation (cleaning, date calculation)
        4. Data aggregation (daily summaries)
        
        Args:
            days: Number of days to process
            
        Returns:
            Dictionary with pipeline results
        """
        self.logger.info(f"🚀 Starting complete 4-stage pipeline for {days} days")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        
        results = {
            'start_date': start_date,
            'end_date': end_date,
            'days_processed': days,
            'stages_completed': 0,
            'services_processed': {},
            'aggregations_created': 0
        }
        
        try:
            # Stage 1-3: Existing pipeline
            self.logger.info("📊 Running stages 1-3: Raw → Extract → Transform")
            
            # Process each service
            services = ['whoop', 'oura', 'withings', 'hevy', 'nutrition']
            for service in services:
                try:
                    if service == 'whoop':
                        service_results = self.process_whoop_data(days)
                    elif service == 'oura':
                        service_results = self.process_oura_data(days)
                    elif service == 'withings':
                        service_results = self.process_withings_data(days)
                    elif service == 'hevy':
                        service_results = self.process_hevy_data(days)
                    elif service == 'nutrition':
                        service_results = self.process_nutrition_data(days)
                    
                    results['services_processed'][service] = service_results
                    self.logger.info(f"✅ {service.title()}: Stages 1-3 completed")
                    
                except Exception as e:
                    self.logger.error(f"❌ {service.title()}: Pipeline failed - {e}")
                    results['services_processed'][service] = {'error': str(e)}
            
            results['stages_completed'] = 3
            
            # Stage 4: Aggregations
            self.logger.info("🔄 Running stage 4: Daily aggregations")
            
            current_date = start_date
            total_aggregations = 0
            
            while current_date <= end_date:
                try:
                    daily_results = self.aggregation_pipeline.run_daily_aggregations(current_date)
                    total_aggregations += len(daily_results)
                    self.logger.info(f"✅ {current_date}: {len(daily_results)} aggregations created")
                except Exception as e:
                    self.logger.error(f"❌ {current_date}: Aggregation failed - {e}")
                
                current_date += timedelta(days=1)
            
            results['aggregations_created'] = total_aggregations
            results['stages_completed'] = 4
            
            self.logger.info(f"🎉 Complete 4-stage pipeline finished!")
            self.logger.info(f"📊 Services processed: {len(results['services_processed'])}")
            self.logger.info(f"📊 Aggregations created: {total_aggregations}")
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            results['error'] = str(e)
        
        return results
