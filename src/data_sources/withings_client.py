"""Withings API client for handling OAuth2 authentication and data retrieval."""

import os
import secrets
from datetime import datetime, timedelta
from http.server import HTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from src.data_sources.base import APIClient, APIClientError, OAuthCallbackHandler
from src.utils.date_utils import DateFormat, DateUtils
from src.utils.file_utils import save_json_to_file
from src.utils.progress_indicators import ProgressIndicator


class WithingsCallbackHandler(OAuthCallbackHandler):
    """Handle OAuth callback from Withings."""

    def do_GET(self):
        """Handle OAuth callback from Withings.

        This method is called when Withings redirects back to our local server
        after the user approves access. The URL contains an authorization code
        that we exchange for an access token.
        """
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


class WithingsError(Exception):
    """Custom exception for Withings API errors."""

    pass


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
            base_url="https://wbsapi.withings.net"
        )
        
        # Withings-specific state
        self.state = None
        saved_tokens = self.token_manager.get_tokens()
        if saved_tokens:
            self.access_token = saved_tokens.get("access_token")
            self.refresh_token = saved_tokens.get("refresh_token")
            self.token_type = saved_tokens.get("token_type")
            self.expires_in = saved_tokens.get("expires_in", 0)

    def _make_request(
        self, endpoint: str, params: dict[str, Any] = None, method: str = "POST"
    ) -> dict[str, Any]:
        """Make a request to the Withings API.

        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            method: HTTP method (GET or POST)

        Returns:
            Dictionary containing response data

        Raises:
            WithingsError: If the request fails
        """
        # Ensure we have a valid token
        if not self.is_authenticated():
            if not self.refresh_access_token():
                raise WithingsError("Not authenticated and token refresh failed")

        # Build the URL and headers
        url = f"{self.base_url}/{endpoint}"
        headers = {
            # Force capital B for Bearer
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        # Make the request
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            else:  # POST
                response = requests.post(url, headers=headers, data=params)

            # Check for errors
            response.raise_for_status()
            data = response.json()

            # Save API response as JSON file
            save_json_to_file(
                data,
                f"withings-{endpoint.replace('/', '-')}",
                subdir="api-responses/withings",
            )

            # Withings API returns a status code in the response body
            if data.get("status") != 0:
                error_msg = data.get("error", "Unknown error")
                raise WithingsError(f"API error: {error_msg}")

            return data.get("body", {})
        except requests.exceptions.RequestException as e:
            # Try to refresh token if unauthorized
            if (
                hasattr(e, "response")
                and hasattr(e.response, "status_code")
                and e.response.status_code == 401
            ):
                if self.refresh_access_token():
                    # Retry the request
                    return self._make_request(endpoint, params, method)

            raise WithingsError(f"Request failed: {str(e)}")

    def get_weight_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get weight measurements for a specified time range.

        Args:
            start_date: Start date for weight data
            end_date: End date for weight data

        Returns:
            Dict containing weight measurements

        Raises:
            WithingsError: If the API call fails
            SystemExit: Stops execution if the API call fails
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()

        # Use dynamic date range from pipeline
        startdate = int(start_date.timestamp())
        enddate = int(end_date.timestamp())

        # Format parameters according to Withings API documentation
        # https://developer.withings.com/api-reference/#tag/measure/operation/measure-getmeas
        params = {
            "action": "getmeas",
            "meastype": 1,  # Weight measurement type (1)
            "category": 1,  # Real measurements (1)
            "startdate": startdate,
            "enddate": enddate,
        }

        try:
            result = self._make_request("measure", params, method="POST")

            return result
        except WithingsError as e:
            error_msg = f"Withings API error: {str(e)}"
            self.logger.warning(error_msg)
            # Use ProgressIndicator imported at the top
            ProgressIndicator.step_error(f"ERROR: {error_msg}")
            ProgressIndicator.bullet_item(
                "Pipeline execution stopped due to Withings API error."
            )
            import sys

            sys.exit(1)

    def authenticate(self) -> bool:
        """Authenticate with Withings using OAuth2 flow.

        Returns:
            bool: True if authentication was successful, False otherwise
        """
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
            WithingsError: If token exchange fails or state doesn't match
        """
        # Verify state parameter to prevent CSRF attacks
        if state != self.state:
            raise WithingsError("State parameter doesn't match")

        # Exchange code for token
        params = {
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": "http://localhost:8080/callback",
        }

        try:
            # Use the correct endpoint for token exchange
            response = requests.post(
                "https://wbsapi.withings.net/v2/oauth2", data=params
            )
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if data.get("status") != 0:
                error_msg = data.get("error", "Unknown error")
                raise WithingsError(f"Token exchange failed: {error_msg}")

            # Extract token data
            token_data = data.get("body", {})
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "Bearer")
            self.expires_in = token_data.get("expires_in", 0)

            # Save tokens
            self.token_manager.save_tokens(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                    "timestamp": datetime.now().timestamp(),
                }
            )

        except requests.exceptions.RequestException as e:
            raise WithingsError(f"Token exchange failed: {str(e)}")

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token.

        Returns:
            bool: True if refresh was successful, False otherwise

        Raises:
            WithingsError: If refresh fails or no refresh token is available
        """
        if not self.refresh_token:
            self.logger.warning("No refresh token available")
            return False

        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }

        try:
            response = requests.post(
                "https://wbsapi.withings.net/v2/oauth2", data=params
            )
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if data.get("status") != 0:
                error_msg = data.get("error", "Unknown error")
                self.logger.warning(f"Token refresh failed: {error_msg}")
                return False

            # Extract token data
            token_data = data.get("body", {})
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "Bearer")
            self.expires_in = token_data.get("expires_in", 0)

            # Save tokens
            self.token_manager.save_tokens(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                    "timestamp": datetime.now().timestamp(),
                }
            )

            return True
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Token refresh failed: {str(e)}")
            return False

    def is_authenticated(self) -> bool:
        """Check if we have valid authentication tokens.

        Returns:
            True if we have both access and refresh tokens
        """
        return bool(self.access_token and self.refresh_token)
