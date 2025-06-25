"""Pipeline data persistence utilities for saving data at each stage."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Union
from pathlib import Path

import pandas as pd

from src.utils.logging_utils import HealthLogger


class PipelinePersistence:
    """Utility for saving pipeline data at each stage."""
    
    def __init__(self, base_dir: str = "data"):
        """Initialize pipeline persistence.
        
        Args:
            base_dir: Base directory for pipeline data
        """
        self.base_dir = Path(base_dir)
        self.logger = HealthLogger(self.__class__.__name__)
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all pipeline directories exist."""
        stages = ["01_raw", "02_extracted", "03_transformed"]
        for stage in stages:
            stage_dir = self.base_dir / stage
            stage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_raw_data(self, service_name: str, data: Dict[str, Any], timestamp: datetime = None) -> str:
        """Save raw API response data.
        
        Args:
            service_name: Name of the service (e.g., 'whoop', 'oura')
            data: Raw API response data
            timestamp: Timestamp for filename (defaults to now)
            
        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        filename = f"{service_name}_raw_{timestamp.strftime('%Y-%m-%d')}.json"
        filepath = self.base_dir / "01_raw" / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Saved raw data to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save raw data: {e}")
            raise
    
    def save_extracted_data(self, service_name: str, data_type: str, records: List[Any], timestamp: datetime = None) -> str:
        """Save extracted data models as CSV.
        
        Args:
            service_name: Name of the service (e.g., 'whoop', 'oura')
            data_type: Type of data (e.g., 'workouts', 'activities', 'weights')
            records: List of data model records
            timestamp: Timestamp for filename (defaults to now)
            
        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        filename = f"{service_name}_{data_type}_extracted_{timestamp.strftime('%Y-%m-%d')}.csv"
        filepath = self.base_dir / "02_extracted" / filename
        
        try:
            # Convert records to DataFrame
            if not records:
                self.logger.warning(f"No records to save for {service_name} {data_type}")
                return str(filepath)
            
            # Convert data model objects to dictionaries
            data_dicts = []
            for record in records:
                if hasattr(record, '__dict__'):
                    record_dict = record.__dict__.copy()
                    # Convert datetime objects to strings
                    for key, value in record_dict.items():
                        if isinstance(value, datetime):
                            record_dict[key] = value.isoformat()
                        elif hasattr(value, 'value'):  # Handle enums
                            record_dict[key] = value.value
                    data_dicts.append(record_dict)
                else:
                    data_dicts.append(record)
            
            df = pd.DataFrame(data_dicts)
            df.to_csv(filepath, index=False)
            
            self.logger.info(f"Saved {len(records)} extracted records to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save extracted data: {e}")
            raise
    
    def save_transformed_data(self, service_name: str, data_type: str, records: List[Any], timestamp: datetime = None) -> str:
        """Save transformed data models as CSV.
        
        Args:
            service_name: Name of the service (e.g., 'whoop', 'oura')
            data_type: Type of data (e.g., 'workouts', 'activities', 'weights')
            records: List of transformed data model records
            timestamp: Timestamp for filename (defaults to now)
            
        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        filename = f"{service_name}_{data_type}_transformed_{timestamp.strftime('%Y-%m-%d')}.csv"
        filepath = self.base_dir / "03_transformed" / filename
        
        try:
            # Convert records to DataFrame
            if not records:
                self.logger.warning(f"No transformed records to save for {service_name} {data_type}")
                return str(filepath)
            
            # Convert data model objects to dictionaries
            data_dicts = []
            for record in records:
                if hasattr(record, '__dict__'):
                    record_dict = record.__dict__.copy()
                    # Convert datetime objects to strings
                    for key, value in record_dict.items():
                        if isinstance(value, datetime):
                            record_dict[key] = value.isoformat()
                        elif hasattr(value, 'value'):  # Handle enums
                            record_dict[key] = value.value
                    data_dicts.append(record_dict)
                else:
                    data_dicts.append(record)
            
            df = pd.DataFrame(data_dicts)
            df.to_csv(filepath, index=False)
            
            self.logger.info(f"Saved {len(records)} transformed records to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save transformed data: {e}")
            raise
    
    def get_latest_file(self, stage: str, service_name: str, data_type: str = None) -> str:
        """Get the latest file for a given stage and service.
        
        Args:
            stage: Pipeline stage ('01_raw', '02_extracted', '03_transformed')
            service_name: Name of the service
            data_type: Type of data (optional for raw stage)
            
        Returns:
            Path to latest file, or None if not found
        """
        stage_dir = self.base_dir / stage
        
        if not stage_dir.exists():
            return None
        
        # Build pattern based on stage
        if stage == "01_raw":
            pattern = f"{service_name}_raw_*.json"
        else:
            if data_type:
                pattern = f"{service_name}_{data_type}_*.csv"
            else:
                pattern = f"{service_name}_*.csv"
        
        # Find matching files
        matching_files = list(stage_dir.glob(pattern))
        
        if not matching_files:
            return None
        
        # Return the most recent file
        latest_file = max(matching_files, key=os.path.getmtime)
        return str(latest_file)
