"""Withings API client for handling OAuth2 authentication and data retrieval."""

import os
import secrets
from datetime import datetime, timedelta
from http.server import HTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from src.app_config import AppConfig
from src.utils.api_client import APIClient, APIClientError, OAuthCallbackHandler
from src.utils.date_utils import DateFormat, DateUtils
from src.utils.progress_indicators import ProgressIndicator


class WithingsCallbackHandler(OAuthCallbackHandler):
    """Handle OAuth callback from Withings."""

    def do_GET(self):
        """Handle OAuth callback from Withings."""
        try:
            parsed_url = urlparse(self.path)
            query_components = parse_qs(parsed_url.query)

            if "code" in query_components and "state" in query_components:
                code = query_components["code"][0]
                state = query_components["state"][0]

                # Pass the code and state to the WithingsClient instance
                self.server.withings_client.get_token(code, state)
                self.server.authenticated = True
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authentication successful! You can close this window.</h1></body></html>"
                )
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authentication failed. No code received.</h1></body></html>"
                )
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error: {e}</h1></body></html>".encode())
        finally:
            # Signal the server to stop after handling the request
            self.server.should_stop = True


class WithingsClient(APIClient):
    """Client for interacting with the Withings API.

    This client handles:
    1. OAuth2 authentication with Withings
    2. Token management (refresh, storage)
    3. API requests for health data

    The client follows the OAuth2 flow and stores tokens using the TokenManager.
    """

    def __init__(
        self, client_id: str = None, client_secret: str = None, token_file: str = None
    ):
        """Initialize the Withings client.

        Args:
            client_id: Optional client ID. If not provided, will look for WITHINGS_CLIENT_ID in environment.
            client_secret: Optional client secret. If not provided, will look for WITHINGS_CLIENT_SECRET in environment.
            token_file: Optional path to token storage file.

        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        # Initialize base class
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file,
            env_client_id="WITHINGS_CLIENT_ID",
            env_client_secret="WITHINGS_CLIENT_SECRET",
            default_token_path="~/.withings_tokens.json",
            base_url="https://wbsapi.withings.net",
        )

        # Withings-specific state
        self.state = None
        
        # Load existing tokens (needed for Withings-specific authentication check)
        saved_tokens = self.token_manager.get_tokens()
        if saved_tokens:
            self.access_token = saved_tokens.get("access_token")
            self.refresh_token = saved_tokens.get("refresh_token")
            self.token_type = saved_tokens.get("token_type")
            self.expires_in = saved_tokens.get("expires_in", 0)

    def get_weight_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get weight measurements for a specified time range.

        Args:
            start_date: Start date for weight data
            end_date: End date for weight data

        Returns:
            Dict containing weight measurements and body composition data

        Raises:
            APIClientError: If the API call fails
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()

        # Use dynamic date range from pipeline
        startdate = int(start_date.timestamp())
        enddate = int(end_date.timestamp())

        # Format parameters according to Withings API documentation
        # https://developer.withings.com/api-reference/#tag/measure/operation/measure-getmeas
        # Request all body composition measurement types:
        # 1=weight, 6=body_fat_percentage, 76=muscle_mass, 88=bone_mass, 77=water_percentage
        meastype_values = [
            str(AppConfig.WITHINGS_MEASUREMENT_TYPE_WEIGHT),
            str(AppConfig.WITHINGS_MEASUREMENT_TYPE_FAT_RATIO),
            str(AppConfig.WITHINGS_MEASUREMENT_TYPE_MUSCLE_MASS),
            str(AppConfig.WITHINGS_MEASUREMENT_TYPE_BONE_MASS),
            str(AppConfig.WITHINGS_MEASUREMENT_TYPE_WATER_PERCENTAGE),
        ]
        
        params = {
            "action": "getmeas",
            "meastype": ",".join(meastype_values),  # All body composition measurement types
            "category": 1,  # Real measurements (1)
            "startdate": startdate,
            "enddate": enddate,
        }

        return self._make_request(
            endpoint="measure",
            params=params,
            method="POST",
        )

    def authenticate(self) -> bool:
        """Authenticate with Withings using OAuth2 flow.

        Returns:
            bool: True if authentication was successful, False otherwise
        """
        # Use the base class handle_authentication method which handles token refresh and clearing
        # If it returns True, authentication was successful
        if super().handle_authentication():
            return True

        # If the base class authentication failed, continue with Withings-specific authentication

        # Generate a random state parameter for security
        self.state = secrets.token_urlsafe(32)

        # Get the authorization URL
        auth_url = self._get_auth_url()

        # Print the URL for the user to visit
        # Use ProgressIndicator imported at the top
        ProgressIndicator.bullet_item(
            f"[Withings Auth] Please visit this URL to authorize the application: {auth_url}"
        )

        # Start a local server to receive the callback
        server_address = ("localhost", 8080)
        httpd = HTTPServer(server_address, WithingsCallbackHandler)
        httpd.withings_client = self
        httpd.authenticated = False
        httpd.should_stop = False

        try:
            # Wait for the callback
            while not httpd.should_stop:
                httpd.handle_request()

            return httpd.authenticated
        finally:
            httpd.server_close()

    def _get_auth_url(self) -> str:
        """Get the URL for OAuth2 authorization.

        Returns:
            URL to redirect user for authorization
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "state": self.state,
            "scope": "user.metrics,user.activity,user.sleepevents",
            "redirect_uri": "http://localhost:8080/callback",
        }

        return (
            f"https://account.withings.com/oauth2_user/authorize2?{urlencode(params)}"
        )

    def get_token(self, code: str, state: str) -> None:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback, must match the one we sent

        Raises:
            APIClientError: If token exchange fails or state doesn't match
        """
        # Prepare token parameters for Withings
        token_params = {
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": "http://localhost:8080/callback",
        }

        # Withings has a different response format, so we need to handle it specially
        try:
            # Verify state parameter to prevent CSRF attacks
            if state != self.state:
                raise APIClientError("State parameter doesn't match")

            # Use the correct endpoint for token exchange
            response = requests.post(
                "https://wbsapi.withings.net/v2/oauth2", data=token_params
            )
            response.raise_for_status()
            data = response.json()

            # Check for errors in Withings-specific format
            if data.get("status") != 0:
                error_msg = data.get("error", "Unknown error")
                raise APIClientError(f"Token exchange failed: {error_msg}")

            # Extract token data from Withings-specific format
            token_data = data.get("body", {})

            # Save tokens and update instance variables
            self.token_manager.save_tokens(
                {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "expires_in": token_data.get("expires_in", 0),
                    "timestamp": datetime.now().timestamp(),
                }
            )

            # Update instance variables
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "Bearer")
            self.expires_in = token_data.get("expires_in", 0)

        except requests.exceptions.RequestException as e:
            raise APIClientError(f"Token exchange failed: {str(e)}")

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token.

        Returns:
            bool: True if refresh was successful, False otherwise
        """
        if not self.refresh_token:
            self.logger.warning("No refresh token available for Withings")
            return False

        self.logger.debug("Refreshing Withings access token")
        
        params = {
            "action": "requesttoken",  # Required action parameter
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }

        try:
            response = requests.post(
                "https://wbsapi.withings.net/v2/oauth2", data=params
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                self.logger.warning(f"Withings token refresh failed with status {response.status_code}: {response.text}")
                return False
                
            data = response.json()

            # Check for API errors
            if data.get("status") != 0:
                error_msg = data.get("error", "Unknown error")
                error_code = data.get("error_code", "Unknown code")
                self.logger.warning(f"Withings token refresh failed: {error_msg} (code: {error_code})")
                return False

            # Extract token data
            token_data = data.get("body", {})
            
            # Validate the response contains required fields
            if "access_token" not in token_data or "refresh_token" not in token_data:
                self.logger.warning(f"Invalid token response from Withings: missing required fields")
                return False
                
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "Bearer")
            
            # Use base class helper method to calculate extended expiration
            original_expires_in = token_data.get("expires_in", 3600)
            extended_expires_in, validity_days = self.get_extended_expiration_seconds(original_expires_in)
            self.expires_in = extended_expires_in

            # Save tokens with extended expiration
            self.token_manager.save_tokens(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": self.token_type,
                    "expires_in": extended_expires_in,
                    "original_expires_in": original_expires_in,
                    "timestamp": datetime.now().timestamp(),
                    "last_refresh_time": datetime.now().isoformat(),  # For sliding window
                }
            )
            
            self.logger.debug(f"Successfully refreshed Withings token, extended validity to {validity_days} days")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to refresh Withings access token: {str(e)}")
            import traceback
            self.logger.debug(f"Withings token refresh error details: {traceback.format_exc()}")
            return False
