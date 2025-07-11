"""Client for interacting with the Hevy API.

This module provides a client for interacting with the Hevy API, which uses
API key authentication rather than OAuth. Despite this difference, the client
follows the same architectural patterns as other API clients in the system.
"""

import os
from datetime import datetime
from typing import Any, Optional

import requests

from src.app_config import AppConfig
from src.utils.api_client import APIClient, APIClientError
from src.utils.logging_utils import HealthLogger
from src.utils.progress_indicators import ProgressIndicator


class HevyClient(APIClient):
    """Client for interacting with the Hevy API.

    This client uses API key authentication rather than OAuth, but still follows
    the same architectural patterns as other API clients in the system.

    Attributes:
        api_key: The API key for authenticating with the Hevy API
        logger: Logger for this client
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the HevyClient.

        Args:
            api_key: Optional API key for the Hevy API. If not provided,
                    it will be read from the HEVY_API_KEY environment variable.

        Raises:
            ValueError: If the API key is not provided and not found in environment variables
        """
        # Initialize with dummy values for OAuth parameters since Hevy uses API key auth
        super().__init__(
            client_id="dummy",  # Not used for API key auth
            client_secret="dummy",  # Not used for API key auth
            env_client_id="HEVY_DUMMY_ID",  # Not used but required by base class
            env_client_secret="HEVY_DUMMY_SECRET",  # Not used but required by base class
            default_token_path="~/.hevy_dummy_tokens.json",  # Not used but required
            base_url="https://api.hevyapp.com",  # Correct API endpoint
        )

        # Get API key from parameter or environment variable
        self.api_key = api_key or os.environ.get("HEVY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Hevy API key not found in environment variable: HEVY_API_KEY"
            )

        # Set up logger
        self.logger = HealthLogger(self.__class__.__name__)



    def _get_access_token(self) -> str:
        """Get API key for Hevy authentication.
        
        Returns:
            str: The API key for authentication
            
        Raises:
            APIClientError: If no API key is available
        """
        if not self.api_key:
            raise APIClientError("No API key available for Hevy authentication")
        return self.api_key

    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] = None,
        method: str = "GET",
        headers: dict[str, str] = None,
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """Make a request to the Hevy API.

        This method overrides the base class implementation to use API key authentication
        instead of OAuth tokens.

        Args:
            endpoint: API endpoint (e.g., "v1/workouts")
            params: Dictionary of query parameters
            method: HTTP method (only GET is supported by Hevy API)
            headers: Additional headers (will be merged with API key header)
            retry_count: Current retry attempt (used internally for recursion)

        Returns:
            JSON response from API

        Raises:
            APIClientError: If the request fails after all retries
        """
        if method.upper() != "GET":
            raise APIClientError("Hevy API only supports GET requests")

        # Build request URL
        url = f"{self.base_url}/{endpoint}"

        # Set up headers with API key
        request_headers = headers or {}
        request_headers["api-key"] = self._get_access_token()
        request_headers["accept"] = "application/json"

        # Set default page size for workouts endpoint if not specified
        request_params = params if params is not None else {}
        if endpoint == "v1/workouts" and "pageSize" not in request_params:
            request_params["pageSize"] = AppConfig.HEVY_DEFAULT_PAGE_SIZE

        try:
            # Make the request
            response = requests.get(url, headers=request_headers, params=request_params)

            # Handle 404 for workouts endpoint as empty result
            if response.status_code == 404 and endpoint == "v1/workouts":
                return {}

            response.raise_for_status()
            response_data = response.json()

            return response_data

        except requests.exceptions.RequestException as e:
            # If we've exhausted retries, give up
            if retry_count < self.MAX_RETRIES:
                self.logger.logger.warning(
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
                )

            # All retries failed
            raise APIClientError(
                f"API request failed after {self.MAX_RETRIES} retries: {str(e)}"
            )

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        For Hevy, this simply checks if we have an API key.

        Returns:
            True if the client has an API key, False otherwise
        """
        return bool(self.api_key)

    def authenticate(self) -> bool:
        """Authenticate with the Hevy API.

        For Hevy, authentication is handled via API key.

        Returns:
            True if authentication is successful

        Raises:
            APIClientError: If authentication fails
        """
        # For API key auth, just verify we have the key
        self._get_access_token()  # Will raise APIClientError if no key
        return True

    def get_workouts(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        page_size: int = AppConfig.HEVY_DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:
        """Get workout data from the Hevy API.

        This is the main method that should be called by the health pipeline.
        Date filtering will be handled in the health data processor since
        Hevy API doesn't support date filtering directly.

        Args:
            start_date: Start date for filtering workouts (applied in processor)
            end_date: End date for filtering workouts (applied in processor)
            page_size: Number of workouts to fetch per page

        Returns:
            Dictionary containing workout data
            
        Raises:
            APIClientError: If the API request fails
        """
        # Log the start of the fetch operation
        self.logger.logger.info(f"Fetching Hevy workouts with page size {page_size}")

        all_workouts = []
        page = 1

        try:
            while True:
                params = {"page": page, "pageSize": page_size}

                response_data = self._make_request(
                    endpoint="v1/workouts",
                    params=params,
                )

                workouts = response_data.get("workouts", [])
                if not workouts:
                    break

                all_workouts.extend(workouts)
                self.logger.logger.debug(
                    f"Fetched {len(workouts)} workouts from page {page}"
                )
                page += 1

            self.logger.logger.info(
                f"Successfully fetched {len(all_workouts)} workouts from Hevy API"
            )
            return {"workouts": all_workouts}

        except Exception as e:
            error_msg = f"Failed to fetch Hevy workouts: {str(e)}"
            self.logger.log_skipped_date(None, error_msg)
            ProgressIndicator.step_error(f"ERROR: {error_msg}")
            raise APIClientError(error_msg)
