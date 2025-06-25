"""Whoop API service for clean separation of concerns."""

from datetime import date, datetime
from typing import Optional, Dict, Any

from src.api.services.base_service import BaseAPIService
from src.api.clients.whoop_client import WhoopClient


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
        """Get workouts data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            limit: Maximum number of workouts to return

        Returns:
            Raw API response containing workout data
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
