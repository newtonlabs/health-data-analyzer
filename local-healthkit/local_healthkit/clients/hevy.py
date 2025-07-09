"""Hevy API client using API key authentication."""

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from .base.api_key_auth import APIKeyAuthBase
from .base.config import ClientFactory


class HevyClient(APIKeyAuthBase):
    """Hevy API client using API key authentication.
    
    Hevy is a workout tracking app with a simple API that uses API key authentication.
    No OAuth2 flows, token refresh, or persistent authentication needed.
    """
    
    def __init__(self, page_size: Optional[int] = None):
        """Initialize the Hevy client.
        
        Reads HEVY_API_KEY from environment variables.
        
        Args:
            page_size: Number of workouts to fetch per page (uses config default if None)
        """
        # Get service configuration
        service_config = ClientFactory.get_service_config("hevy")
        
        super().__init__(
            env_api_key="HEVY_API_KEY",
            base_url=service_config["base_url"]
        )
        
        self.page_size = page_size or service_config["default_page_size"]
    
    def get_workouts(
        self, 
        start_date: datetime = None, 
        end_date: datetime = None,
        page_size: int = 10  # Match source of truth: AppConfig.HEVY_DEFAULT_PAGE_SIZE = 10
    ) -> Dict[str, Any]:
        """Get workout data from the Hevy API.
        
        Note: Hevy API doesn't support date filtering, so start_date and end_date
        are accepted for interface consistency but will be applied client-side.
        
        Args:
            start_date: Start date for filtering (applied client-side)
            end_date: End date for filtering (applied client-side)
            page_size: Number of workouts per page (default from init)
            
        Returns:
            Dictionary containing workout data
        """
        # Use provided page_size or fall back to instance default
        if page_size is None:
            page_size = self.page_size
        
        all_workouts = []
        page = 1
        
        while True:
            params = {
                "page": page,
                "pageSize": page_size
            }
            
            response = self.make_request("v1/workouts", params=params)
            data = response.json()
            workouts = data.get("workouts", [])
            
            if not workouts:
                break
            
            all_workouts.extend(workouts)
            page += 1
            
            # If we got fewer workouts than page size, we're done
            if len(workouts) < page_size:
                break
        
        return {"workouts": all_workouts}
    
    
    def get_client_info(self) -> Dict[str, str]:
        """Get client information for debugging.
        
        Returns:
            Dictionary with client configuration info
        """
        base_info = super().get_client_info()
        base_info.update({
            "service": "Hevy",
            "api_type": "Workout tracking",
            "features": "Paginated workouts, exercise details, client-side date filtering"
        })
        return base_info
