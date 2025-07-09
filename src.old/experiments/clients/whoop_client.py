"""Whoop API client using authlib for OAuth2 authentication."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict

from .oauth2_auth_base import (
    OAuth2AuthBase, 
    TokenFileManager, 
    SlidingWindowValidator
)
from .config import ClientFactory


class WhoopClient(OAuth2AuthBase):
    """Whoop API client using authlib with shared utilities."""

    def __init__(self):
        """Initialize the Whoop client.
        
        Reads WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET from environment.
        Uses shared utilities for configuration and token management.
        """
        # Initialize shared utilities
        self.token_manager = TokenFileManager("whoop")
        self.sliding_window = SlidingWindowValidator()
        
        # Get service configuration
        service_config = ClientFactory.get_service_config("whoop")
        
        super().__init__(
            env_client_id="WHOOP_CLIENT_ID",
            env_client_secret="WHOOP_CLIENT_SECRET",
            token_file="~/.whoop_tokens.json",
            base_url=service_config["base_url"],
            authorization_endpoint=service_config["auth_url"],
            token_endpoint=service_config["token_url"],
            scopes=service_config["scopes"]
        )

    def get_token_status(self) -> dict:
        """Get token status using shared utilities.
        
        Returns:
            Dictionary with token status information
        """
        token_data = self.token_manager.load_token()
        if not token_data:
            return {"status": "no_token", "days_remaining": 0}
        
        is_valid = self.sliding_window.is_in_sliding_window(token_data)
        days_remaining = self.sliding_window.get_days_remaining(token_data)
        should_refresh = self.sliding_window.should_refresh_proactively(
            token_data, self.config.refresh_buffer_hours
        )
        
        return {
            "status": "valid" if is_valid else "expired",
            "days_remaining": days_remaining,
            "should_refresh": should_refresh,
            "sliding_window_valid": is_valid
        }

    def clear_stored_token(self) -> None:
        """Clear stored token using shared utilities."""
        self.token_manager.clear_token()
        self.token = None
        if hasattr(self.session, 'token'):
            self.session.token = None

    def _paginated_request(
        self, 
        endpoint: str, 
        start_date: datetime, 
        end_date: datetime, 
        limit: int = 25,
        adjust_end_date: bool = True
    ) -> dict[str, Any]:
        """Generic pagination handler for Whoop API endpoints.
        
        Args:
            endpoint: API endpoint (e.g., "v1/recovery")
            start_date: Start date for data
            end_date: End date for data
            limit: Max records per page
            adjust_end_date: Whether to add 1 day to end_date (required by some endpoints)
            
        Returns:
            Dictionary with all paginated records
        """
        # Adjust end date if required by endpoint
        api_end = end_date + timedelta(days=1) if adjust_end_date else end_date
        
        all_records = []
        next_token = None
        page_count = 0
        
        while True:
            page_count += 1
            params = {
                "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": api_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": limit,
            }
            
            if next_token:
                params["nextToken"] = next_token
            
            response = self.make_request(endpoint, params=params)
            data = response.json()
            
            records = data.get("records", [])
            all_records.extend(records)
            
            # Check if there are more pages
            next_token = data.get("next_token")
            if not next_token:
                break
        
        return {
            "records": all_records,
            "next_token": None
        }

    def get_recovery_data(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Fetch recovery data for a date range with automatic pagination.
        
        Args:
            start_date: Start date for recovery data
            end_date: End date for recovery data
            
        Returns:
            Dictionary containing recovery data with pagination
        """
        return self._paginated_request("v1/recovery", start_date, end_date)
    
    def get_recovery(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get recovery data for a specified time range.

        Args:
            start_date: Start date for recovery data
            end_date: End date for recovery data

        Returns:
            Dict containing recovery data
        """
        return self._paginated_request("v1/recovery", start_date, end_date)

    def get_workouts(
        self, start_date: datetime, end_date: datetime, limit: int = 25
    ) -> dict[str, Any]:
        """Get workouts for a date range with automatic pagination.

        Args:
            start_date: Start date
            end_date: End date
            limit: Max number of workouts per page

        Returns:
            Dictionary containing all workout data across pages
        """
        return self._paginated_request(
            "v1/activity/workout", start_date, end_date, limit, adjust_end_date=False
        )

    def get_sleep(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get sleep data for a specified time range.

        Args:
            start_date: Start date for sleep data
            end_date: End date for sleep data

        Returns:
            Dict containing sleep data
        """
        return self._paginated_request("v2/activity/sleep", start_date, end_date)

    def get_cycles(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get physiological cycle data for a specified time range.

        Args:
            start_date: Start date for cycle data
            end_date: End date for cycle data

        Returns:
            Dict containing cycle data
        """
        return self._paginated_request("v1/cycle", start_date, end_date)
