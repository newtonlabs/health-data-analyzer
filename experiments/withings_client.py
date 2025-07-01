"""Experimental Withings API client using authlib for OAuth2 authentication."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict

import requests
from auth_base import AuthlibOAuth2Client


class WithingsClientExperimental(AuthlibOAuth2Client):
    """Experimental Withings API client using authlib."""

    def __init__(self):
        """Initialize the Withings client.
        
        Reads WITHINGS_CLIENT_ID and WITHINGS_CLIENT_SECRET from environment.
        """
        super().__init__(
            env_client_id="WITHINGS_CLIENT_ID",
            env_client_secret="WITHINGS_CLIENT_SECRET",
            token_file="~/.withings_tokens_experimental.json",
            base_url="https://wbsapi.withings.net",
            authorization_endpoint="https://account.withings.com/oauth2_user/authorize2",
            token_endpoint="https://wbsapi.withings.net/v2/oauth2",
            scopes=["user.metrics,user.activity,user.sleepevents"]
        )
        
        # Use Withings-specific error handling strategy
        from auth_base import WithingsErrorStrategy
        self.error_strategy = WithingsErrorStrategy()

    def _exchange_code_for_token(self, code: str, state: str) -> dict:
        """Exchange authorization code for access token using Withings-specific format.
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback
            
        Returns:
            Token dictionary
            
        Raises:
            Exception: If token exchange fails
        """
        token_data = {
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        response = requests.post(self.token_endpoint, data=token_data)
        response.raise_for_status()
        token_response = response.json()
        
        # Handle Withings-specific response format
        if token_response.get("status") != 0:
            error_msg = token_response.get("error", "Unknown error")
            raise Exception(f"Withings token exchange failed: {error_msg}")
        
        return token_response.get("body", {})

    def _is_authentication_error(self, error: Exception, response_data: dict = None) -> bool:
        """Override to handle Withings-specific error format."""
        # First check standard errors
        if super()._is_authentication_error(error, response_data):
            return True
            
        # Check for Withings-specific error format
        # Withings returns errors in response JSON with status != 0
        try:
            if hasattr(error, 'response') and error.response is not None:
                response_json = error.response.json()
                if response_json.get("status") != 0:
                    error_msg = response_json.get("error", "").lower()
                    if "invalid_token" in error_msg:
                        return True
        except:
            pass
            
        return False

    def _refresh_access_token(self) -> dict:
        """Refresh the access token using Withings-specific format.
        
        Returns:
            New token dictionary
            
        Raises:
            Exception: If token refresh fails
        """
        refresh_data = {
            "action": "requesttoken",
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.token['refresh_token'],
        }
        
        response = requests.post(self.token_endpoint, data=refresh_data)
        response.raise_for_status()
        token_response = response.json()
        
        # Handle Withings-specific response format
        if token_response.get("status") != 0:
            error_msg = token_response.get("error", "Unknown error")
            raise Exception(f"Withings token refresh failed: {error_msg}")
        
        return token_response.get("body", {})

    def get_weight_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get weight measurements for a specified time range.

        Args:
            start_date: Start date for weight data
            end_date: End date for weight data

        Returns:
            Dict containing weight measurements and body composition data
        """
        # Convert dates to Unix timestamps
        startdate = int(start_date.timestamp())
        enddate = int(end_date.timestamp())
        
        # Request weight measurements (type 1)
        # Note: Multiple measurement types cause "Multiple type request not available" error
        # This may be due to account limitations or API changes
        params = {
            "action": "getmeas",
            "meastype": "1",  # Weight only for now
            "category": "1",  # Real measurements
            "startdate": startdate,
            "enddate": enddate,
        }
        
        response = self.make_request("v2/measure", params=params)
        data = response.json()
        
        # Error checking is now handled in the make_request override
        return data.get("body", {})

