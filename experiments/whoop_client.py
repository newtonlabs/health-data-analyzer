"""Experimental Whoop API client using authlib for OAuth2 authentication."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict

from auth_base import AuthlibOAuth2Client


class WhoopClientExperimental(AuthlibOAuth2Client):
    """Experimental Whoop API client using authlib."""

    def __init__(self):
        """Initialize the Whoop client.
        
        Reads WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET from environment.
        """
        super().__init__(
            env_client_id="WHOOP_CLIENT_ID",
            env_client_secret="WHOOP_CLIENT_SECRET",
            token_file="~/.whoop_tokens_experimental.json",
            base_url="https://api.prod.whoop.com/developer",
            authorization_endpoint="https://api.prod.whoop.com/oauth/oauth2/auth",
            token_endpoint="https://api.prod.whoop.com/oauth/oauth2/token",
            scopes=[
                "read:recovery",
                "read:cycles", 
                "read:sleep",
                "read:workout",
                "read:profile",
                "offline"
            ]
        )

    def get_recovery(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get recovery data for a specified time range.

        Args:
            start_date: Start date for recovery data
            end_date: End date for recovery data

        Returns:
            Dict containing recovery data
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()
        
        # Whoop API requires end date to be after start date
        api_end = end_date + timedelta(days=1)
        
        all_records = []
        next_token = None
        page_count = 0
        
        while True:
            page_count += 1
            params = {
                "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": api_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": 25,
            }
            
            if next_token:
                params["nextToken"] = next_token
            
            response = self.make_request("v1/recovery", params=params)
            data = response.json()
            
            records = data.get("records", [])
            all_records.extend(records)
            
            # Check if there are more pages
            next_token = data.get("next_token")
            if not next_token:
                break
        
        return {
            "records": all_records,
            "next_token": None
        }

    def get_workouts(
        self, start_date: datetime, end_date: datetime, limit: int = 25
    ) -> dict[str, Any]:
        """Get workouts for a date range with automatic pagination.

        Args:
            start_date: Start date
            end_date: End date
            limit: Max number of workouts per page

        Returns:
            Dictionary containing all workout data across pages
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()
        
        all_records = []
        next_token = None
        page_count = 0
        
        while True:
            page_count += 1
            params = {
                "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": limit,
            }
            
            if next_token:
                params["nextToken"] = next_token
            
            response = self.make_request("v1/activity/workout", params=params)
            data = response.json()
            
            records = data.get("records", [])
            all_records.extend(records)
            
            # Check if there are more pages
            next_token = data.get("next_token")
            if not next_token:
                break
        
        return {
            "records": all_records,
            "next_token": None
        }

    def get_sleep(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get sleep data for a specified time range.

        Args:
            start_date: Start date for sleep data
            end_date: End date for sleep data

        Returns:
            Dict containing sleep data
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()
        
        # Whoop API requires end date to be after start date
        api_end = end_date + timedelta(days=1)
        
        all_records = []
        next_token = None
        page_count = 0
        
        while True:
            page_count += 1
            params = {
                "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": api_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": 25,
            }
            
            if next_token:
                params["nextToken"] = next_token
            
            response = self.make_request("v2/activity/sleep", params=params)
            data = response.json()
            
            records = data.get("records", [])
            all_records.extend(records)
            
            # Check if there are more pages
            next_token = data.get("next_token")
            if not next_token:
                break
        
        return {
            "records": all_records,
            "next_token": None
        }

    def get_cycles(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get physiological cycle data for a specified time range.

        Args:
            start_date: Start date for cycle data
            end_date: End date for cycle data

        Returns:
            Dict containing cycle data
        """
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()
        
        # Whoop API requires end date to be after start date
        api_end = end_date + timedelta(days=1)
        
        all_records = []
        next_token = None
        page_count = 0
        
        while True:
            page_count += 1
            params = {
                "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": api_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": 25,
            }
            
            if next_token:
                params["nextToken"] = next_token
            
            response = self.make_request("v1/cycle", params=params)
            data = response.json()
            
            records = data.get("records", [])
            all_records.extend(records)
            
            # Check if there are more pages
            next_token = data.get("next_token")
            if not next_token:
                break
        
        return {
            "records": all_records,
            "next_token": None
        }
