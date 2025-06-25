"""Withings data extractor for processing health data from Withings API."""

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.processing.extractors.base_extractor import BaseExtractor
from src.models.data_records import WeightRecord
from src.analysis.processors.withings import WithingsProcessor


class WithingsExtractor(BaseExtractor):
    """Extractor for processing Withings health data."""
    
    def __init__(self):
        """Initialize the Withings extractor."""
        super().__init__()
        self.withings_processor = WithingsProcessor()
    
    def extract_weight_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[WeightRecord]:
        """Extract weight records from Withings API response.
        
        Args:
            raw_data: Raw response from Withings API containing weight data
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            List of WeightRecord objects
        """
        if not raw_data or "weight" not in raw_data:
            self.logger.warning("No weight data found in Withings response")
            return []
        
        # Process the raw data using the existing WithingsProcessor
        processed_data = self.withings_processor.process_weight_data(
            raw_data["weight"], start_date, end_date
        )
        
        if processed_data.empty:
            self.logger.warning("No weight data after processing")
            return []
        
        # Convert DataFrame to WeightRecord objects
        weight_records = []
        for _, row in processed_data.iterrows():
            try:
                record = WeightRecord(
                    date=row["date"],
                    source="withings",
                    weight_kg=row.get("weight_kg", 0.0),
                    weight_lbs=row.get("weight_lbs", 0.0),
                    bmi=row.get("bmi", 0.0),
                    metadata={
                        "measurement_type": row.get("measurement_type", ""),
                        "category": row.get("category", ""),
                        "device_id": row.get("device_id", ""),
                        "raw_value": row.get("raw_value", 0),
                        "unit": row.get("unit", ""),
                        "timestamp": row.get("timestamp", 0),
                    }
                )
                weight_records.append(record)
                
            except Exception as e:
                self.logger.error(f"Error creating WeightRecord from Withings data: {e}")
                continue
        
        self.logger.info(f"Extracted {len(weight_records)} weight records from Withings")
        return weight_records
    
    def extract_all_data(
        self, 
        raw_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Extract all available data from Withings API response.
        
        Args:
            raw_data: Raw response from Withings API
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            Dictionary containing all extracted data
        """
        extracted_data = {}
        
        # Extract weight data
        weight_records = self.extract_weight_data(raw_data, start_date, end_date)
        if weight_records:
            extracted_data["weight_records"] = weight_records
        
        # Process all data using the existing processor for consistency
        processed_data = self.withings_processor.process_data(raw_data, start_date, end_date)
        if processed_data:
            extracted_data["processed_data"] = processed_data
        
        self.logger.info(f"Extracted Withings data with {len(extracted_data)} data types")
        return extracted_data
