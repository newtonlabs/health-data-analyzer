"""Oura data extractor for processing health data from Oura Ring API."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional

import pandas as pd

from .base_extractor import BaseExtractor
from src.models.raw_data import ActivityRecord, ResilienceRecord, WorkoutRecord
from src.models.enums import DataSource, SportType
from src.utils.date_utils import DateUtils
from src.config import default_config


class OuraExtractor(BaseExtractor):
    """Extractor for processing Oura Ring health data."""
    
    def __init__(self):
        """Initialize the Oura extractor."""
        super().__init__(DataSource.OURA)
        self.config = default_config
    
    def extract_activity_data(self, raw_data: Dict[str, Any]) -> List[ActivityRecord]:
        """Extract activity records from Oura API response.
        
        This is pure extraction - converts raw API data to basic ActivityRecord models
        without any transformation, cleaning, or date filtering.
        
        Args:
            raw_data: Raw response from Oura API containing activity data
            
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
                calculated_date = self._calculate_date_from_timestamp(timestamp_str)
                record = ActivityRecord(
                    timestamp=timestamp_str,  # Preserve for transformer
                    date=calculated_date,  # Calculate date in extractor
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
    
    def extract_resilience_data(self, raw_data: Dict[str, Any]) -> List[ResilienceRecord]:
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
                calculated_date = self._calculate_date_from_timestamp(timestamp_str)
                record = ResilienceRecord(
                    timestamp=timestamp_str,  # Preserve for transformer
                    date=calculated_date,  # Calculate date in extractor
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
    
    def extract_workout_data(self, raw_data: Dict[str, Any]) -> List[WorkoutRecord]:
        """Extract workout records from Oura API response.
        
        This is pure extraction - converts raw API data to basic WorkoutRecord models
        without any transformation, cleaning, or persistence.
        
        Args:
            raw_data: Raw response from Oura API containing workout data
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            List of raw WorkoutRecord objects
        """
        if not raw_data or "data" not in raw_data:
            print("No workout data found in Oura response")
            return []
        
        workout_records = []
        
        # Direct conversion from raw API data to WorkoutRecord objects
        for workout_item in raw_data["data"]:
            try:
                # Extract timestamps
                start_datetime_str = workout_item.get("start_datetime")
                end_datetime_str = workout_item.get("end_datetime")
                
                if not start_datetime_str or not end_datetime_str:
                    print(f"Missing datetime fields in Oura workout data, skipping record")
                    continue
                
                # Parse timestamps to calculate duration
                start_dt = DateUtils.parse_iso_timestamp(start_datetime_str)
                end_dt = DateUtils.parse_iso_timestamp(end_datetime_str)
                duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                
                # Get sport name and determine type using config system
                sport_name = workout_item.get('activity', 'unknown')
                sport_type = self.config.get_sport_type_from_name(sport_name)
                
                # Create WorkoutRecord with raw data (no transformation or filtering)
                calculated_date = self._calculate_date_from_timestamp(start_datetime_str)
                record = WorkoutRecord(
                    timestamp=start_datetime_str,  # Preserve for transformer
                    date=calculated_date,  # Calculate date in extractor
                    source=DataSource.OURA,
                    sport_type=sport_type,
                    sport_name=sport_name,
                    duration_minutes=duration_minutes,
                    calories=int(workout_item.get("calories", 0))
                )
                workout_records.append(record)
                
            except Exception as e:
                print(f"Error creating WorkoutRecord from Oura data: {e}")
                continue
        
        print(f"Extracted {len(workout_records)} raw workout records from Oura")
        return workout_records
    

    
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
            extracted_data["activity"] = activity_records
        
        # Extract resilience data
        resilience_records = self.extract_resilience_data(raw_data, start_date, end_date)
        if resilience_records:
            extracted_data["resilience"] = resilience_records
        
        # Extract workout data
        workout_records = self.extract_workout_data(raw_data, start_date, end_date)
        if workout_records:
            extracted_data["workouts"] = workout_records
        
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
        
        extracted_data = {}
        
        # Extract activity data if available (pure conversion, no filtering)
        if "activities" in raw_data:
            activity_records = self.extract_activity_data(raw_data["activities"])
            if activity_records:
                extracted_data["activity"] = activity_records
        
        # Extract resilience data if available (pure conversion, no filtering)
        if "resilience" in raw_data:
            resilience_records = self.extract_resilience_data(raw_data["resilience"])
            if resilience_records:
                extracted_data["resilience"] = resilience_records
        
        # Extract workout data if available (pure conversion, no filtering)
        if "workouts" in raw_data:
            workout_records = self.extract_workout_data(raw_data["workouts"])
            if workout_records:
                extracted_data["workouts"] = workout_records
        
        print(f"Extracted Oura data with {len(extracted_data)} data types")
        return extracted_data
    
    def _calculate_date_from_timestamp(self, timestamp: str) -> Optional[date]:
        """Calculate date from timestamp using generic conversion.
        
        Args:
            timestamp: ISO timestamp string
            
        Returns:
            Date or None if parsing fails
        """
        if not timestamp:
            return None
            
        try:
            # Parse timestamp and convert to local time
            parsed_datetime = DateUtils.parse_timestamp(timestamp, to_local=True)
            if parsed_datetime:
                return parsed_datetime.date()
        except Exception as e:
            self.logger.warning(f"Error calculating date from timestamp {timestamp}: {e}")
        
        return None
