"""Oura data extractor for processing health data from Oura Ring API."""

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.processing.extractors.base_extractor import BaseExtractor
from src.models.data_records import ActivityRecord
from src.models.enums import DataSource
from src.analysis.processors.oura import OuraProcessor


class OuraExtractor(BaseExtractor):
    """Extractor for processing Oura Ring health data."""
    
    def __init__(self):
        """Initialize the Oura extractor."""
        super().__init__(DataSource.OURA)
        self.oura_processor = OuraProcessor()
    
    def extract_activity_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ActivityRecord]:
        """Extract activity records from Oura API response.
        
        Args:
            raw_data: Raw response from Oura API containing activity data
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            List of ActivityRecord objects
        """
        if not raw_data or "activity" not in raw_data:
            self.logger.warning("No activity data found in Oura response")
            return []
        
        # Process the raw data using the existing OuraProcessor
        processed_data = self.oura_processor._process_oura_activity(
            raw_data["activity"], start_date, end_date
        )
        
        if processed_data.empty:
            self.logger.warning("No activity data after processing")
            return []
        
        # Convert DataFrame to ActivityRecord objects
        activity_records = []
        for _, row in processed_data.iterrows():
            try:
                record = ActivityRecord(
                    date=row["date"],
                    source=DataSource.OURA,
                    steps=row.get("steps", 0),
                    active_calories=row.get("active_calories", 0),
                    total_calories=row.get("calories_total", 0),
                    raw_data={
                        "activity_score": row.get("score", 0),
                        "met_1min": row.get("met_1min", 0),
                        "met_2plus": row.get("met_2plus", 0),
                        "average_met": row.get("average_met", 0.0),
                        "class_5min": row.get("class_5min", ""),
                        "non_wear_time": row.get("non_wear_time", 0),
                        "equivalent_walking_distance": row.get("equivalent_walking_distance", 0),
                        # Moved detailed activity data to raw_data for reference
                        "distance": row.get("distance", 0),
                        "inactive_time": row.get("inactive_time", 0),
                        "low_activity_time": row.get("low_activity_time", 0),
                        "medium_activity_time": row.get("medium_activity_time", 0),
                        "high_activity_time": row.get("high_activity_time", 0),
                    }
                )
                activity_records.append(record)
                
            except Exception as e:
                self.logger.error(f"Error creating ActivityRecord from Oura data: {e}")
                continue
        
        self.logger.info(f"Extracted {len(activity_records)} activity records from Oura")
        return activity_records
    
    def extract_resilience_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """Extract resilience data from Oura API response.
        
        Args:
            raw_data: Raw response from Oura API containing resilience data
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with processed resilience data
        """
        if not raw_data or "resilience" not in raw_data:
            self.logger.warning("No resilience data found in Oura response")
            return pd.DataFrame()
        
        # Process the raw data using the existing OuraProcessor
        processed_data = self.oura_processor._process_oura_resilience(
            raw_data["resilience"], start_date, end_date
        )
        
        if processed_data.empty:
            self.logger.warning("No resilience data after processing")
            return pd.DataFrame()
        
        self.logger.info(f"Extracted {len(processed_data)} resilience records from Oura")
        return processed_data
    
    def extract_all_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Extract all available data from Oura API response.
        
        Args:
            raw_data: Raw response from Oura API
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            Dictionary containing all extracted data
        """
        extracted_data = {}
        
        # Extract activity data
        activity_records = self.extract_activity_data(raw_data, start_date, end_date)
        if activity_records:
            extracted_data["activity_records"] = activity_records
        
        # Extract resilience data
        resilience_data = self.extract_resilience_data(raw_data, start_date, end_date)
        if not resilience_data.empty:
            extracted_data["resilience_data"] = resilience_data
        
        # Process all data using the existing processor for consistency
        processed_data = self.oura_processor.process_data(raw_data, start_date, end_date)
        if processed_data:
            extracted_data["processed_data"] = processed_data
        
        self.logger.info(f"Extracted Oura data with {len(extracted_data)} data types")
        return extracted_data
    
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract all data types from raw Oura API response.
        
        This is the main entry point for Oura data extraction, implementing
        the BaseExtractor interface.
        
        Args:
            raw_data: Raw API response data from Oura
            
        Returns:
            Dictionary with keys like 'activity_records', 'resilience_data', etc.
            and values as lists of structured records or processed DataFrames
        """
        self.logger.info("Starting Oura data extraction")
        
        # Use a reasonable date range if not provided in raw_data
        # In practice, the calling code should provide proper date filtering
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
        
        # Leverage the existing extract_all_data method
        extracted_data = self.extract_all_data(raw_data, start_date, end_date)
        
        # Save extracted data to CSV files
        saved_files = self.save_extracted_data_to_csv(extracted_data)
        if saved_files:
            self.logger.info(f"💾 Oura data exported to: {list(saved_files.values())}")
        
        return extracted_data
