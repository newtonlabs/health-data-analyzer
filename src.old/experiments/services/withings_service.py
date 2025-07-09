"""Withings API service for clean separation of concerns."""

from datetime import date, datetime
from typing import Dict, Any, Optional

from experiments.services.base_service import BaseAPIService
from experiments.clients.withings_client import WithingsClient


class WithingsService(BaseAPIService):
    """Service for Withings API communication.
    
    This service provides a clean interface to Withings data while delegating
    all actual API communication to the existing WithingsClient.
    """

    def __init__(self):
        """Initialize the Withings service."""
        self.withings_client = WithingsClient()
        super().__init__(self.withings_client)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.withings_client.is_authenticated()

    def get_weight_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get weight data for a date range.

        Args:
            start_date: Start datetime for data collection
            end_date: End datetime for data collection

        Returns:
            Raw API response containing weight data
        """
        return self.withings_client.get_weight_data(start_date, end_date)

    def fetch_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Fetch all available Withings data for the specified date range.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            Dictionary containing all Withings data types
        """
        if not start_date or not end_date:
            raise ValueError("Both start_date and end_date are required for Withings API")
        
        # Convert dates to datetime objects
        start_datetime, end_datetime = self.convert_dates_to_datetime(start_date, end_date)
        
        # Fetch all data types
        data = {}
        
        data['weight'] = self.get_weight_data(start_datetime, end_datetime)
        self.log_api_call('weight', {'start': start_date, 'end': end_date}, 
                        len(data['weight'].get('measuregrps', [])))
        
        return data
