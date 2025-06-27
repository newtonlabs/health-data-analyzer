"""Oura API service for clean separation of concerns."""

from datetime import date, datetime, time
from typing import Dict, Any

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

    def get_activity_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get activity data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing activity data
        """
        # Convert date to datetime for client
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        return self.oura_client.get_activity_data(start_dt, end_dt)

    def get_resilience_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get resilience data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing resilience data
        """
        # Convert date to datetime for client
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        return self.oura_client.get_resilience_data(start_dt, end_dt)

    def get_workouts_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get workouts data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing workouts data
        """
        # Convert date to datetime for client
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        return self.oura_client.get_workouts(start_dt, end_dt)
