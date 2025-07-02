"""Withings API client using authlib for OAuth2 authentication."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict

import requests
from .auth_base import (
    AuthlibOAuth2Client, 
    ClientConfig, 
    TokenFileManager, 
    SlidingWindowValidator,
    WithingsErrorStrategy
)


class WithingsClient(AuthlibOAuth2Client):
    """Withings API client using authlib.
    
    ## Why Withings Requires Custom Implementation:
    
    Withings deviates from standard OAuth2 in several ways, requiring method overrides:
    
    ### 1. Custom Token Request Format:
    **Standard OAuth2**: `grant_type=authorization_code&client_id=...`
    **Withings**: `action=requesttoken&grant_type=authorization_code&client_id=...`
    
    ### 2. Custom Response Format:
    **Standard OAuth2**: `{"access_token": "...", "refresh_token": "..."}`
    **Withings**: `{"status": 0, "body": {"access_token": "...", "refresh_token": "..."}}`
    
    ### 3. Custom Error Handling:
    **Standard OAuth2**: HTTP status codes (401, 403) indicate auth errors
    **Withings**: HTTP 200 with `{"status": 401, "error": "invalid_token"}` indicates auth errors
    
    ## Architecture Solution:
    
    ### Method Overrides (Required):
    - `_exchange_code_for_token()`: Handle Withings token request/response format
    - `_refresh_access_token()`: Handle Withings refresh request/response format
    
    ### Strategy Pattern (Automatic):
    - `WithingsErrorStrategy`: Handles error detection and response validation
    - No need to override `_is_authentication_error()` or `make_request()`
    - Base class automatically uses strategy for error handling
    
    ## Result:
    Clean separation of concerns:
    - **Method overrides**: Handle API format differences
    - **Strategy pattern**: Handle error detection and validation
    - **Base class**: Provides all OAuth2 flow and retry logic
    """

    def __init__(self):
        """Initialize the Withings client.
        
        Reads WITHINGS_CLIENT_ID and WITHINGS_CLIENT_SECRET from environment.
        Uses shared utilities for configuration and token management.
        """
        # Initialize shared utilities
        self.config = ClientConfig.from_env()
        self.token_manager = TokenFileManager("withings")
        self.sliding_window = SlidingWindowValidator()
        
        super().__init__(
            env_client_id="WITHINGS_CLIENT_ID",
            env_client_secret="WITHINGS_CLIENT_SECRET",
            token_file="~/.withings_tokens.json",
            base_url="https://wbsapi.withings.net",
            authorization_endpoint="https://account.withings.com/oauth2_user/authorize2",
            token_endpoint="https://wbsapi.withings.net/v2/oauth2",
            scopes=["user.metrics,user.activity,user.sleepevents"]
        )
        
        # Use Withings-specific error handling strategy
        self.error_strategy = WithingsErrorStrategy()
        
        # Override token validity settings from shared config
        self.validity_days = self.config.validity_days
        self.refresh_buffer_hours = self.config.refresh_buffer_hours

    def get_token_status(self) -> dict:
        """Get token status using shared utilities.
        
        Returns:
            Dictionary with token status information
        """
        token_data = self.token_manager.load_token()
        if not token_data:
            return {"status": "no_token", "days_remaining": 0}
        
        is_valid = self.sliding_window.is_in_sliding_window(token_data)
        days_remaining = self.sliding_window.get_days_remaining(token_data)
        should_refresh = self.sliding_window.should_refresh_proactively(
            token_data, self.config.refresh_buffer_hours
        )
        
        return {
            "status": "valid" if is_valid else "expired",
            "days_remaining": days_remaining,
            "should_refresh": should_refresh,
            "sliding_window_valid": is_valid
        }

    def clear_stored_token(self) -> None:
        """Clear stored token using shared utilities."""
        self.token_manager.clear_token()
        self.token = None
        if hasattr(self.session, 'token'):
            self.session.token = None

    def _exchange_code_for_token(self, code: str, state: str) -> dict:
        """Exchange authorization code for access token using Withings-specific format.
        
        **OVERRIDE REQUIRED** because Withings uses non-standard OAuth2 format:
        
        **Standard OAuth2 Request**:
        ```
        POST /token
        grant_type=authorization_code&client_id=...&code=...
        ```
        
        **Withings Request** (requires 'action' parameter):
        ```
        POST /v2/oauth2
        action=requesttoken&grant_type=authorization_code&client_id=...&code=...
        ```
        
        **Withings Response** (tokens wrapped in 'body'):
        ```
        {"status": 0, "body": {"access_token": "...", "refresh_token": "..."}}
        ```
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback
            
        Returns:
            Token dictionary extracted from response body
            
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
        
        # Use strategy to validate and extract token data
        return self.error_strategy.validate_token_response(token_response, "token exchange")

    # _is_authentication_error override removed - now handled by WithingsErrorStrategy

    def _refresh_access_token(self) -> dict:
        """Refresh the access token using Withings-specific format.
        
        **OVERRIDE REQUIRED** because Withings uses non-standard OAuth2 format:
        
        **Standard OAuth2 Request**:
        ```
        POST /token
        grant_type=refresh_token&client_id=...&refresh_token=...
        ```
        
        **Withings Request** (requires 'action' parameter):
        ```
        POST /v2/oauth2
        action=requesttoken&grant_type=refresh_token&client_id=...&refresh_token=...
        ```
        
        **Withings Response** (tokens wrapped in 'body'):
        ```
        {"status": 0, "body": {"access_token": "...", "refresh_token": "..."}}
        ```
        
        Returns:
            New token dictionary extracted from response body
            
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
        
        # Use strategy to validate and extract token data
        return self.error_strategy.validate_token_response(token_response, "token refresh")

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
