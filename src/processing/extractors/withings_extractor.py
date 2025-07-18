"""Withings data extractor for processing health data from Withings API."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional

import pandas as pd

from .base_extractor import BaseExtractor
from src.models.raw_data import WeightRecord
from src.models.enums import DataSource
from src.utils.date_utils import DateUtils


class WithingsExtractor(BaseExtractor):
    """Extractor for processing Withings health data."""
    
    def __init__(self):
        """Initialize the Withings extractor."""
        super().__init__(DataSource.WITHINGS)
    
    def extract_weight_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[WeightRecord]:
        """Extract weight records from Withings API response.
        
        This is pure extraction - converts raw API data to basic WeightRecord models
        without any transformation, cleaning, or persistence.
        
        Args:
            raw_data: Raw response from Withings API containing weight data
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            List of raw WeightRecord objects
        """
        # Handle both old format (raw_data["body"]) and new format (raw_data["weight"])
        weight_data = None
        if "body" in raw_data:
            weight_data = raw_data["body"]
        elif "weight" in raw_data:
            weight_data = raw_data["weight"]
        
        if not raw_data or not weight_data:
            self.logger.info("No weight data found in Withings response")
            return []
        
        weight_records = []
        
        # Direct conversion from raw API data to WeightRecord objects
        if "measuregrps" in weight_data:
            for group in weight_data["measuregrps"]:
                # Parse timestamp from API response
                timestamp = DateUtils.parse_timestamp(group.get("date", 0))
                
                # Filter by date range
                if not (start_date.date() <= timestamp.date() <= end_date.date()):
                    continue
                
                # Initialize measurement values
                weight_kg = None
                body_fat_percentage = None
                muscle_mass_kg = None
                bone_mass_kg = None
                water_percentage = None
                
                # Extract measurements from the group
                for measure in group.get("measures", []):
                    measure_type = measure.get("type")
                    value = measure.get("value", 0)
                    unit = measure.get("unit", 0)
                    
                    # Convert value based on unit
                    actual_value = value * (10 ** unit) if value and unit else value
                    
                    # Map measurement types to fields
                    if measure_type == 1:  # Weight
                        weight_kg = actual_value
                    elif measure_type == 6:  # Body fat percentage
                        body_fat_percentage = actual_value
                    elif measure_type == 76:  # Muscle mass
                        muscle_mass_kg = actual_value
                    elif measure_type == 88:  # Bone mass
                        bone_mass_kg = actual_value
                    elif measure_type == 77:  # Water percentage
                        water_percentage = actual_value
                
                # Only create record if we have weight data
                if weight_kg is not None:
                    calculated_date = self._calculate_date_from_timestamp(timestamp)
                    record = WeightRecord(
                        timestamp=timestamp,
                        date=calculated_date,  # Calculate date in extractor
                        source=DataSource.WITHINGS,
                        weight_kg=weight_kg,
                        body_fat_percentage=body_fat_percentage,
                        muscle_mass_kg=muscle_mass_kg,
                        bone_mass_kg=bone_mass_kg,
                        water_percentage=water_percentage
                    )
                    weight_records.append(record)
        
        self.logger.info(f"Extracted {len(weight_records)} raw weight records from Withings")
        return weight_records
    
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract all data types from raw Withings API response.
        
        This is the main entry point for Withings data extraction.
        
        Args:
            raw_data: Raw API response data from Withings
            
        Returns:
            Dictionary with keys like 'weight', etc.
            and values as lists of structured records
        """
        self.logger.info("Starting Withings data extraction")
        
        extracted_data = {}
        
        # Use a wide date range since API already filtered the data
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Wide range to include all API data
        
        # Extract weight data using existing method
        weight_records = self.extract_weight_data(raw_data, start_date, end_date)
        if weight_records:
            extracted_data["weight"] = weight_records
        
        self.logger.info(f"Extracted {len(weight_records)} raw weight records from Withings")
        self.logger.info(f"Extracted Withings data with {len(extracted_data)} data types")
        return extracted_data
    

    
    def _calculate_date_from_timestamp(self, timestamp: datetime) -> Optional[date]:
        """Calculate date from datetime timestamp.
        
        Args:
            timestamp: datetime object
            
        Returns:
            Date or None if parsing fails
        """
        if not timestamp:
            return None
            
        return timestamp.date()
