"""Nutrition data service for handling CSV-based nutrition data.

This module provides a service for interacting with nutrition data from CSV files,
following the same architectural patterns as other API services in the system.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional

from .base import BaseAPIService
from ..clients.nutrition import NutritionClient


class NutritionService(BaseAPIService):
    """Service for nutrition data communication.
    
    This service provides a clean interface to nutrition data while delegating
    all actual file reading to the NutritionClient.
    """

    def __init__(self, data_dir: str = "data", filename: str = "dailysummary.csv"):
        """Initialize the NutritionService.

        Args:
            data_dir: Directory containing the nutrition CSV file
            filename: Name of the nutrition data CSV file
        """
        self.nutrition_client = NutritionClient(data_dir=data_dir, filename=filename)
        super().__init__(self.nutrition_client)
    
    def fetch_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Fetch nutrition data for the specified date range.
        
        This method follows the standard service interface used by all services.
        
        Args:
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            Dictionary containing nutrition data in the expected format
        """
        self.logger.info(f"Fetching nutrition data from {start_date} to {end_date}")
        
        try:
            # Use the client to get nutrition data
            nutrition_records = self.client.get_nutrition_data(start_date, end_date)
            
            # Return in the expected format for the pipeline
            return {"nutrition": nutrition_records}
            
        except Exception as e:
            self.logger.error(f"Error fetching nutrition data: {e}")
            return {"nutrition": []}
    
    def get_nutrition_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get nutrition data for the specified date range.
        
        This method is used by the fetch stage which expects datetime objects.
        
        Args:
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            Dictionary containing nutrition data in the expected format
        """
        # Convert datetime to date for the client
        start_dt = start_date.date() if hasattr(start_date, 'date') else start_date
        end_dt = end_date.date() if hasattr(end_date, 'date') else end_date
        
        return self.fetch_data(start_dt, end_dt)
