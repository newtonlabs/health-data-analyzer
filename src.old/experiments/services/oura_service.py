"""Oura API service for clean separation of concerns."""

from datetime import date, datetime, time
from typing import Dict, Any, Optional

from experiments.services.base_service import BaseAPIService
from experiments.clients.oura_client import OuraClient


class OuraService(BaseAPIService):
    """Service for Oura API communication.
    
    This service provides a clean interface to Oura data while delegating
    all actual API communication to the existing OuraClient.
    """

    def __init__(self):
        """Initialize the Oura service."""
        self.oura_client = OuraClient()
        super().__init__(self.oura_client)

    def get_activity_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get activity data for a date range.

        Args:
            start_date: Start datetime for data collection
            end_date: End datetime for data collection

        Returns:
            Raw API response containing activity data
        """
        return self.oura_client.get_activity_data(start_date, end_date)

    def get_resilience_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get resilience data for a date range.

        Args:
            start_date: Start datetime for data collection
            end_date: End datetime for data collection

        Returns:
            Raw API response containing resilience data
        """
        return self.oura_client.get_resilience_data(start_date, end_date)

    def get_workouts_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get workouts data for a date range.

        Args:
            start_date: Start datetime for data collection
            end_date: End datetime for data collection

        Returns:
            Raw API response containing workouts data
        """
        return self.oura_client.get_workouts(start_date, end_date)

    def fetch_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Fetch all available Oura data for the specified date range.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            Dictionary containing all Oura data types
        """
        if not start_date or not end_date:
            raise ValueError("Both start_date and end_date are required for Oura API")
        
        # Convert dates to datetime objects
        start_datetime, end_datetime = self.convert_dates_to_datetime(start_date, end_date)
        
        # Fetch all data types
        data = {}
        
        data['activity'] = self.get_activity_data(start_datetime, end_datetime)
        self.log_api_call('activity', {'start': start_date, 'end': end_date}, 
                        len(data['activity'].get('data', [])))
        
        data['resilience'] = self.get_resilience_data(start_datetime, end_datetime)
        self.log_api_call('resilience', {'start': start_date, 'end': end_date}, 
                        len(data['resilience'].get('data', [])))
        
        data['workouts'] = self.get_workouts_data(start_datetime, end_datetime)
        self.log_api_call('workouts', {'start': start_date, 'end': end_date}, 
                        len(data['workouts'].get('data', [])))
        
        return data
