"""Experimental Whoop API client using authlib for OAuth2 authentication."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict

from auth_base import AuthlibOAuth2Client


class WhoopClientExperimental(AuthlibOAuth2Client):
    """Experimental Whoop API client using authlib."""

    def __init__(self):
        """Initialize the Whoop client.
        
        Reads WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET from environment.
        """
        super().__init__(
            env_client_id="WHOOP_CLIENT_ID",
            env_client_secret="WHOOP_CLIENT_SECRET",
            token_file="~/.whoop_tokens_experimental.json",
            base_url="https://api.prod.whoop.com/developer",
            authorization_endpoint="https://api.prod.whoop.com/oauth/oauth2/auth",
            token_endpoint="https://api.prod.whoop.com/oauth/oauth2/token",
            scopes=[
                "read:recovery",
                "read:cycles", 
                "read:sleep",
                "read:workout",
                "read:profile",
                "offline"
            ]
        )

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
