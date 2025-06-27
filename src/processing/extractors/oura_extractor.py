"""Oura data extractor for processing health data from Oura Ring API."""

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.models.data_records import ActivityRecord, ResilienceRecord
from src.models.enums import DataSource
from src.utils.date_utils import DateUtils


class OuraExtractor:
    """Extractor for processing Oura Ring health data."""
    
    def __init__(self):
        """Initialize the Oura extractor."""
        self.source = DataSource.OURA
    
    def extract_activity_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ActivityRecord]:
        """Extract activity records from Oura API response.
        
        This is pure extraction - converts raw API data to basic ActivityRecord models
        without any transformation, cleaning, or persistence.
        
        Args:
            raw_data: Raw response from Oura API containing activity data
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            List of raw ActivityRecord objects
        """
        if not raw_data or "data" not in raw_data:
            print("No activity data found in Oura response")
            return []
        
        activity_records = []
        
        # Direct conversion from raw API data to ActivityRecord objects
        for activity_item in raw_data["data"]:
            try:
                # Extract date and preserve raw timestamp for transformer
                day_str = activity_item.get("day")
                timestamp_str = activity_item.get("timestamp")
                
                if not day_str:
                    print(f"No day field found in Oura activity data, skipping record")
                    continue
                
                # Create ActivityRecord with raw data (no transformation or filtering)
                # API already filters by date range, so no need to filter again
                record = ActivityRecord(
                    timestamp=timestamp_str,  # Preserve for transformer
                    date=None,  # Will be calculated in transformer
                    source=DataSource.OURA,
                    steps=activity_item.get("steps", 0),
                    active_calories=activity_item.get("active_calories", 0),
                    total_calories=activity_item.get("total_calories", 0)
                )
                activity_records.append(record)
                
            except Exception as e:
                print(f"Error creating ActivityRecord from Oura data: {e}")
                continue
        
        print(f"Extracted {len(activity_records)} raw activity records from Oura")
        return activity_records
    
    def extract_resilience_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ResilienceRecord]:
        """Extract resilience records from Oura API response.
        
        This is pure extraction - converts raw API data to basic ResilienceRecord models
        without any transformation, cleaning, or persistence.
        
        Args:
            raw_data: Raw response from Oura API containing resilience data
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            List of raw ResilienceRecord objects
        """
        if not raw_data or "data" not in raw_data:
            print("No resilience data found in Oura response")
            return []
        
        resilience_records = []
        
        # Direct conversion from raw API data to ResilienceRecord objects
        for resilience_item in raw_data["data"]:
            try:
                # Extract date field
                day_str = resilience_item.get("day")
                
                if not day_str:
                    print(f"No day field found in Oura resilience data, skipping record")
                    continue
                
                # Extract contributors data
                contributors = resilience_item.get("contributors", {})
                
                # Create ResilienceRecord with raw data (no transformation or filtering)
                # API already filters by date range, so no need to filter again
                record = ResilienceRecord(
                    timestamp=day_str,  # Use day as timestamp, will be processed in transformer
                    date=None,  # Will be calculated in transformer
                    source=DataSource.OURA,
                    sleep_recovery=contributors.get("sleep_recovery"),
                    daytime_recovery=contributors.get("daytime_recovery"),
                    stress=contributors.get("stress"),
                    level=resilience_item.get("level")
                )
                resilience_records.append(record)
                
            except Exception as e:
                print(f"Error creating ResilienceRecord from Oura data: {e}")
                continue
        
        print(f"Extracted {len(resilience_records)} raw resilience records from Oura")
        return resilience_records
    
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
        resilience_records = self.extract_resilience_data(raw_data, start_date, end_date)
        if resilience_records:
            extracted_data["resilience_records"] = resilience_records
        
        print(f"Extracted Oura data with {len(extracted_data)} data types")
        return extracted_data
    
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract all data types from raw Oura API response.
        
        This is the main entry point for Oura data extraction.
        
        Args:
            raw_data: Raw API response data from Oura
            
        Returns:
            Dictionary with keys like 'activity_records', 'resilience_records', etc.
            and values as lists of structured records or processed DataFrames
        """
        print("Starting Oura data extraction")
        
        # Use a reasonable date range if not provided in raw_data
        # In practice, the calling code should provide proper date filtering
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
        
        # Leverage the existing extract_all_data method
        extracted_data = self.extract_all_data(raw_data, start_date, end_date)
        
        return extracted_data
