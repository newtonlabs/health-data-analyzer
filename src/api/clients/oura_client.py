"""Oura Ring API client for fetching health data using OAuth2."""

import json
import os
from datetime import datetime, timedelta
from typing import Any

import requests

from src.utils.api_client import APIClient, APIClientError
from src.utils.date_utils import DateFormat, DateUtils
from src.utils.logging_utils import HealthLogger


class OuraClient(APIClient):
    def __init__(
        self,
        personal_access_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_file: str = None,
    ):
        """Initialize the Oura client.

        Args:
            personal_access_token: Optional personal access token
            client_id: Optional client ID. If not provided, will look for OURA_CLIENT_ID in environment.
            client_secret: Optional client secret. If not provided, will look for OURA_CLIENT_SECRET in environment.
            token_file: Optional path to token storage file.

        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        # Try personal access token first
        self.personal_access_token = personal_access_token or os.getenv("OURA_API_KEY")
        if self.personal_access_token:
            # Initialize with dummy values for OAuth parameters since we're using personal token
            super().__init__(
                client_id="dummy",
                client_secret="dummy", 
                env_client_id="OURA_DUMMY_ID",
                env_client_secret="OURA_DUMMY_SECRET",
                default_token_path="~/.oura_dummy_tokens.json",
                base_url="https://api.ouraring.com/v2",
            )
            self.access_token = self.personal_access_token
            self.token_type = "Bearer"
            self.expires_in = 0  # Personal tokens don't expire
            self.refresh_token = None
            return

        # Fall back to OAuth2 if no personal token
        client_id = client_id or os.getenv("OURA_CLIENT_ID")
        client_secret = client_secret or os.getenv("OURA_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError(
                "Either personal access token or client ID/secret are required"
            )

        # Initialize base class with OAuth2 parameters
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file,
            env_client_id="OURA_CLIENT_ID",
            env_client_secret="OURA_CLIENT_SECRET", 
            default_token_path="~/.oura_tokens.json",
            base_url="https://api.ouraring.com/v2",
        )

    def get_token(self, code: str, state: str) -> None:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback, must match the one we sent

        Raises:
            APIClientError: If token exchange fails or state doesn't match
        """
        if state != self.state:
            raise APIClientError("State parameter doesn't match. Possible CSRF attack.")

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
            raise APIClientError(f"Failed to get access token: {str(e)}")

    def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.

        Raises:
            APIClientError: If refresh fails or no refresh token is available
        """
        if not self.refresh_token:
            raise APIClientError("No refresh token available")

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
            raise APIClientError(f"Failed to refresh access token: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if we have valid authentication.

        Returns:
            True if we have either a personal access token or valid OAuth tokens
        """
        if self.personal_access_token:
            return True
        # Use base class authentication check for OAuth2
        return super().is_authenticated()

    def _get_access_token(self) -> str:
        """Get a valid access token for API requests.
        
        Returns:
            str: A valid access token
            
        Raises:
            APIClientError: If unable to obtain a valid token
        """
        if self.personal_access_token:
            return self.personal_access_token
        # Use base class implementation for OAuth2
        return super()._get_access_token()

    def get_activity_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get activity data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary containing activity data
        """
        # Add one day to end_date to ensure we get the full day
        api_end_date = end_date + timedelta(days=1)
        
        return self._make_request(
            endpoint="usercollection/daily_activity",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": api_end_date.strftime("%Y-%m-%d"),
            },
        )

    def get_resilience_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get resilience data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary containing resilience data
        """
        return self._make_request(
            endpoint="usercollection/daily_resilience",
            params={
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

        return self._make_request(
            endpoint="usercollection/workout",
            params=params,
        )
