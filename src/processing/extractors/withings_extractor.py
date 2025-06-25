"""Withings data extractor for processing health data from Withings API."""

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.processing.extractors.base_extractor import BaseExtractor
from src.models.data_records import WeightRecord
from src.models.enums import DataSource
from src.analysis.processors.withings import WithingsProcessor


class WithingsExtractor(BaseExtractor):
    """Extractor for processing Withings health data."""
    
    def __init__(self):
        """Initialize the Withings extractor."""
        super().__init__(DataSource.WITHINGS)
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
        if not raw_data or "body" not in raw_data:
            self.logger.warning("No weight data found in Withings response")
            return []
        
        # Process the raw data using the existing WithingsProcessor
        # Pass the body data which contains measuregrps
        processed_data = self.withings_processor.process_weight_data(
            raw_data["body"], start_date, end_date
        )
        
        if processed_data.empty:
            self.logger.warning("No weight data after processing")
            return []
        
        # Convert DataFrame to WeightRecord objects
        weight_records = []
        for _, row in processed_data.iterrows():
            try:
                # Convert date to datetime for timestamp field
                record_date = row["date"]
                if isinstance(record_date, str):
                    timestamp = datetime.strptime(record_date, "%Y-%m-%d")
                else:
                    timestamp = datetime.combine(record_date, datetime.min.time())
                
                record = WeightRecord(
                    timestamp=timestamp,
                    source=DataSource.WITHINGS,
                    weight_kg=row.get("weight", 0.0),  # Already in kg from updated processor
                    body_fat_percentage=row.get("body_fat_percentage"),
                    muscle_mass_kg=row.get("muscle_mass_kg"),
                    bone_mass_kg=row.get("bone_mass_kg"),
                    water_percentage=row.get("water_percentage"),
                    raw_data={
                        "date": str(row.get("date", "")),
                        "timestamp": row.get("timestamp", 0),
                        "original_weight": row.get("weight", 0.0),
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

    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract all data types from raw Withings API response.
        
        This is the main entry point for Withings data extraction, implementing
        the BaseExtractor interface.
        
        Args:
            raw_data: Raw API response data from Withings
            
        Returns:
            Dictionary with keys like 'weight_records', 'processed_data', etc.
            and values as lists of structured records or processed DataFrames
        """
        self.logger.info("Starting Withings data extraction")
        
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
            self.logger.info(f"💾 Withings data exported to: {list(saved_files.values())}")
        
        return extracted_data
