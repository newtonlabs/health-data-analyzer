"""Whoop API client for handling OAuth2 authentication."""
import os
import secrets
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, Any, Optional

from src.utils.date_utils import DateUtils, DateFormat
from src.utils.logging_utils import HealthLogger
from .token_manager import TokenManager

class WhoopError(Exception):
    """Custom exception for Whoop API errors."""
    pass

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Whoop."""
    def do_GET(self):
        """Handle OAuth callback from Whoop.
        
        This method is called when Whoop redirects back to our local server
        after the user approves access. The URL contains an authorization code
        that we exchange for an access token.
        """
        try:
            # Parse the authorization code from the callback URL
            parsed_url = urlparse(self.path)
            query_components = parse_qs(parsed_url.query)
            
            if 'code' in query_components and 'state' in query_components:
                # Exchange code for token
                self.server.whoop_client.get_token(query_components['code'][0], query_components['state'][0])
                self.server.authenticated = True
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Authentication successful! You can close this window.")
                self.server.should_stop = True
            else:
                self.send_response(400)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Authentication failed! No authorization code received.")
        except Exception as e:
            self.send_response(500)
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())

class WhoopClient:
    def __init__(self, client_id: str = None, client_secret: str = None, token_file: str = None):
        """Initialize the Whoop client.
        
        Args:
            client_id: Optional client ID. If not provided, will look for WHOOP_CLIENT_ID in environment.
            client_secret: Optional client secret. If not provided, will look for WHOOP_CLIENT_SECRET in environment.
            token_file: Optional path to token storage file.
        
        Raises:
            ValueError: If credentials are not provided or found in environment.
        """
        self.client_id = client_id or os.getenv('WHOOP_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('WHOOP_CLIENT_SECRET')
        if not self.client_id or not self.client_secret:
            raise ValueError("Whoop client ID and secret are required")
            
        self.base_url = "https://api.prod.whoop.com/developer"
        self.access_token = None
        self.token_type = None
        self.expires_in = 0
        self.refresh_token = None
        self.state = None
        
        # Set up token manager and logger
        self.token_manager = TokenManager(token_file or os.path.expanduser('~/.whoop_tokens.json'))
        self.logger = HealthLogger(__name__)
        
        # Try to load existing tokens
        saved_tokens = self.token_manager.get_tokens()
        if saved_tokens:
            self.access_token = saved_tokens.get('access_token')
            self.refresh_token = saved_tokens.get('refresh_token')
            self.token_type = saved_tokens.get('token_type')
            self.expires_in = saved_tokens.get('expires_in', 0)
            self.logger.debug("Found saved authentication tokens")

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, use_developer_api: bool = True) -> Dict[str, Any]:
        """Make a request to the Whoop API.
        
        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            use_developer_api: Whether to use the developer API prefix
            
        Returns:
            Dictionary containing response data
            
        Raises:
            WhoopError: If the request fails
        """
        # Check if we need to refresh the token
        if self.token_manager.is_token_expired():
            try:
                self.refresh_access_token()
            except WhoopError:
                raise WhoopError("Token expired and refresh failed. Please authenticate again.")
        
        if not self.access_token:
            raise WhoopError("Not authenticated. Call authenticate() first")
        
        try:
            import json
            base = self.base_url
            if not use_developer_api:
                base = base.replace('/developer', '')
                
            response = requests.get(
                f"{base}/{endpoint}",
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                },
                params=params,
                verify=False  # Disable SSL verification for development
            )
            response.raise_for_status()
            # Log the JSON response in a consistent format
            response_data = response.json()
            
            # Log API response in debug mode
            from src.utils.logging_utils import DEBUG_MODE
            if DEBUG_MODE:
                # Log to stderr
                import sys
                print(f"\n===== WHOOP API RESPONSE for {endpoint} =====\n{json.dumps(response_data, indent=2)}\n===== END WHOOP API RESPONSE =====", 
                      file=sys.stderr)
            return response.json()
        except Exception as e:
            raise WhoopError(f"Failed to fetch data from Whoop API: {str(e)}")

    # Data fetching methods
    def get_recovery_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
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
        
    def get_user_id(self) -> str:
        """Get the current user's ID.
        
        Returns:
            User ID string
        """
        response = self._make_request('v1/user/profile/basic', use_developer_api=True)
        return str(response['user_id'])
    
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
        return self._make_request('v1/activity/sleep', params, use_developer_api=True)
        
    def get_cycle(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get cycle data for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary containing cycle data including strain, recovery, and sleep metrics
        """
        params = {
            'start': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end': end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        return self._make_request('v1/cycle', params, use_developer_api=True)

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
                self.logger.debug("Token refresh failed, starting new authentication...")
                self.access_token = None
                self.refresh_token = None
                self.token_manager.clear_tokens()
        
        # Start new authentication
        auth_url = self._get_auth_url()
        print(f"[Whoop Auth] Please visit this URL to authorize the application: {auth_url}")
        self.logger.debug(f"Please visit this URL to authorize the application: {auth_url}")
        
        # Start local server to handle callback
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
        server.should_stop = False
        server.authenticated = False
        server.whoop_client = self
        
        self.logger.debug("Waiting for authorization...")
        while not server.should_stop:
            server.handle_request()
        
        return server.authenticated

    def _get_auth_url(self) -> str:
        """Get the URL for OAuth2 authorization.
        
        Returns:
            URL to redirect user for authorization
        """
        # Generate a secure random state
        self.state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'offline read:recovery read:workout read:profile read:sleep read:cycles read:body_measurement',
            'redirect_uri': 'http://localhost:8080/callback',
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
                "https://api.prod.whoop.com/oauth/oauth2/token",
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': 'http://localhost:8080/callback'
                },
                verify=False  # Disable SSL verification for development
            )
            
            # Check for error response
            if response.status_code != 200:
                error_msg = response.json().get('error_description', 'Unknown error')
                raise WhoopError(f"Failed to get access token: {error_msg}")
                
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_type = token_data.get('token_type', 'Bearer')
            self.expires_in = token_data.get('expires_in', 0)
            self.refresh_token = token_data.get('refresh_token')
            
            # Save tokens
            self.token_manager.save_tokens({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_type': self.token_type,
                'expires_in': self.expires_in
            })
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
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token', self.refresh_token)
            self.token_type = token_data.get('token_type', 'Bearer')
            self.expires_in = token_data.get('expires_in', 0)
            
            # Save new tokens
            self.token_manager.save_tokens({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_type': self.token_type,
                'expires_in': self.expires_in
            })
            
        except requests.exceptions.RequestException as e:
            raise WhoopError(f"Failed to refresh access token: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication tokens.
        
        Returns:
            True if we have both access and refresh tokens
        """
        return bool(self.access_token and self.refresh_token)
