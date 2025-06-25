"""Withings API service for handling OAuth2 authentication and data retrieval."""

import os
import secrets
from datetime import datetime
from http.server import HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from src.api.services.base_service import BaseAPIService
from src.utils.api_client import OAuthCallbackHandler


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

                # Pass the code and state to the WithingsService instance
                self.server.withings_service.get_token(code, state)
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


class WithingsService(BaseAPIService):
    """Service for interacting with the Withings API.

    This service handles:
    1. OAuth2 authentication with Withings
    2. Token management (refresh, storage)
    3. API requests for health data

    The service follows the OAuth2 flow and stores tokens using the TokenManager.
    """

    def __init__(
        self, 
        client_id: Optional[str] = None, 
        client_secret: Optional[str] = None, 
        token_file: Optional[str] = None
    ):
        """Initialize the Withings service.

        Args:
            client_id: Optional client ID. If not provided, will look for WITHINGS_CLIENT_ID in environment.
            client_secret: Optional client secret. If not provided, will look for WITHINGS_CLIENT_SECRET in environment.
            token_file: Optional path to token storage file.

        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        super().__init__(
            base_url="https://wbsapi.withings.net",
            service_name="withings"
        )
        
        # Get credentials from parameters or environment
        self.client_id = client_id or os.getenv("WITHINGS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("WITHINGS_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Client ID and secret are required. Set WITHINGS_CLIENT_ID and WITHINGS_CLIENT_SECRET environment variables."
            )
        
        # Set up token storage
        from src.utils.token_manager import TokenManager
        self.token_manager = TokenManager(
            token_file or os.path.expanduser("~/.withings_tokens.json")
        )
        
        # Withings-specific state
        self.state = None
        
        # Try to load existing tokens
        saved_tokens = self.token_manager.get_tokens()
        if saved_tokens:
            self.access_token = saved_tokens.get("access_token")
            self.refresh_token = saved_tokens.get("refresh_token")
            self.token_type = saved_tokens.get("token_type")
            self.expires_in = saved_tokens.get("expires_in", 0)

    def _prepare_request_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests.
        
        Returns:
            Dictionary of headers to include in requests
        """
        # Check if we need to refresh the token
        if self.token_manager and self.token_manager.is_token_expired():
            try:
                self.refresh_access_token()
            except Exception:
                raise Exception(
                    "Token expired and refresh failed. Please authenticate again."
                )

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Make a request to the Withings API.

        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            method: HTTP method (GET or POST)

        Returns:
            Dictionary containing response data
        """
        headers = self._prepare_request_headers()
        
        if method.upper() == "POST":
            response = super()._make_request(
                method="POST",
                endpoint=endpoint,
                data=params,
                headers=headers
            )
        else:
            response = super()._make_request(
                method="GET",
                endpoint=endpoint,
                params=params,
                headers=headers
            )
        
        # Save API response as JSON file
        from src.utils.file_utils import save_json_to_file
        save_json_to_file(
            response,
            f"withings-{endpoint.replace('/', '-')}",
            subdir="api-responses/withings",
        )
        
        return response

    def get_weight_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get weight measurements for a specified time range.

        Args:
            start_date: Start date for weight data
            end_date: End date for weight data

        Returns:
            Dict containing weight measurements

        Raises:
            Exception: If the API call fails
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please authenticate first.")

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

        return self._make_request("measure", params, method="POST")

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return bool(self.access_token)

    def authenticate(self) -> bool:
        """Authenticate with Withings using OAuth2 flow.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Generate a random state for security
            self.state = secrets.token_urlsafe(32)

            # Set up OAuth2 parameters
            params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": "http://localhost:8080/callback",
                "scope": "user.metrics",
                "state": self.state,
            }

            # Create authorization URL
            auth_url = f"https://account.withings.com/oauth2_user/authorize2?{urlencode(params)}"

            self.logger.info("Opening browser for Withings authentication...")
            self.logger.info(f"If browser doesn't open, visit: {auth_url}")

            # Start local server to handle callback
            httpd = HTTPServer(("localhost", 8080), WithingsCallbackHandler)
            httpd.withings_service = self
            httpd.authenticated = False
            httpd.should_stop = False

            # Open browser
            import webbrowser
            webbrowser.open(auth_url)

            # Handle the callback
            while not httpd.should_stop:
                httpd.handle_request()

            return httpd.authenticated

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def get_token(self, code: str, state: str) -> None:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback, must match the one we sent

        Raises:
            Exception: If token exchange fails or state doesn't match
        """
        if state != self.state:
            raise Exception("State parameter doesn't match. Possible CSRF attack.")

        try:
            token_params = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": "http://localhost:8080/callback",
            }

            response = requests.post(
                "https://wbsapi.withings.net/v2/oauth2", data=token_params
            )
            response.raise_for_status()
            token_data = response.json()

            if token_data.get("status") != 0:
                raise Exception(f"Token exchange failed: {token_data}")

            # Extract token information
            body = token_data.get("body", {})
            self.access_token = body.get("access_token")
            self.refresh_token = body.get("refresh_token")
            self.token_type = "Bearer"
            self.expires_in = body.get("expires_in", 3600)

            # Save tokens
            self.token_manager.save_tokens({
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "token_type": self.token_type,
                "expires_in": self.expires_in,
            })

            self.logger.info("Successfully obtained access token")

        except Exception as e:
            raise Exception(f"Failed to exchange code for token: {str(e)}")

    def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.

        Raises:
            Exception: If token refresh fails
        """
        if not self.refresh_token:
            raise Exception("No refresh token available")

        try:
            params = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            }

            response = requests.post(
                "https://wbsapi.withings.net/v2/oauth2", data=params
            )
            response.raise_for_status()
            token_data = response.json()

            if token_data.get("status") != 0:
                raise Exception(f"Token refresh failed: {token_data}")

            # Update tokens
            body = token_data.get("body", {})
            self.access_token = body.get("access_token")
            if "refresh_token" in body:
                self.refresh_token = body.get("refresh_token")
            self.expires_in = body.get("expires_in", 3600)

            # Save updated tokens
            self.token_manager.save_tokens({
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "token_type": self.token_type,
                "expires_in": self.expires_in,
            })

            self.logger.info("Successfully refreshed access token")

        except Exception as e:
            raise Exception(f"Failed to refresh token: {str(e)}")
