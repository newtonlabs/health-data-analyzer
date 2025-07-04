"""Base class for API key-based authentication clients.

This module provides a simplified base class for APIs that use API key authentication
instead of OAuth2. It follows similar patterns to the OAuth2 clients but without
the complexity of token management, refresh logic, or persistent storage.
"""

import os
import time
from typing import Any, Dict, Optional

import requests

from .config import ClientFactory


class APIKeyClient:
    """Base class for API key-based authentication clients.
    
    This is a simplified base class for APIs that use API key authentication
    instead of OAuth2. It follows the same patterns as the OAuth2 clients
    but without token management complexity.
    
    Key features:
    - Simple API key authentication from environment variables
    - Retry logic with exponential backoff
    - Consistent error handling
    - Configurable authentication headers
    - No token persistence (stateless)
    
    Example usage:
    ```python
    class MyAPIClient(APIKeyClient):
        def __init__(self):
            super().__init__(
                env_api_key="MY_API_KEY",
                base_url="https://api.example.com"
            )
        
        def get_data(self):
            response = self.make_request("v1/data")
            return response.json()
    ```
    """
    
    def __init__(self, env_api_key: str, base_url: str, max_retries: int = 3):
        """Initialize the API key client.
        
        Args:
            env_api_key: Environment variable name containing the API key
            base_url: Base URL for API requests
            max_retries: Maximum number of retry attempts for failed requests
            
        Raises:
            ValueError: If the API key environment variable is not found
        """
        self.api_key = os.getenv(env_api_key)
        if not self.api_key:
            raise ValueError(f"Environment variable {env_api_key} is required")
        
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.config = ClientFactory.get_client_config()
        self.env_api_key = env_api_key  # Store for debugging
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated (has valid API key).
        
        Returns:
            True if API key is available
        """
        return bool(self.api_key)
    
    def make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        **kwargs
    ) -> requests.Response:
        """Make an authenticated API request.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            method: HTTP method
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            Exception: If request fails after all retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Prepare headers with API key
        request_headers = headers or {}
        request_headers.update(self._get_auth_headers())
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=request_headers,
                    **kwargs
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                    print(f"⚠️  Request failed (attempt {attempt + 1}), retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"API request failed after {self.max_retries} retries: {e}")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests.
        
        Override this method in subclasses to customize header format.
        
        Default format:
        - "api-key": {api_key}
        - "accept": "application/json"
        
        Returns:
            Dictionary of headers for authentication
        """
        return {
            "api-key": self.api_key,
            "accept": "application/json"
        }
    
    def get_client_info(self) -> Dict[str, str]:
        """Get client information for debugging and verification.
        
        Returns:
            Dictionary with client configuration info
        """
        return {
            "client_type": "API Key",
            "base_url": self.base_url,
            "authenticated": "✅ Yes" if self.is_authenticated() else "❌ No",
            "env_variable": self.env_api_key,
            "config": f"{self.config.validity_days} days validity, {self.config.refresh_buffer_hours}h buffer",
            "max_retries": str(self.max_retries),
            "notes": "No token persistence needed - uses API key authentication"
        }


class APIKeyError(Exception):
    """Exception raised for API key client errors."""
    pass
