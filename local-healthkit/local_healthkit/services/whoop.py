"""Whoop API service for clean separation of concerns."""

from datetime import date, datetime
from typing import Optional, Dict, Any

from .base import BaseAPIService
from ..clients.whoop import WhoopClient


class WhoopService(BaseAPIService):
    """Service for Whoop API communication.
    
    This service provides a clean interface to Whoop data while delegating
    all actual API communication to the existing WhoopClient.
    """
    
    def __init__(self):
        """Initialize the Whoop service."""
        self.whoop_client = WhoopClient()
        super().__init__(self.whoop_client)
    
    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.whoop_client.is_authenticated()
    
    def get_workouts_data(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Get workouts data for a date range with automatic pagination.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            limit: Maximum number of workouts per API call (default: 25)

        Returns:
            Raw API response containing all workout data across all pages
        """
        return self.whoop_client.get_workouts(start_date, end_date, limit)

    def get_recovery_data(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get recovery data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing recovery data
        """
        return self.whoop_client.get_recovery_data(start_date, end_date)

    def get_sleep_data(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get sleep data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing sleep data
        """
        return self.whoop_client.get_sleep(start_date, end_date)

    def get_cycles_data(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get cycle data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing cycle data
        """
        return self.whoop_client.get_cycles(start_date, end_date)

    def fetch_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Fetch all available Whoop data for the specified date range.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            Dictionary containing all Whoop data types
        """
        if not start_date or not end_date:
            raise ValueError("Both start_date and end_date are required for Whoop API")
        
        # Convert dates to datetime objects
        start_datetime, end_datetime = self.convert_dates_to_datetime(start_date, end_date)
        
        # Fetch all data types
        data = {}
        
        data['workouts'] = self.get_workouts_data(start_datetime, end_datetime)
        self.log_api_call('workouts', {'start': start_date, 'end': end_date}, 
                        len(data['workouts'].get('records', [])))
        
        data['recovery'] = self.get_recovery_data(start_datetime, end_datetime)
        self.log_api_call('recovery', {'start': start_date, 'end': end_date}, 
                        len(data['recovery'].get('records', [])))
        
        data['sleep'] = self.get_sleep_data(start_datetime, end_datetime)
        self.log_api_call('sleep', {'start': start_date, 'end': end_date}, 
                        len(data['sleep'].get('records', [])))
        
        data['cycles'] = self.get_cycles_data(start_datetime, end_datetime)
        self.log_api_call('cycles', {'start': start_date, 'end': end_date}, 
                        len(data['cycles'].get('records', [])))
        
        return data
