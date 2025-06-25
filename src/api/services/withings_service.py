"""Withings API service for handling OAuth2 authentication and data retrieval."""

import os
import secrets
from datetime import datetime
from http.server import HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from src.api.services.base_service import BaseAPIService
from src.utils.api_client import OAuthCallbackHandler


class WithingsCallbackHandler(OAuthCallbackHandler):
    """Handle OAuth callback from Withings."""

    def do_GET(self):
        """Handle OAuth callback from Withings.

        This method is called when Withings redirects back to our local server
        after the user approves access. The URL contains an authorization code
        that we exchange for an access token.
        """
        try:
            parsed_url = urlparse(self.path)
            query_components = parse_qs(parsed_url.query)

            if "code" in query_components and "state" in query_components:
                code = query_components["code"][0]
                state = query_components["state"][0]

                # Pass the code and state to the WithingsService instance
                self.server.withings_service.get_token(code, state)
                self.server.authenticated = True
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authentication successful! You can close this window.</h1></body></html>"
                )
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authentication failed. No code received.</h1></body></html>"
                )
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error: {e}</h1></body></html>".encode())
        finally:
            # Signal the server to stop after handling the request
            self.server.should_stop = True


class WithingsService(BaseAPIService):
    """Service for Withings API communication.
    
    This service provides a clean interface to Withings data while delegating
    all actual API communication to the existing WithingsClient.
    """

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        token_file: str = None,
    ):
        """Initialize the Withings service.

        Args:
            client_id: Optional client ID
            client_secret: Optional client secret
            token_file: Optional path to token storage file
        """
        from src.api.clients.withings_client import WithingsClient
        
        self.withings_client = WithingsClient(
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file
        )
        super().__init__(self.withings_client)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.withings_client.is_authenticated()

    def get_weight_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get weight data for a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Raw API response containing weight data
        """
        return self.withings_client.get_weight_data(start_date, end_date)
