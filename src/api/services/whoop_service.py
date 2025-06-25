"""Whoop API service for pure data fetching.

This service handles only API communication with Whoop.
No data processing or transformation is performed here.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

from .base_service import BaseAPIService
from src.sources.whoop import WhoopClient
from src.utils.date_utils import DateUtils, DateFormat


class WhoopService(BaseAPIService):
    """Pure API service for Whoop data fetching.
    
    This service is responsible only for making API calls and returning
    raw responses. All data processing is handled by extractors.
    """
    
    def __init__(self, client: Optional[WhoopClient] = None):
        """Initialize the Whoop service.
        
        Args:
            client: Optional WhoopClient instance. If None, creates a new one.
        """
        if client is None:
            client = WhoopClient()
        
        super().__init__(client)
    
    def fetch_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Fetch all available data from Whoop API.
        
        Args:
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            Dictionary containing raw API responses for all data types
            
        Raises:
            APIClientError: If API calls fail
        """
        start_date, end_date = self.validate_date_range(start_date, end_date)
        
        # Convert dates to datetime for API calls
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
        else:
            start_dt = datetime.now() - timedelta(days=7)  # Default to last week
            
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
        else:
            end_dt = datetime.now()
        
        self.logger.info(f"Fetching Whoop data from {start_dt.date()} to {end_dt.date()}")
        
        # Fetch all data types
        data = {}
        
        try:
            # Fetch workouts
            self.log_api_call("v1/activity/workout", {"start": start_dt, "end": end_dt})
            data['workouts'] = self.client.get_workouts(start_dt, end_dt)
            self.log_api_call("v1/activity/workout", response_size=len(data['workouts'].get('data', [])))
            
        except Exception as e:
            self.handle_api_error(e, "v1/activity/workout")
            data['workouts'] = {"data": []}
        
        try:
            # Fetch recovery data
            self.log_api_call("v1/recovery", {"start": start_dt, "end": end_dt})
            data['recovery'] = self.client.get_recovery(start_dt, end_dt)
            self.log_api_call("v1/recovery", response_size=len(data['recovery'].get('data', [])))
            
        except Exception as e:
            self.handle_api_error(e, "v1/recovery")
            data['recovery'] = {"data": []}
        
        try:
            # Fetch sleep data
            self.log_api_call("v1/activity/sleep", {"start": start_dt, "end": end_dt})
            data['sleep'] = self.client.get_sleep(start_dt, end_dt)
            self.log_api_call("v1/activity/sleep", response_size=len(data['sleep'].get('data', [])))
            
        except Exception as e:
            self.handle_api_error(e, "v1/activity/sleep")
            data['sleep'] = {"data": []}
        
        self.logger.info(f"Successfully fetched Whoop data: "
                        f"{len(data['workouts'].get('data', []))} workouts, "
                        f"{len(data['recovery'].get('data', []))} recovery records, "
                        f"{len(data['sleep'].get('data', []))} sleep records")
        
        return data
    
    def fetch_workouts(
        self, 
        start_date: date, 
        end_date: date, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Fetch workout data from Whoop API.
        
        Args:
            start_date: Start date for workouts
            end_date: End date for workouts
            limit: Maximum number of workouts to return
            
        Returns:
            Raw API response containing workout data
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        try:
            self.log_api_call("v1/activity/workout", {
                "start": start_dt, 
                "end": end_dt, 
                "limit": limit
            })
            
            response = self.client.get_workouts(start_dt, end_dt, limit)
            
            self.log_api_call("v1/activity/workout", 
                            response_size=len(response.get('data', [])))
            
            return response
            
        except Exception as e:
            self.handle_api_error(e, "v1/activity/workout")
            return {"data": []}
    
    def fetch_recovery(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Fetch recovery data from Whoop API.
        
        Args:
            start_date: Start date for recovery data
            end_date: End date for recovery data
            
        Returns:
            Raw API response containing recovery data
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        try:
            self.log_api_call("v1/recovery", {"start": start_dt, "end": end_dt})
            
            response = self.client.get_recovery(start_dt, end_dt)
            
            self.log_api_call("v1/recovery", 
                            response_size=len(response.get('data', [])))
            
            return response
            
        except Exception as e:
            self.handle_api_error(e, "v1/recovery")
            return {"data": []}
    
    def fetch_sleep(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Fetch sleep data from Whoop API.
        
        Args:
            start_date: Start date for sleep data
            end_date: End date for sleep data
            
        Returns:
            Raw API response containing sleep data
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        try:
            self.log_api_call("v1/activity/sleep", {"start": start_dt, "end": end_dt})
            
            response = self.client.get_sleep(start_dt, end_dt)
            
            self.log_api_call("v1/activity/sleep", 
                            response_size=len(response.get('data', [])))
            
            return response
            
        except Exception as e:
            self.handle_api_error(e, "v1/activity/sleep")
            return {"data": []}
