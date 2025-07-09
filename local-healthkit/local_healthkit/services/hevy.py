"""Hevy API service for interacting with workout data.

This module provides a service for interacting with the Hevy API, which uses
API key authentication rather than OAuth. Despite this difference, the service
follows the same architectural patterns as other API services in the system.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional

from .base import BaseAPIService
from ..clients.hevy import HevyClient


class HevyService(BaseAPIService):
    """Service for Hevy API communication.
    
    This service provides a clean interface to Hevy data while delegating
    all actual API communication to the existing HevyClient.
    """

    def __init__(self, page_size: Optional[int] = None):
        """Initialize the HevyService.

        Args:
            page_size: Optional page size for workout pagination
        """
        self.hevy_client = HevyClient(page_size=page_size)
        super().__init__(self.hevy_client)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.
        
        Returns:
            True if API key is available, False otherwise
        """
        return self.hevy_client.is_authenticated()

    def get_workouts_data(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Get workouts data from Hevy API.

        Args:
            start_date: Start date for filtering (applied client-side)
            end_date: End date for filtering (applied client-side)
            page_size: Number of workouts per page

        Returns:
            Raw API response containing workout data
        """
        return self.hevy_client.get_workouts(start_date, end_date, page_size)

    def get_workout_details(self, workout_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific workout.
        
        Args:
            workout_id: ID of the workout to fetch
            
        Returns:
            Dictionary containing detailed workout data
        """
        return self.hevy_client.get_workout_details(workout_id)



    def fetch_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Fetch all available Hevy data for the specified date range.
        
        Args:
            start_date: Start date for data collection (optional for Hevy)
            end_date: End date for data collection (optional for Hevy)
            
        Returns:
            Dictionary containing all Hevy data types
        """
        # Convert dates to datetime objects if provided
        start_datetime = None
        end_datetime = None
        if start_date and end_date:
            start_datetime, end_datetime = self.convert_dates_to_datetime(start_date, end_date)
        
        # Fetch all data types
        data = {}
        
        data['workouts'] = self.get_workouts_data(start_datetime, end_datetime, page_size=10)
        self.log_api_call('workouts', {'start': start_date, 'end': end_date}, 
                        len(data['workouts'].get('workouts', [])))
        

        
        return data
