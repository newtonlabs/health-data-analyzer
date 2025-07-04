"""Hevy API client using API key authentication."""

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from .api_key_client import APIKeyClient
from .config import ClientFactory


class HevyClient(APIKeyClient):
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
        page_size: int = None
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
        page_size = page_size or self.page_size
        print(f"📋 Fetching Hevy workouts with page size {page_size}")
        
        all_workouts = []
        page = 1
        
        try:
            while True:
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                
                response = self.make_request("v1/workouts", params=params)
                
                # Handle 404 as empty result (no workouts found)
                if response.status_code == 404:
                    break
                
                data = response.json()
                workouts = data.get("workouts", [])
                
                if not workouts:
                    break
                
                # Apply client-side date filtering if dates provided
                if start_date or end_date:
                    filtered_workouts = []
                    for workout in workouts:
                        workout_date = datetime.fromisoformat(workout.get('start_time', '').replace('Z', '+00:00'))
                        
                        if start_date and workout_date.date() < start_date.date():
                            continue
                        if end_date and workout_date.date() > end_date.date():
                            continue
                            
                        filtered_workouts.append(workout)
                    
                    workouts = filtered_workouts
                
                all_workouts.extend(workouts)
                print(f"📄 Fetched {len(workouts)} workouts from page {page}")
                page += 1
                
                # If we got fewer workouts than page size, we're done
                if len(data.get("workouts", [])) < page_size:
                    break
            
            print(f"✅ Retrieved {len(all_workouts)} total workouts from Hevy")
            return {"workouts": all_workouts}
            
        except Exception as e:
            print(f"❌ Hevy client failed: {e}")
            raise
    
    def get_workout_details(self, workout_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific workout.
        
        Args:
            workout_id: ID of the workout to fetch
            
        Returns:
            Dictionary containing detailed workout data
        """
        try:
            response = self.make_request(f"v1/workouts/{workout_id}")
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch workout {workout_id}: {e}")
            raise
    
    def get_exercises(self) -> Dict[str, Any]:
        """Get list of available exercises from Hevy.
        
        Returns:
            Dictionary containing exercise data
        """
        try:
            response = self.make_request("v1/exercises")
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch exercises: {e}")
            raise
    
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
