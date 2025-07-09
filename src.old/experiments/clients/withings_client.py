"""Withings API client using authlib for OAuth2 authentication."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict

import requests
from .oauth2_auth_base import (
    OAuth2AuthBase, 
    TokenFileManager, 
    SlidingWindowValidator,
    WithingsErrorStrategy
)
from .config import ClientFactory


class WithingsClient(OAuth2AuthBase):
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
        self.token_manager = TokenFileManager("withings")
        self.sliding_window = SlidingWindowValidator()
        
        # Get service configuration
        service_config = ClientFactory.get_service_config("withings")
        
        # Withings uses comma-separated scopes, but base class expects list
        scopes_string = service_config["scopes"]
        scopes_list = scopes_string.split(",") if isinstance(scopes_string, str) else scopes_string
        
        super().__init__(
            env_client_id="WITHINGS_CLIENT_ID",
            env_client_secret="WITHINGS_CLIENT_SECRET",
            token_file="~/.withings_tokens.json",
            base_url=service_config["base_url"],
            authorization_endpoint=service_config["auth_url"],
            token_endpoint=service_config["token_url"],
            scopes=scopes_list
        )
        
        # Store original comma-separated scopes for Withings API
        self.withings_scopes = scopes_string
        
        # Override OAuth2 session with comma-separated scopes for Withings
        from authlib.integrations.requests_client import OAuth2Session
        self.session = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.withings_scopes  # Use comma-separated scopes
        )
        
        # Use Withings-specific error handling strategy
        self.error_strategy = WithingsErrorStrategy()

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
        
        # Request all body composition measurement types (matching source of truth)
        # 1=weight, 6=body_fat_percentage, 76=muscle_mass, 88=bone_mass, 77=water_percentage
        meastype_values = [
            "1",   # WITHINGS_MEASUREMENT_TYPE_WEIGHT
            "6",   # WITHINGS_MEASUREMENT_TYPE_FAT_RATIO
            "76",  # WITHINGS_MEASUREMENT_TYPE_MUSCLE_MASS
            "88",  # WITHINGS_MEASUREMENT_TYPE_BONE_MASS
            "77",  # WITHINGS_MEASUREMENT_TYPE_WATER_PERCENTAGE
        ]
        
        params = {
            "action": "getmeas",
            "meastype": ",".join(meastype_values),  # All body composition measurement types
            "category": "1",  # Real measurements (1)
            "startdate": startdate,
            "enddate": enddate,
        }
        
        response = self.make_request("measure", params=params)
        data = response.json()
        
        # Error checking is now handled in the make_request override
        return data.get("body", {})
