"""Base classes for data sources and API clients."""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from typing import Any, Optional

import pandas as pd
import requests

from src.sources.token_manager import TokenManager
from src.utils.date_utils import DateFormat, DateUtils
from src.utils.logging_utils import HealthLogger


class DataSource(ABC):
    def __init__(self, data_dir: str = "data"):
        """Initialize data source.

        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def get_file_path(self, filename: str) -> str:
        """Get full path for a file."""
        return os.path.join(self.data_dir, filename)

    def get_dated_file_path(self, base_name: str, date: datetime) -> str:
        """Get path for a dated file."""
        return self.get_file_path(
            f"{DateUtils.format_date(date, DateFormat.STANDARD)}-{base_name}"
        )

    @abstractmethod
    def load_data(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Load data for the specified date range.

        Args:
            start_date: Start date for data range
            end_date: End date for data range

        Returns:
            DataFrame with data for the specified range
        """
        pass


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Base handler for OAuth callbacks."""

    def log_message(self, format, *args):
        """Override to suppress HTTP server logs."""
        # Disable logging of HTTP requests
        pass


class APIClientError(Exception):
    """Base exception for API client errors."""

    pass


class APIClient:
    """Base class for API clients.

    This class provides common functionality for API clients including:
    1. Credential management with environment variable fallbacks
    2. Token management and storage with extended validity periods
    3. Standardized authentication flow with reduced reauthentication
    4. Centralized API request handling with error handling and retries
    """

    # Maximum number of retries for API requests
    MAX_RETRIES = 3

    # Default validity period for tokens (90 days)
    DEFAULT_TOKEN_VALIDITY_DAYS = 90  # Extended to 90 days for sliding window
    # Default buffer time before expiration to trigger refresh (1 day)
    DEFAULT_REFRESH_BUFFER_HOURS = 24
    
    # Conversion constants
    SECONDS_PER_DAY = 24 * 3600  # 24 hours * 3600 seconds per hour

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        token_file: str = None,
        env_client_id: str = None,
        env_client_secret: str = None,
        default_token_path: str = None,
        base_url: str = None,
        validity_days: int = None,
        refresh_buffer_hours: int = None,
    ):
        """Initialize the API client.

        Args:
            client_id: Optional client ID. If not provided, will look for env_client_id in environment.
            client_secret: Optional client secret. If not provided, will look for env_client_secret in environment.
            token_file: Optional path to token storage file.
            env_client_id: Environment variable name for client ID.
            env_client_secret: Environment variable name for client secret.
            default_token_path: Default path for token storage.
            base_url: Base URL for API requests.
            validity_days: Number of days tokens are considered valid (default: 30)
            refresh_buffer_hours: Hours before expiration to trigger refresh (default: 24)

        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        # Initialize credentials
        self.client_id = client_id or os.getenv(env_client_id)
        self.client_secret = client_secret or os.getenv(env_client_secret)
        if not self.client_id:
            raise ValueError(f"{env_client_id} is required")

        # Get validity period from environment or use default
        validity_days = validity_days or int(
            os.getenv("TOKEN_VALIDITY_DAYS", self.DEFAULT_TOKEN_VALIDITY_DAYS)
        )
        refresh_buffer_hours = refresh_buffer_hours or int(
            os.getenv("TOKEN_REFRESH_BUFFER_HOURS", self.DEFAULT_REFRESH_BUFFER_HOURS)
        )

        # Initialize API configuration
        self.base_url = base_url
        self.token_manager = TokenManager(
            token_file or os.path.expanduser(default_token_path),
            validity_days=validity_days,
            refresh_buffer_hours=refresh_buffer_hours,
        )

        # Initialize token state
        self.access_token = None
        self.refresh_token = None
        self.token_type = None
        self.expires_in = 0
        self.state = None
        self.auth_attempts = 0  # Track authentication attempts

        # Set up logging
        self.logger = HealthLogger(self.__class__.__name__)

        # Try to load existing tokens
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from token manager and update instance variables."""
        saved_tokens = self.token_manager.get_tokens()
        if saved_tokens:
            self.access_token = saved_tokens.get("access_token")
            self.refresh_token = saved_tokens.get("refresh_token")
            self.token_type = saved_tokens.get("token_type")
            self.expires_in = saved_tokens.get("expires_in", 0)

    def is_authenticated(self) -> bool:
        """Check if we have valid authentication.

        Returns:
            True if we have valid tokens
        """
        # First check if we have an access token in memory
        if not self.access_token:
            # If not, try to load from token manager
            self._load_tokens()

        return bool(self.access_token)

    def handle_authentication(self) -> bool:
        """Handle authentication with token refresh and sliding window approach.

        This method tries to authenticate in the following order:
        1. Use existing tokens if valid
        2. Try to refresh tokens if possible
        3. Return False to let subclasses handle full authentication

        With the sliding window approach, each successful refresh extends
        the token validity period by another 90 days.

        Returns:
            bool: True if authentication was successful with existing tokens, False otherwise
        """
        # Try using saved tokens first
        if self.is_authenticated():
            try:
                self.logger.debug("Found saved authentication tokens")
                
                # Check if we need to refresh the access token
                if self.token_manager.is_token_expired():
                    self.logger.debug("Access token expired or expiring soon, refreshing...")
                    if self.refresh_access_token():
                        self.logger.debug("Successfully refreshed access token")
                        return True
                    else:
                        self.logger.warning(
                            "Token refresh failed, clearing tokens and starting new authentication..."
                        )
                        self.token_manager.clear_tokens()
                else:
                    self.logger.debug("Using existing valid access token")
                    return True
            except Exception as e:
                self.logger.warning(
                    f"Token refresh failed ({str(e)}), clearing tokens and starting new authentication..."
                )
                self.token_manager.clear_tokens()

        # Return False to let subclasses handle full authentication
        return False

    def _get_access_token(self) -> str:
        """Get a valid access token for API requests.

        This method tries to:
        1. Use an existing token if available
        2. Refresh the token if needed
        3. Authenticate if necessary

        Returns:
            str: A valid access token

        Raises:
            APIClientError: If unable to obtain a valid token
        """
        # Try to use existing token
        if self.access_token:
            return self.access_token

        # Try to refresh token
        if self.refresh_token and self.refresh_access_token():
            return self.access_token

        # If refresh failed, try full authentication
        if self.authenticate():
            if self.access_token:
                return self.access_token

        # If we still don't have a token, raise an error
        raise APIClientError("Failed to obtain a valid access token")

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token.

        This is a base implementation that subclasses should override
        with their specific token refresh logic.

        Returns:
            bool: True if refresh was successful

        Raises:
            APIClientError: If refresh fails
        """
        raise APIClientError("refresh_access_token not implemented")

    def get_extended_expiration_seconds(self, original_expires_in: int = 3600) -> tuple[int, int]:
        """
        Calculate extended expiration time in seconds based on TokenManager's validity period.
        
        Args:
            original_expires_in: Original expiration time in seconds from the API
            
        Returns:
            Tuple of (extended_expires_in, validity_days)
        """
        # Get validity period from token manager
        validity_days = self.token_manager.validity_days
        
        # Convert days to seconds
        extended_expires_in = validity_days * self.SECONDS_PER_DAY
        
        return extended_expires_in, validity_days
        
    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] = None,
        method: str = "GET",
        headers: dict[str, str] = None,
        retry_count: int = 0,
        save_response: bool = False,
        save_path: str = None,
    ) -> dict[str, Any]:
        """Make a request to the API with retry logic and token refresh.

        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            method: HTTP method (GET, POST, etc.)
            headers: Optional headers
            retry_count: Current retry attempt (used internally for recursion)
            save_response: Whether to save the response to a file
            save_path: Path to save the response (if save_response is True)

        Returns:
            JSON response from API

        Raises:
            APIClientError: If the request fails after all retries
        """
        # Get a valid access token
        try:
            access_token = self._get_access_token()
        except APIClientError as e:
            if retry_count < self.MAX_RETRIES:
                self.logger.warning(
                    f"Authentication failed, retrying ({retry_count + 1}/{self.MAX_RETRIES})"
                )
                return self._make_request(
                    endpoint,
                    params,
                    method,
                    headers,
                    retry_count + 1,
                    save_response,
                    save_path,
                )
            raise e

        # Build request URL
        url = f"{self.base_url}/{endpoint}"

        # Set up headers
        request_headers = headers or {}
        request_headers["Authorization"] = (
            f"{self.token_type or 'Bearer'} {access_token}"
        )

        try:
            # Make the request
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, params=params)
            else:  # POST
                response = requests.post(url, headers=request_headers, json=params)

            response.raise_for_status()
            response_data = response.json()

            # Save response to file if requested
            if save_response and save_path:
                from src.utils.file_utils import save_json_to_file

                # Extract client name from class name for the subdir
                client_name = self.__class__.__name__.replace("Client", "").lower()
                subdir = f"api-responses/{client_name}"
                save_json_to_file(response_data, save_path, subdir=subdir)

            return response_data
        except requests.exceptions.RequestException as e:
            # Try token refresh if unauthorized
            if hasattr(e, "response") and e.response.status_code == 401:
                if retry_count < self.MAX_RETRIES:
                    try:
                        # Try to refresh the token
                        self.logger.debug("Received 401, attempting token refresh")
                        if self.refresh_token and hasattr(self, "refresh_access_token"):
                            refresh_success = self.refresh_access_token()
                            if refresh_success:
                                # Retry with new token
                                return self._make_request(
                                    endpoint,
                                    params,
                                    method,
                                    headers,
                                    retry_count + 1,
                                    save_response,
                                    save_path,
                                )
                    except Exception as refresh_error:
                        self.logger.warning(
                            f"Token refresh failed: {str(refresh_error)}"
                        )

                    # If refresh failed, try to reauthenticate
                    try:
                        self.logger.debug(
                            "Token refresh failed, attempting full reauthentication"
                        )
                        self.authenticate()
                        return self._make_request(
                            endpoint,
                            params,
                            method,
                            headers,
                            retry_count + 1,
                            save_response,
                            save_path,
                        )
                    except Exception as auth_error:
                        self.logger.warning(
                            f"Reauthentication failed: {str(auth_error)}"
                        )

            # If we've exhausted retries or it's not a 401 error, give up
            if retry_count < self.MAX_RETRIES:
                self.logger.warning(
                    f"Request failed, retrying ({retry_count + 1}/{self.MAX_RETRIES})"
                )
                # Exponential backoff
                import time

                time.sleep(2**retry_count)  # 1, 2, 4, 8 seconds
                return self._make_request(
                    endpoint,
                    params,
                    method,
                    headers,
                    retry_count + 1,
                    save_response,
                    save_path,
                )

            # All retries failed
            raise APIClientError(
                f"API request failed after {self.MAX_RETRIES} retries: {str(e)}"
            )

    def exchange_code_for_token(
        self,
        code: str,
        state: str,
        expected_state: str,
        token_url: str,
        token_params: dict[str, Any],
    ) -> bool:
        """Exchange authorization code for access token.

        This is a base implementation for OAuth2 code exchange that can be used by subclasses.

        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback
            expected_state: Expected state parameter (to prevent CSRF)
            token_url: URL for token exchange
            token_params: Parameters for token exchange request

        Returns:
            bool: True if token exchange was successful

        Raises:
            APIClientError: If token exchange fails or state doesn't match
        """
        # Verify state parameter to prevent CSRF attacks
        if state != expected_state:
            raise APIClientError("State parameter doesn't match. Possible CSRF attack.")

        try:
            self.logger.debug("Exchanging authorization code for access token")
            response = requests.post(token_url, data=token_params)
            response.raise_for_status()

            # Process response
            token_data = response.json()

            # Check for error response if needed
            if hasattr(token_data, "get") and token_data.get("error"):
                error_msg = token_data.get("error_description", "Unknown error")
                raise APIClientError(f"Failed to get access token: {error_msg}")

            # Save tokens
            self.token_manager.save_tokens(token_data)

            # Update instance variables
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "Bearer")
            self.expires_in = token_data.get("expires_in", 0)

            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to exchange code for token: {str(e)}")
            raise APIClientError(f"Failed to get access token: {str(e)}")

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the API.

        Returns:
            bool: True if authentication was successful, False otherwise
        """
        pass
