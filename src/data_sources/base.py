"""Base classes for data sources and API clients."""

import os
import secrets
from abc import ABC, abstractmethod
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import pandas as pd
import requests

from src.utils.date_utils import DateFormat, DateUtils
from src.utils.logging_utils import HealthLogger
from src.utils.progress_indicators import ProgressIndicator
from .token_manager import TokenManager


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
    2. Token management and storage
    3. Authentication flow
    4. API request handling with error handling
    """
    
    def __init__(
        self, 
        client_id: str = None, 
        client_secret: str = None, 
        token_file: str = None,
        env_client_id: str = None,
        env_client_secret: str = None,
        default_token_path: str = None,
        base_url: str = None
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
            
        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        self.client_id = client_id or os.getenv(env_client_id)
        self.client_secret = client_secret or os.getenv(env_client_secret)
        if not self.client_id:
            raise ValueError(f"{env_client_id} is required")
            
        self.base_url = base_url
        self.token_manager = TokenManager(token_file or os.path.expanduser(default_token_path))
        self.access_token = None
        self.refresh_token = None
        self.token_type = None
        self.expires_in = 0
        self.state = None
        
        # Set up logging
        self.logger = HealthLogger(self.__class__.__name__)
        
        # Try to load existing tokens
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
        return bool(self.access_token)
    
    def _make_request(
        self, endpoint: str, params: dict[str, Any] = None, method: str = "GET", headers: dict[str, str] = None
    ) -> dict[str, Any]:
        """Make a request to the API.
        
        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            method: HTTP method (GET, POST, etc.)
            headers: Optional headers
            
        Returns:
            JSON response from API
            
        Raises:
            APIClientError: If the request fails
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()
            
        # Build request URL
        url = f"{self.base_url}/{endpoint}"
        
        # Set up headers
        request_headers = headers or {}
        if self.access_token:
            request_headers["Authorization"] = f"{self.token_type or 'Bearer'} {self.access_token}"
            
        try:
            # Make the request
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, params=params)
            else:  # POST
                response = requests.post(url, headers=request_headers, json=params)
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Try token refresh if unauthorized
            if hasattr(e, "response") and e.response.status_code == 401:
                if hasattr(self, "refresh_access_token") and self.refresh_token:
                    try:
                        self.refresh_access_token()
                        return self._make_request(endpoint, params, method, headers)
                    except Exception as refresh_error:
                        raise APIClientError(f"Token refresh failed: {str(refresh_error)}")
            raise APIClientError(f"API request failed: {str(e)}")
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the API.
        
        Returns:
            bool: True if authentication was successful
        """
        pass
