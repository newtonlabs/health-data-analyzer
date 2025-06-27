"""Oura API service for clean separation of concerns."""

from datetime import date, datetime, time
from typing import Optional, Dict, Any

from src.api.services.base_service import BaseAPIService
from src.api.clients.oura_client import OuraClient


class OuraService(BaseAPIService):
    """Service for Oura API communication.
    
    This service provides a clean interface to Oura data while delegating
    all actual API communication to the existing OuraClient.
    """

    def __init__(
        self,
        personal_access_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_file: str = None,
    ):
        """Initialize the Oura service.

        Args:
            personal_access_token: Optional personal access token
            client_id: Optional client ID for OAuth2
            client_secret: Optional client secret for OAuth2
            token_file: Optional path to token storage file
        """
        self.oura_client = OuraClient(
            personal_access_token=personal_access_token,
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file
        )
        super().__init__(self.oura_client)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.oura_client.is_authenticated()

    def get_activity_data(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get activity data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing activity data
        """
        return self.oura_client.get_activity_data(start_date, end_date)

    def get_resilience_data(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get resilience data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing resilience data
        """
        return self.oura_client.get_resilience_data(start_date, end_date)

    def get_workouts_data(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get workouts data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing workout data
        """
        return self.oura_client.get_workouts(start_date, end_date)
