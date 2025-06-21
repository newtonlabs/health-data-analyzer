"""Whoop API client for handling OAuth2 authentication."""
import os
import secrets
import requests
import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import socket
import threading
from typing import Dict, Any

from src.utils.date_utils import DateUtils, DateFormat
from src.utils.logging_utils import HealthLogger
from .token_manager import TokenManager

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Whoop."""
    def do_GET(self):
        """Handle OAuth callback from Whoop.
        
        This method is called when Whoop redirects back to our local server
        after the user approves access. The URL contains an authorization code
        that we exchange for an access token.
        """
        try:
            parsed_url = urlparse(self.path)
            query_components = parse_qs(parsed_url.query)
            
            if 'code' in query_components and 'state' in query_components:
                self.server.auth_code = query_components['code'][0]
                self.server.auth_state = query_components['state'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication successful! You can close this window.</h1></body></html>")
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication failed. No code received.</h1></body></html>")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error: {e}</h1></body></html>".encode())
        finally:
            # Shutdown the server after handling the request
            threading.Thread(target=self.server.shutdown).start()

class WhoopError(Exception):
    """Custom exception for Whoop API errors."""
    pass



class WhoopClient:
    """Client for interacting with the Whoop API."""
    def __init__(self, client_id: str, client_secret: str, token_manager: TokenManager):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_manager = token_manager
        self.base_url = "https://api.prod.whoop.com/developer"
        self.token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
        self.redirect_uri = "http://localhost:8080/callback"
        
        # For OAuth flow
        self.code = None
        self.state = None

        self.logger = HealthLogger(__name__)

    def get_auth_url(self) -> str:
        """Get the URL for OAuth2 authorization.
        
        Returns:
            URL to redirect user for authorization
        """
        # Generate a secure random state
        self.state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'read:recovery read:cycles read:sleep read:workout read:profile offline',
            'redirect_uri': self.redirect_uri,
            'state': self.state
        }
        return f"https://api.prod.whoop.com/oauth/oauth2/auth?{urlencode(params)}"

    def get_token(self, code: str, state: str) -> None:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback, must match the one we sent
            
        Raises:
            WhoopError: If token exchange fails or state doesn't match
        """
        if state != self.state:
            raise WhoopError("State parameter doesn't match. Possible CSRF attack.")

        try:
            response = requests.post(
                self.token_url,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.redirect_uri
                }
            )
            response.raise_for_status()
            token_data = response.json()
            self.token_manager.save_tokens(token_data)
        except requests.exceptions.RequestException as e:
            raise WhoopError(f"Failed to get access token: {str(e)}")

    def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.
        
        Raises:
            WhoopError: If refresh fails or no refresh token is available
        """
        refresh_token = self.token_manager.get_refresh_token()
        if not refresh_token:
            raise WhoopError("No refresh token available")

        try:
            response = requests.post(
                self.token_url,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            response.raise_for_status()
            token_data = response.json()
            self.token_manager.save_tokens(token_data)
        except requests.exceptions.RequestException as e:
            raise WhoopError(f"Failed to refresh access token: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if we have a valid access token.
        
        Returns:
            True if we have an access token and it's not expired
        """
        return self.token_manager.get_access_token() is not None and not self.token_manager.is_token_expired()

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Whoop API.
        
        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            
        Returns:
            JSON response from API
        """
        if not self.is_authenticated():
            raise WhoopError("Not authenticated. Please get an access token.")

        headers = {
            "Authorization": f"Bearer {self.token_manager.get_access_token()}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            # Always log the JSON response when in debug mode
            response_data = response.json()
            
            # Log API response in debug mode
            from src.utils.logging_utils import DEBUG_MODE
            if DEBUG_MODE:
                # Log to stderr
                import sys
                print(f"\n===== WHOOP API RESPONSE for {endpoint} =====\n{json.dumps(response_data, indent=2)}\n===== END WHOOP API RESPONSE ====", 
                      file=sys.stderr)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise WhoopError(f"Failed to fetch data from Whoop API: {str(e)}")

    def get_recovery_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch recovery data for a date range."""
        # Use the /v1/recovery endpoint as /v1/activity/recovery seems to be deprecated or incorrect.
        # This method is kept for compatibility but internally calls get_recovery.
        return self.get_recovery(start_date, end_date)

    def get_recovery(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get recovery data for a specified time range.
        
        Args:
            start_date: Start date for recovery data
            end_date: End date for recovery data
            
        Returns:
            Dict containing recovery data
        """
        # Add one day to end_date to ensure we get recovery scores recorded early morning
        api_end = end_date + timedelta(days=1)
        
        params = {
            'start': DateUtils.format_date(start_date, DateFormat.ISO),
            'end': DateUtils.format_date(api_end, DateFormat.ISO)
        }
        self.logger.debug(f"API request to v1/recovery with params: {params}")
        response = self._make_request('v1/recovery', params)
        self.logger.log_data_counts('recovery', len(response.get('records', [])))
        return response

    def get_workouts(self, start_date: datetime, end_date: datetime, limit: int = 25) -> Dict[str, Any]:
        """Get workouts for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            limit: Max number of workouts to return
            
        Returns:
            Dictionary containing workout data
        """
        params = {
            'start': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'limit': min(limit, 25)
        }
        return self._make_request('v1/activity/workout', params)
        

    
    def get_sleep(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get sleep data for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary containing sleep data including duration, stages, and quality metrics
        """
        params = {
            'start': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end': end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        return self._make_request('v1/activity/sleep', params)
        


    # Authentication methods
    def authenticate(self) -> bool:
        """Authenticate with Whoop using OAuth2 flow.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        # Try using saved tokens first
        if self.is_authenticated():
            try:
                self.logger.debug("Found saved authentication tokens")
                self.logger.debug("Refreshing access token...")
                self.refresh_access_token()
                return True
            except Exception:
                self.logger.debug("Token refresh failed, clearing tokens and starting new authentication...")
                self.token_manager.clear_tokens()
        
        # Start new authentication
        auth_url = self.get_auth_url()
        print(f"\n[Whoop Auth] Please visit this URL to authorize the application: {auth_url}")
        self.logger.debug(f"Please visit this URL to authorize the application: {auth_url}")
        
        # Start local server to handle callback
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
        server.auth_code = None
        server.auth_state = None
        
        # Set a timeout for the server to prevent it from running indefinitely
        server.timeout = 60  # seconds
        
        self.logger.debug("Waiting for authorization...")
        try:
            # Handle a single request, then shut down
            server.handle_request()
            
            if server.auth_code and server.auth_state:
                self.get_token(server.auth_code, server.auth_state)
                self.logger.info("Whoop authentication successful!")
                return True
            else:
                self.logger.error("Did not receive authorization code or state from callback.")
                return False
        except socket.timeout:
            self.logger.error("Authentication server timed out. Please try again.")
            return False
        except Exception as e:
            self.logger.error(f"Error starting or handling authentication server: {e}")
            return False
        finally:
            server.server_close()


        
    def get_token(self, code: str, state: str) -> None:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback, must match the one we sent
            
        Raises:
            WhoopError: If token exchange fails or state doesn't match
        """
        if state != self.state:
            raise WhoopError("State parameter doesn't match. Possible CSRF attack.")
            
        try:
            response = requests.post(
                self.token_url,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.redirect_uri
                }
            )
            
            # Check for error response
            if response.status_code != 200:
                error_msg = response.json().get('error_description', 'Unknown error')
                raise WhoopError(f"Failed to get access token: {error_msg}")
                
            token_data = response.json()
            self.token_manager.save_tokens(token_data)
        except requests.exceptions.RequestException as e:
            raise WhoopError(f"Failed to get access token: {str(e)}")
        
    def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.
        
        Raises:
            WhoopError: If refresh fails or no refresh token is available
        """
        if not self.refresh_token:
            raise WhoopError("No refresh token available")
            
        try:
            response = requests.post(
                "https://api.prod.whoop.com/oauth/oauth2/token",
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': self.refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.token_manager.save_tokens(token_data)
            
        except requests.exceptions.RequestException as e:
            raise WhoopError(f"Failed to refresh access token: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if we have a valid access token.
        
        Returns:
            True if we have an access token and it's not expired
        """
        return self.token_manager.get_access_token() is not None and not self.token_manager.is_token_expired()
