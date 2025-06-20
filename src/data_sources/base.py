"""Base class for data sources."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
import os
import pandas as pd

from src.utils.date_utils import DateUtils, DateFormat

class DataSource(ABC):
    def __init__(self, data_dir: str = 'data'):
        """Initialize data source.
        
        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def get_file_path(self, filename: str) -> str:
        """Get full path for a file."""
        return os.path.join(self.data_dir, filename)
    
    def get_dated_file_path(self, base_name: str, date: datetime) -> str:
        """Get path for a dated file."""
        return self.get_file_path(f"{DateUtils.format_date(date, DateFormat.STANDARD)}-{base_name}")
    
    @abstractmethod
    def load_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Load data for the specified date range.
        
        Args:
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            DataFrame with data for the specified range
        """
        pass
    
    def save_data(self, data: pd.DataFrame, filename: str) -> None:
        """Save data to file.
        
        Args:
            data: DataFrame to save
            filename: Name of file to save to
        """
        if data is not None:
            data.to_json(self.get_file_path(filename), orient='records')
    
    def save_raw_data(self, data: Dict[str, Any], source: str, date: datetime) -> None:
        """Save raw API response data to JSON.
        
        Args:
            data: Raw API response data
            source: Source identifier (e.g. 'whoop', 'oura')
            date: Date of the data
        """
        import json
        path = self.get_dated_file_path(f"{source}-raw.json", date)
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def load_raw_data(self, source: str, date: datetime) -> Optional[Dict[str, Any]]:
        """Load raw data from JSON if available.
        
        Args:
            source: Source identifier (e.g. 'whoop', 'oura')
            date: Date of the data
            
        Returns:
            Raw data dictionary if found, None otherwise
        """
        import json
        path = self.get_dated_file_path(f"{source}-raw.json", date)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None
