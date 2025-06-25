"""Utilities for exporting processed data to various formats."""

import os
from datetime import datetime
from typing import List, Dict, Any, Union
from pathlib import Path

import pandas as pd

from src.models.data_records import (
    WorkoutRecord, RecoveryRecord, SleepRecord, 
    WeightRecord, NutritionRecord, ActivityRecord
)
from src.utils.logging_utils import HealthLogger


class DataExporter:
    """Handles exporting processed data to various formats."""
    
    def __init__(self, base_data_dir: str = "data"):
        """Initialize the data exporter.
        
        Args:
            base_data_dir: Base directory for data exports
        """
        self.base_data_dir = base_data_dir
        self.extracted_dir = os.path.join(base_data_dir, "extracted")
        self.logger = HealthLogger(self.__class__.__name__)
        
        # Ensure directories exist
        os.makedirs(self.extracted_dir, exist_ok=True)
    
    def save_records_to_csv(
        self, 
        records: List[Union[WorkoutRecord, RecoveryRecord, SleepRecord, WeightRecord, NutritionRecord, ActivityRecord]], 
        extractor_name: str,
        data_type: str,
        timestamp: datetime = None
    ) -> str:
        """Save data records to CSV file.
        
        Args:
            records: List of data record objects
            extractor_name: Name of the extractor (e.g., 'whoop', 'oura')
            data_type: Type of data (e.g., 'workouts', 'recovery', 'sleep')
            timestamp: Optional timestamp for filename (defaults to now)
            
        Returns:
            Path to the saved CSV file
        """
        if not records:
            self.logger.warning(f"No {data_type} records to save for {extractor_name}")
            return None
        
        # Create extractor directory
        extractor_dir = os.path.join(self.extracted_dir, extractor_name.lower())
        os.makedirs(extractor_dir, exist_ok=True)
        
        # Generate filename with date (allows overwriting)
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime("%Y-%m-%d")
        filename = f"{data_type}_{date_str}.csv"
        filepath = os.path.join(extractor_dir, filename)
        
        try:
            # Convert records to DataFrame
            df = self._records_to_dataframe(records)
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            
            self.logger.info(f"Saved {len(records)} {data_type} records to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save {data_type} records to CSV: {e}")
            return None
    
    def save_dataframe_to_csv(
        self,
        df: pd.DataFrame,
        extractor_name: str,
        data_type: str,
        timestamp: datetime = None
    ) -> str:
        """Save DataFrame directly to CSV file.
        
        Args:
            df: DataFrame to save
            extractor_name: Name of the extractor (e.g., 'whoop', 'oura')
            data_type: Type of data (e.g., 'processed_activity', 'processed_workouts')
            timestamp: Optional timestamp for filename (defaults to now)
            
        Returns:
            Path to the saved CSV file
        """
        if df.empty:
            self.logger.warning(f"Empty DataFrame for {data_type} from {extractor_name}")
            return None
        
        # Create extractor directory
        extractor_dir = os.path.join(self.extracted_dir, extractor_name.lower())
        os.makedirs(extractor_dir, exist_ok=True)
        
        # Generate filename with date (allows overwriting)
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime("%Y-%m-%d")
        filename = f"{data_type}_{date_str}.csv"
        filepath = os.path.join(extractor_dir, filename)
        
        try:
            # Save DataFrame to CSV
            df.to_csv(filepath, index=False)
            
            self.logger.info(f"Saved {len(df)} rows of {data_type} data to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save {data_type} DataFrame to CSV: {e}")
            return None
    
    def _records_to_dataframe(self, records: List[Any]) -> pd.DataFrame:
        """Convert list of data records to DataFrame.
        
        Args:
            records: List of data record objects
            
        Returns:
            DataFrame with record data
        """
        if not records:
            return pd.DataFrame()
        
        # Convert records to dictionaries, excluding raw_data for cleaner CSV
        record_dicts = []
        for record in records:
            record_dict = {}
            for field_name, field_value in record.__dict__.items():
                if field_name == 'raw_data':
                    continue  # Skip raw_data for cleaner CSV
                
                # Convert enums to string values
                if hasattr(field_value, 'value'):
                    record_dict[field_name] = field_value.value
                else:
                    record_dict[field_name] = field_value
            
            record_dicts.append(record_dict)
        
        return pd.DataFrame(record_dicts)
    
    def get_latest_export_path(self, extractor_name: str, data_type: str) -> str:
        """Get the path to the most recent export file.
        
        Args:
            extractor_name: Name of the extractor
            data_type: Type of data
            
        Returns:
            Path to the most recent export file, or None if not found
        """
        extractor_dir = os.path.join(self.extracted_dir, extractor_name.lower())
        if not os.path.exists(extractor_dir):
            return None
        
        # Find files matching the pattern
        pattern = f"{data_type}_*.csv"
        matching_files = list(Path(extractor_dir).glob(pattern))
        
        if not matching_files:
            return None
        
        # Return the most recent file
        latest_file = max(matching_files, key=os.path.getctime)
        return str(latest_file)
