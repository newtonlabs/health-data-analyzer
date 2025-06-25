"""Hevy API service for interacting with workout data.

This module provides a service for interacting with the Hevy API, which uses
API key authentication rather than OAuth. Despite this difference, the service
follows the same architectural patterns as other API services in the system.
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from src.api.services.base_service import BaseAPIService
from src.app_config import AppConfig


class HevyService(BaseAPIService):
    """Service for interacting with the Hevy API.

    This service uses API key authentication rather than OAuth, but still follows
    the same architectural patterns as other API services in the system.

    Attributes:
        api_key: The API key for authenticating with the Hevy API
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the HevyService.

        Args:
            api_key: Optional API key for the Hevy API. If not provided,
                    it will be read from the HEVY_API_KEY environment variable.

        Raises:
            ValueError: If the API key is not provided and not found in environment variables
        """
        super().__init__(
            base_url="https://api.hevyapp.com",
            service_name="hevy"
        )

        # Get API key from parameter or environment variable
        self.api_key = api_key or os.environ.get("HEVY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Hevy API key not found in environment variable: HEVY_API_KEY"
            )

    def _prepare_request_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests.
        
        Returns:
            Dictionary of headers to include in requests
        """
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def fetch_workouts(
        self, page_size: int = AppConfig.HEVY_DEFAULT_PAGE_SIZE
    ) -> Dict[str, Any]:
        """Fetch all workout data from the Hevy API.

        Hevy API does not support date range filtering directly in the endpoint.
        We will fetch all workouts and filter them later in the extractor/processor.

        Args:
            page_size: Number of workouts to fetch per page (default from config)

        Returns:
            Dict containing all raw Hevy workout data.

        Raises:
            Exception: If the API request fails
        """
        # Log the start of the fetch operation
        self.logger.info(f"Fetching Hevy workouts with page size {page_size}")

        all_workouts = []
        page = 1

        try:
            while True:
                params = {"page": page, "pageSize": page_size}
                
                response_data = self._make_request(
                    method="GET",
                    endpoint="v1/workouts",
                    params=params
                )

                # Save individual page response
                from src.utils.file_utils import save_json_to_file
                save_json_to_file(
                    response_data,
                    f"hevy-workouts-page-{page}",
                    subdir="api-responses/hevy",
                )

                # Extract workouts from response
                workouts = response_data.get("workouts", [])
                if not workouts:
                    self.logger.info(f"No more workouts found on page {page}")
                    break

                all_workouts.extend(workouts)
                self.logger.info(f"Fetched {len(workouts)} workouts from page {page}")

                # Check if we've reached the end
                if len(workouts) < page_size:
                    self.logger.info("Reached end of workout data")
                    break

                page += 1

            self.logger.info(f"Total workouts fetched: {len(all_workouts)}")

            # Return in the expected format
            result = {"workouts": all_workouts}
            
            # Save combined results
            save_json_to_file(
                result,
                "hevy-all-workouts",
                subdir="api-responses/hevy",
            )

            return result

        except Exception as e:
            error_msg = f"Hevy API error: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def get_workouts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page_size: int = AppConfig.HEVY_DEFAULT_PAGE_SIZE,
    ) -> Dict[str, Any]:
        """Get workout data from the Hevy API.

        This is the main method that should be called by the health pipeline.
        Date filtering will be handled in the extractor/processor since
        Hevy API doesn't support date filtering directly.

        Args:
            start_date: Start date for filtering workouts (applied in processor)
            end_date: End date for filtering workouts (applied in processor)
            page_size: Number of workouts to fetch per page

        Returns:
            Dictionary containing workout data
        """
        # Note: start_date and end_date are accepted for API consistency
        # but filtering is done in the processor since Hevy API doesn't support it
        return self.fetch_workouts(page_size=page_size)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.

        Returns:
            True if API key is available, False otherwise
        """
        return bool(self.api_key)
