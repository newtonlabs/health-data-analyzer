"""Clean 3-stage health data pipeline implementation.

This module implements the clean pipeline architecture:
1. API Service    → Raw JSON response     → data/01_raw/
2. Extractor      → Raw Data Models       → data/02_extracted/  
3. Transformer    → Clean Data Models     → data/03_transformed/
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.api.services.whoop_service import WhoopService
from src.processing.extractors.whoop_extractor import WhoopExtractor
from src.processing.transformers.whoop_transformer import WhoopTransformer
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
        
        # Initialize extractors
        self.whoop_extractor = WhoopExtractor()
        
        # Initialize transformers
        self.whoop_transformer = WhoopTransformer()
    
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
