"""Clean 3-stage health data pipeline implementation.

This module implements the clean pipeline architecture:
1. API Service    → Raw JSON response     → data/01_raw/
2. Extractor      → Raw Data Models       → data/02_extracted/  
3. Transformer    → Clean Data Models     → data/03_transformed/
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.api.services.whoop_service import WhoopService
from src.api.services.oura_service import OuraService
from src.api.services.withings_service import WithingsService
from src.api.services.hevy_service import HevyService
from src.processing.extractors.whoop_extractor import WhoopExtractor
from src.processing.extractors.oura_extractor import OuraExtractor
from src.processing.extractors.withings_extractor import WithingsExtractor
from src.processing.extractors.hevy_extractor import HevyExtractor
from src.processing.transformers.whoop_transformer import WhoopTransformer
from src.processing.transformers.oura_transformer import OuraTransformer
from src.processing.transformers.withings_transformer import WithingsTransformer
from src.processing.transformers.hevy_transformer import HevyTransformer
from src.processing.transformers.exercise_transformer import ExerciseTransformer
from src.utils.pipeline_persistence import PipelinePersistence
from src.utils.logging_utils import HealthLogger


class CleanHealthPipeline:
    """Clean 3-stage health data pipeline."""
    
    def __init__(self):
        """Initialize the clean pipeline."""
        self.logger = HealthLogger(self.__class__.__name__)
        self.persistence = PipelinePersistence()
        
        # Initialize services
        self.whoop_service = WhoopService()
        self.oura_service = OuraService()
        self.withings_service = WithingsService()
        self.hevy_service = HevyService()
        
        # Initialize extractors
        self.whoop_extractor = WhoopExtractor()
        self.oura_extractor = OuraExtractor()
        self.withings_extractor = WithingsExtractor()
        self.hevy_extractor = HevyExtractor()
        
        # Initialize transformers
        self.whoop_transformer = WhoopTransformer()
        self.oura_transformer = OuraTransformer()
        self.withings_transformer = WithingsTransformer()
        self.hevy_transformer = HevyTransformer()
        self.exercise_transformer = ExerciseTransformer()
    
    def process_whoop_data(self, days: int = 2) -> Dict[str, str]:
        """Process Whoop data through the complete 3-stage pipeline.
        
        Args:
            days: Number of days of data to process
            
        Returns:
            Dictionary with file paths for each stage
        """
        self.logger.info(f"🚀 Starting clean pipeline for Whoop data ({days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timestamp = datetime.now()
        file_paths = {}
        
        try:
            # STAGE 1: API Service → Raw JSON
            self.logger.info("📡 Stage 1: Fetching raw data from Whoop API...")
            raw_data = self.whoop_service.get_workouts_data(start_date, end_date)
            
            if not raw_data:
                self.logger.warning("No raw data retrieved from Whoop API")
                return file_paths
            
            # Save raw data
            raw_file = self.persistence.save_raw_data("whoop", raw_data, timestamp)
            file_paths["01_raw"] = raw_file
            self.logger.info(f"✅ Stage 1 complete: {raw_file}")
            
            # STAGE 2: Extractor → Raw Data Models
            self.logger.info("🔄 Stage 2: Extracting raw data models...")
            
            # Restructure data for extractor (temporary compatibility)
            restructured_data = {
                'workouts': {
                    'records': raw_data.get('records', [])
                }
            }
            
            extracted_data = self.whoop_extractor.extract_data(restructured_data)
            
            if not extracted_data.get('workouts'):
                self.logger.warning("No workout records extracted")
                return file_paths
            
            # Save extracted data
            extracted_file = self.persistence.save_extracted_data(
                "whoop", "workouts", extracted_data['workouts'], timestamp
            )
            file_paths["02_extracted"] = extracted_file
            self.logger.info(f"✅ Stage 2 complete: {extracted_file}")
            
            # STAGE 3: Transformer → Clean Data Models
            self.logger.info("🧹 Stage 3: Transforming and cleaning data...")
            
            transformed_workouts = self.whoop_transformer.transform(extracted_data['workouts'])
            
            if not transformed_workouts:
                self.logger.warning("No workout records after transformation")
                return file_paths
            
            # Save transformed data
            transformed_file = self.persistence.save_transformed_data(
                "whoop", "workouts", transformed_workouts, timestamp
            )
            file_paths["03_transformed"] = transformed_file
            self.logger.info(f"✅ Stage 3 complete: {transformed_file}")
            
            # Pipeline summary
            self.logger.info("🎉 Clean pipeline completed successfully!")
            self.logger.info(f"   Raw records: {len(raw_data.get('records', []))}")
            self.logger.info(f"   Extracted records: {len(extracted_data['workouts'])}")
            self.logger.info(f"   Transformed records: {len(transformed_workouts)}")
            
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
            # STAGE 1: API Service → Raw JSON
            self.logger.info("📡 Stage 1: Fetching raw data from Oura API...")
            raw_data = self.oura_service.get_activity_data(start_date.date(), end_date.date())
            
            if not raw_data:
                self.logger.warning("No raw data retrieved from Oura API")
                return file_paths
            
            # Save raw data
            raw_file = self.persistence.save_raw_data("oura", raw_data, timestamp)
            file_paths["01_raw"] = raw_file
            self.logger.info(f"✅ Stage 1 complete: {raw_file}")
            
            # STAGE 2: Extractor → Raw Data Models
            self.logger.info("🔄 Stage 2: Extracting raw data models...")
            
            extracted_data = self.oura_extractor.extract_activity_data(raw_data, start_date, end_date)
            
            if not extracted_data:
                self.logger.warning("No activity records extracted")
                return file_paths
            
            # Save extracted data
            extracted_file = self.persistence.save_extracted_data(
                "oura", "activities", extracted_data, timestamp
            )
            file_paths["02_extracted"] = extracted_file
            self.logger.info(f"✅ Stage 2 complete: {extracted_file}")
            
            # STAGE 3: Transformer → Clean Data Models
            self.logger.info("🧹 Stage 3: Transforming and cleaning data...")
            
            transformed_activities = self.oura_transformer.transform(extracted_data)
            
            if not transformed_activities:
                self.logger.warning("No activity records after transformation")
                return file_paths
            
            # Save transformed data
            transformed_file = self.persistence.save_transformed_data(
                "oura", "activities", transformed_activities, timestamp
            )
            file_paths["03_transformed"] = transformed_file
            self.logger.info(f"✅ Stage 3 complete: {transformed_file}")
            
            # Pipeline summary
            self.logger.info("🎉 Clean pipeline completed successfully!")
            self.logger.info(f"   Raw records: {len(raw_data.get('data', []))}")
            self.logger.info(f"   Extracted records: {len(extracted_data)}")
            self.logger.info(f"   Transformed records: {len(transformed_activities)}")
            
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
            
            transformed_weights = self.withings_transformer.transform(extracted_data)
            
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
            
            transformed_workouts = self.hevy_transformer.transform(extracted_workouts)
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
