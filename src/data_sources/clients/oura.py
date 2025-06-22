"""Oura Ring API client for fetching health data using OAuth2."""

import json
import os
from datetime import datetime, timedelta
from typing import Any

import requests

from src.utils.date_utils import DateFormat, DateUtils
from src.utils.file_utils import save_json_to_file
from src.utils.logging_utils import HealthLogger

from src.data_sources.token_manager import TokenManager


class OuraError(Exception):
    """Custom exception for Oura API errors."""

    pass


class OuraClient:
    def __init__(
        self,
        personal_access_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_file: str = None,
    ):
        """Initialize the Oura client.

        Args:
            client_id: Optional client ID. If not provided, will look for OURA_CLIENT_ID in environment.
            client_secret: Optional client secret. If not provided, will look for OURA_CLIENT_SECRET in environment.
            token_file: Optional path to token storage file.

        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        # Set up API configuration
        self.base_url = "https://api.ouraring.com/v2"
        self.access_token = None
        self.token_type = None
        self.expires_in = 0
        self.refresh_token = None
        self.state = None

        # Set up logging
        self.logger = HealthLogger(__name__)

        # Try personal access token first
        self.personal_access_token = personal_access_token or os.getenv("OURA_API_KEY")
        if self.personal_access_token:
            self.access_token = self.personal_access_token
            self.token_type = "Bearer"
            self.expires_in = 0  # Personal tokens don't expire
            self.refresh_token = None
            return

        # Fall back to OAuth2 if no personal token
        self.client_id = client_id or os.getenv("OURA_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("OURA_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Either personal access token or client ID/secret are required"
            )

        # Set up token storage
        self.token_manager = TokenManager(
            token_file or os.path.expanduser("~/.oura_tokens.json")
        )

        # Try to load existing tokens
        saved_tokens = self.token_manager.get_tokens()
        if saved_tokens:
            self.access_token = saved_tokens.get("access_token")
            self.refresh_token = saved_tokens.get("refresh_token")
            self.token_type = saved_tokens.get("token_type")
            self.expires_in = saved_tokens.get("expires_in", 0)

    def get_token(self, code: str, state: str) -> None:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback, must match the one we sent

        Raises:
            OuraError: If token exchange fails or state doesn't match
        """
        if state != self.state:
            raise OuraError("State parameter doesn't match. Possible CSRF attack.")

        try:
            response = requests.post(
                "https://api.ouraring.com/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://localhost:8080/callback",
                },
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_type = token_data.get("token_type", "Bearer")
            self.expires_in = token_data.get("expires_in", 0)
            self.refresh_token = token_data.get("refresh_token")

            # Save tokens
            self.token_manager.save_tokens(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                }
            )
        except requests.exceptions.RequestException as e:
            raise OuraError(f"Failed to get access token: {str(e)}")

    def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.

        Raises:
            OuraError: If refresh fails or no refresh token is available
        """
        if not self.refresh_token:
            raise OuraError("No refresh token available")

        try:
            response = requests.post(
                "https://api.ouraring.com/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)
            self.token_type = token_data.get("token_type", "Bearer")
            self.expires_in = token_data.get("expires_in", 0)

            # Save new tokens
            self.token_manager.save_tokens(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                }
            )

        except requests.exceptions.RequestException as e:
            raise OuraError(f"Failed to refresh access token: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if we have valid authentication.

        Returns:
            True if we have either a personal access token or both access and refresh tokens
        """
        if self.personal_access_token:
            return True
        return bool(self.access_token and self.refresh_token)

    def _make_request(
        self, endpoint: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Make a request to the Oura API.

        Args:
            endpoint: API endpoint to call
            params: Optional query parameters

        Returns:
            JSON response from API
        """
        # Skip token refresh for personal access tokens
        if not self.personal_access_token:
            # Check if we need to refresh the token
            if self.token_manager.is_token_expired():
                try:
                    self.refresh_access_token()
                except OuraError:
                    raise OuraError(
                        "Token expired and refresh failed. Please authenticate again."
                    )

        headers = {
            "Authorization": f"{self.token_type} {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}", headers=headers, params=params
            )
            response.raise_for_status()
            # Always log the JSON response when in debug mode
            response_data = response.json()

            # Save API response as JSON file
            save_json_to_file(
                response_data,
                f"oura-{endpoint.replace('/', '-')}",
                subdir="api-responses/oura",
            )
            return response_data
        except requests.exceptions.RequestException as e:
            raise OuraError(f"Failed to fetch data from Oura API: {str(e)}")

    def get_activity_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Fetch activity data for a date range."""
        # Add one day to end_date to ensure we get the full day
        api_end_date = end_date + timedelta(days=1)
        return self._make_request(
            "usercollection/daily_activity",
            {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": api_end_date.strftime("%Y-%m-%d"),
            },
        )

    def get_resilience_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Fetch resilience data for a date range.

        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            Dictionary containing resilience data
        """
        return self._make_request(
            "usercollection/daily_resilience",
            {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
        )

    def get_workouts(
        self, start: datetime = None, end: datetime = None, limit: int = None
    ) -> dict[str, Any]:
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

        return self._make_request("usercollection/workout", params)
