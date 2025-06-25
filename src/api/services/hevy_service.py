"""Hevy API service for interacting with workout data.

This module provides a service for interacting with the Hevy API, which uses
API key authentication rather than OAuth. Despite this difference, the service
follows the same architectural patterns as other API services in the system.
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from src.api.services.base_service import BaseAPIService
from src.api.clients.hevy_client import HevyClient
from src.app_config import AppConfig


class HevyService(BaseAPIService):
    """Service for Hevy API communication.
    
    This service provides a clean interface to Hevy data while delegating
    all actual API communication to the existing HevyClient.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the HevyService.

        Args:
            api_key: Optional API key for the Hevy API
        """
        self.hevy_client = HevyClient(api_key=api_key)
        super().__init__(self.hevy_client)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.
        
        Returns:
            True if API key is available, False otherwise
        """
        return self.hevy_client.is_authenticated()

    def get_workouts_data(self, page_size: int = 10) -> Dict[str, Any]:
        """Get workouts data from Hevy API.

        Args:
            page_size: Number of workouts per page

        Returns:
            Raw API response containing workout data
        """
        return self.hevy_client.get_workouts(page_size=page_size)
