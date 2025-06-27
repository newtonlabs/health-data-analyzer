"""Withings API service for handling data retrieval."""

from datetime import datetime
from typing import Any, Dict, Optional

from src.api.services.base_service import BaseAPIService


class WithingsService(BaseAPIService):
    """Service for Withings API communication.
    
    This service provides a clean interface to Withings data while delegating
    all actual API communication to the existing WithingsClient.
    """

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        token_file: str = None,
    ):
        """Initialize the Withings service.

        Args:
            client_id: Optional client ID
            client_secret: Optional client secret
            token_file: Optional path to token storage file
        """
        from src.api.clients.withings_client import WithingsClient
        
        self.withings_client = WithingsClient(
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file
        )
        super().__init__(self.withings_client)

    def get_weight_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get weight data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing weight data
        """
        return self.withings_client.get_weight_data(start_date, end_date)
