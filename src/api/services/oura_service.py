"""Oura Ring API service for fetching health data using OAuth2."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.api.services.base_service import BaseAPIService
from src.utils.token_manager import TokenManager


class OuraError(Exception):
    """Custom exception for Oura API errors."""
    pass


class OuraService(BaseAPIService):
    """Service for interacting with the Oura Ring API."""
    
    def __init__(
        self,
        personal_access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_file: Optional[str] = None,
    ):
        """Initialize the Oura service.

        Args:
            personal_access_token: Optional personal access token. If not provided, will look for OURA_API_KEY in environment.
            client_id: Optional client ID. If not provided, will look for OURA_CLIENT_ID in environment.
            client_secret: Optional client secret. If not provided, will look for OURA_CLIENT_SECRET in environment.
            token_file: Optional path to token storage file.

        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        super().__init__(
            base_url="https://api.ouraring.com/v2",
            service_name="oura"
        )
        
        # Initialize token-related attributes
        self.personal_access_token = None
        self.client_id = None
        self.client_secret = None
        self.token_manager = None
        
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
        if state != getattr(self, 'state', None):
            raise OuraError("State parameter doesn't match. Possible CSRF attack.")

        try:
            response = self._make_request(
                method="POST",
                url="https://api.ouraring.com/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                use_base_url=False
            )

            # Store tokens
            self.access_token = response["access_token"]
            self.refresh_token = response["refresh_token"]
            self.token_type = response["token_type"]
            self.expires_in = response["expires_in"]

            # Save tokens to file
            if self.token_manager:
                self.token_manager.save_tokens({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                })

        except Exception as e:
            raise OuraError(f"Failed to exchange code for token: {str(e)}")

    def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.

        Raises:
            OuraError: If token refresh fails
        """
        if not self.refresh_token:
            raise OuraError("No refresh token available")

        try:
            response = self._make_request(
                method="POST",
                url="https://api.ouraring.com/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                use_base_url=False
            )

            # Update tokens
            self.access_token = response["access_token"]
            if "refresh_token" in response:
                self.refresh_token = response["refresh_token"]
            self.token_type = response["token_type"]
            self.expires_in = response["expires_in"]

            # Save updated tokens
            if self.token_manager:
                self.token_manager.save_tokens({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                })

        except Exception as e:
            raise OuraError(f"Failed to refresh token: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return bool(self.access_token)

    def _prepare_request_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests.
        
        Returns:
            Dictionary of headers to include in requests
        """
        # Skip token refresh for personal access tokens
        if not self.personal_access_token and self.token_manager:
            # Check if we need to refresh the token
            if self.token_manager.is_token_expired():
                try:
                    self.refresh_access_token()
                except OuraError:
                    raise OuraError(
                        "Token expired and refresh failed. Please authenticate again."
                    )

        return {
            "Authorization": f"{self.token_type} {self.access_token}",
            "Content-Type": "application/json",
        }

    def get_activity_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Fetch activity data for a date range.
        
        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch
            
        Returns:
            Dictionary containing activity data
        """
        # Add one day to end_date to ensure we get the full day
        api_end_date = end_date + timedelta(days=1)
        return self._make_request(
            method="GET",
            endpoint="usercollection/daily_activity",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": api_end_date.strftime("%Y-%m-%d"),
            },
        )

    def get_resilience_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Fetch resilience data for a date range.

        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            Dictionary containing resilience data
        """
        return self._make_request(
            method="GET",
            endpoint="usercollection/daily_resilience",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
        )

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

        return self._make_request(
            method="GET",
            endpoint="usercollection/workout", 
            params=params
        )
