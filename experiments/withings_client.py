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
        # Ensure we're authenticated
        if not self.is_authenticated():
            self.authenticate()
        
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

    def make_request(self, endpoint: str, method: str = "GET", params: dict = None, json_data: dict = None, **kwargs):
        """Override make_request to handle Withings-specific API errors with retry logic."""
        
        # For Withings API endpoints, we need custom retry logic
        if endpoint.startswith("v2/"):
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # Make the actual request
                    response = super(WithingsClientExperimental, self).make_request(endpoint, method, params, json_data, **kwargs)
                    
                    # Check Withings-specific error format
                    try:
                        data = response.json()
                        if data.get("status") != 0:
                            error_msg = data.get("error", "Unknown error")
                            
                            # If it's an invalid token error and we have retries left
                            if "invalid_token" in error_msg.lower() and attempt < max_retries - 1:
                                print(f"⚠️  Withings invalid token error (attempt {attempt + 1}): {error_msg}")
                                
                                # Try refresh first
                                print("🔄 Attempting token refresh...")
                                if self.refresh_token_if_needed(force=True):
                                    print("✅ Token refreshed, retrying request...")
                                    continue  # Retry the request
                                
                                # Refresh failed, try full re-authentication
                                print("🔄 Refresh failed, attempting full re-authentication...")
                                if self.authenticate():
                                    print("✅ Re-authenticated, retrying request...")
                                    continue  # Retry the request
                                else:
                                    raise Exception(f"Failed to re-authenticate: {error_msg}")
                            else:
                                # Not an auth error, or out of retries
                                raise Exception(f"Withings API error: {error_msg}")
                    except ValueError:
                        # Not JSON, continue normally
                        pass
                        
                    return response
                    
                except Exception as e:
                    # If it's not a Withings API error, re-raise
                    if attempt == max_retries - 1:
                        raise
                    # Otherwise continue to next attempt
        else:
            # For non-v2 endpoints, use standard retry logic
            return super().make_request(endpoint, method, params, json_data, **kwargs)
