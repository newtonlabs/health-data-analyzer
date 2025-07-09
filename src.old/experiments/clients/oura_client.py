"""
Oura Ring API client using the APIKeyClient base class.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from .api_key_auth_base import APIKeyAuthBase
from .config import ClientFactory


class OuraClient(APIKeyAuthBase):
    """Oura Ring API client using personal access token authentication."""
    
    def __init__(self):
        """Initialize the Oura client.
        
        Reads OURA_API_KEY from environment variables.
        """
        # Get service configuration
        service_config = ClientFactory.get_service_config("oura")
        
        super().__init__(
            env_api_key="OURA_API_KEY",
            base_url=service_config["base_url"]
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Oura API requests.
        
        Oura uses Bearer token format in the Authorization header.
        
        Returns:
            Dictionary of headers for authentication
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json"
        }
    
    def get_activity_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get activity data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary containing activity data
        """
        # Add one day to end_date to ensure we get the full day
        api_end_date = end_date + timedelta(days=1)
        
        response = self.make_request(
            endpoint="usercollection/daily_activity",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": api_end_date.strftime("%Y-%m-%d"),
            },
        )
        return response.json()

    def get_resilience_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get resilience data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary containing resilience data
        """
        response = self.make_request(
            endpoint="usercollection/daily_resilience",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
        )
        return response.json()

    def get_workouts(
        self, 
        start: Optional[datetime] = None, 
        end: Optional[datetime] = None, 
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get workouts collection.

        Args:
            start: Optional start time for workouts
            end: Optional end time for workouts
            limit: Optional limit on number of workouts to return

        Returns:
            Dictionary containing workout data
        """
        params = {}
        if start:
            params["start_date"] = start.strftime("%Y-%m-%d")
        if end:
            params["end_date"] = end.strftime("%Y-%m-%d")
        if limit:
            params["limit"] = limit

        response = self.make_request(
            endpoint="usercollection/workout",
            params=params,
        )
        return response.json()

    def get_personal_info(self) -> Dict[str, Any]:
        """Get personal information from Oura API.
        
        Returns:
            Dictionary containing personal information
        """
        response = self.make_request(endpoint="usercollection/personal_info")
        return response.json()

    def get_sleep_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get sleep data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary containing sleep data
        """
        response = self.make_request(
            endpoint="usercollection/daily_sleep",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
        )
        return response.json()

    def get_readiness_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get readiness data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary containing readiness data
        """
        response = self.make_request(
            endpoint="usercollection/daily_readiness",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
        )
        return response.json()
