"""Base OAuth2 client using authlib for authentication."""

import json
import os
import socket
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import requests
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc6749 import OAuth2Token


class ErrorHandlingStrategy:
    """Base class for API-specific error handling strategies."""
    
    def is_authentication_error(self, error: Exception, response=None) -> bool:
        """Check if an error indicates authentication failure.
        
        Args:
            error: The exception that was raised
            response: Optional response object
            
        Returns:
            True if this appears to be an authentication error
        """
        raise NotImplementedError
    
    def extract_error_message(self, error: Exception, response=None) -> str:
        """Extract a meaningful error message from the error.
        
        Args:
            error: The exception that was raised
            response: Optional response object
            
        Returns:
            Human-readable error message
        """
        return str(error)


class StandardHttpErrorStrategy(ErrorHandlingStrategy):
    """Standard HTTP error handling for most OAuth2 APIs."""
    
    def is_authentication_error(self, error: Exception, response=None) -> bool:
        """Check for standard HTTP authentication errors."""
        error_str = str(error).lower()
        
        # Standard HTTP auth errors
        if "401" in error_str or "unauthorized" in error_str:
            return True
            
        # Common token error messages
        token_phrases = ["invalid", "expired", "token", "forbidden", "403"]
        for phrase in token_phrases:
            if phrase in error_str:
                return True
        
        # Check if it's an HTTPError with response
        if hasattr(error, 'response') and error.response:
            try:
                status_code = error.response.status_code
                if status_code in [401, 403]:
                    return True
                    
                # Try to get response JSON for API-specific errors
                try:
                    response_json = error.response.json()
                    error_msg = str(response_json.get("error", "")).lower()
                    if "invalid_token" in error_msg or "expired" in error_msg or "unauthorized" in error_msg:
                        return True
                except:
                    pass
            except:
                pass
                
        return False


class WithingsErrorStrategy(ErrorHandlingStrategy):
    """Withings-specific error handling for status-based responses."""
    
    def is_authentication_error(self, error: Exception, response=None) -> bool:
        """Check for Withings-specific authentication errors."""
        # First check standard HTTP errors
        if StandardHttpErrorStrategy().is_authentication_error(error, response):
            return True
            
        # Check for Withings-specific error format in response
        # This handles both error exceptions and successful HTTP responses with status != 0
        if response:
            try:
                data = response.json()
                if data.get("status") != 0:
                    error_msg = str(data.get("error", "")).lower()
                    if "invalid_token" in error_msg or "expired" in error_msg:
                        return True
            except:
                pass
                
        return False
    
    def extract_error_message(self, error: Exception, response=None) -> str:
        """Extract error message from Withings response format."""
        if response:
            try:
                data = response.json()
                if data.get("status") != 0:
                    return data.get("error", str(error))
            except:
                pass
        return str(error)
    
    def validate_response(self, response) -> None:
        """Validate Withings response format and raise errors if needed.
        
        This method checks successful HTTP responses for Withings-specific errors.
        
        Args:
            response: HTTP response object
            
        Raises:
            Exception: If response contains Withings API errors
        """
        try:
            data = response.json()
            if data.get("status") != 0:
                error_msg = data.get("error", "Unknown error")
                # Create an exception with the response attached for error strategy
                error = requests.HTTPError(f"Withings API error: {error_msg}")
                error.response = response
                raise error
        except ValueError:
            # Not JSON, no validation needed
            pass


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth2 callback."""
    
    def log_message(self, format, *args):
        """Override to suppress HTTP server logs."""
        pass
    
    def do_GET(self):
        """Handle GET request for OAuth callback."""
        # Parse the callback URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Extract authorization code and state
        self.server.auth_code = query_params.get('code', [None])[0]
        self.server.auth_state = query_params.get('state', [None])[0]
        self.server.auth_error = query_params.get('error', [None])[0]
        
        # Send response to browser
        if self.server.auth_error:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization Failed</h1><p>Error: ' + 
                           self.server.auth_error.encode() + b'</p></body></html>')
        elif self.server.auth_code:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization Successful!</h1><p>You can close this window.</p></body></html>')
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization Failed</h1><p>No authorization code received.</p></body></html>')


class AuthlibOAuth2Client:
    """Base OAuth2 client using authlib for authentication."""
    
    # Token validity configuration
    DEFAULT_TOKEN_VALIDITY_DAYS = 90
    DEFAULT_REFRESH_BUFFER_HOURS = 24
    SECONDS_PER_DAY = 24 * 3600

    def __init__(
        self,
        env_client_id: str,
        env_client_secret: str,
        token_file: str,
        base_url: str,
        authorization_endpoint: str,
        token_endpoint: str,
        scopes: list[str],
        redirect_uri: str = 'http://localhost:8080/callback',
    ):
        """Initialize the OAuth2 client.

        Args:
            env_client_id: Environment variable name for client ID
            env_client_secret: Environment variable name for client secret
            token_file: Path to token storage file
            base_url: Base URL for API requests
            authorization_endpoint: OAuth2 authorization endpoint
            token_endpoint: OAuth2 token endpoint
            scopes: List of OAuth2 scopes
            redirect_uri: OAuth2 redirect URI
        """
        # Get credentials from environment
        self.client_id = os.getenv(env_client_id)
        self.client_secret = os.getenv(env_client_secret)
        
        if not self.client_id:
            raise ValueError(f"Environment variable {env_client_id} is required")
        if not self.client_secret:
            raise ValueError(f"Environment variable {env_client_secret} is required")

        # Configuration
        self.base_url = base_url
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.scopes = scopes
        self.redirect_uri = redirect_uri
        
        # Token validity configuration
        self.validity_days = int(os.getenv("TOKEN_VALIDITY_DAYS", self.DEFAULT_TOKEN_VALIDITY_DAYS))
        self.refresh_buffer_hours = int(os.getenv("TOKEN_REFRESH_BUFFER_HOURS", self.DEFAULT_REFRESH_BUFFER_HOURS))
        
        # Token storage
        self.token_file = os.path.expanduser(token_file)
        self.token = None
        
        # Initialize OAuth2 session
        self.session = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=' '.join(self.scopes)
        )
        
        # Initialize error handling strategy (can be overridden by subclasses)
        self.error_strategy = StandardHttpErrorStrategy()
        
        # Load existing token if available
        self._load_token()

    def _load_token(self) -> bool:
        """Load token from file.
        
        Returns:
            True if token was loaded successfully
        """
        if not os.path.exists(self.token_file):
            return False
            
        try:
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
                
            # Convert to OAuth2Token
            self.token = OAuth2Token(token_data)
            
            # Update session with token
            self.session.token = self.token
            
            return True
        except Exception as e:
            print(f"Error loading token: {e}")
            return False

    def _save_token(self, token: OAuth2Token) -> None:
        """Save token to file with extended sliding window expiration.
        
        Args:
            token: OAuth2Token to save
        """
        # Convert to dict and add sliding window expiration
        token_dict = dict(token)
        
        # Add sliding window expiration (90 days from now)
        sliding_window_expires_at = datetime.now() + timedelta(days=self.validity_days)
        token_dict['sliding_window_expires_at'] = sliding_window_expires_at.timestamp()
        token_dict['sliding_window_validity_days'] = self.validity_days
        
        # Create OAuth2Token with extended data
        self.token = OAuth2Token(token_dict)
        
        # Update session token to ensure it uses the new token
        self.session.token = self.token
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        
        try:
            with open(self.token_file, 'w') as f:
                json.dump(token_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving token: {e}")

    def is_in_sliding_window(self) -> bool:
        """Check if token is within the sliding window validity period.
        
        Returns:
            True if token is within the 90-day sliding window
        """
        if not self.token:
            return False
            
        # Check if we have our custom sliding_window_expires_at field
        if 'sliding_window_expires_at' not in self.token:
            return False
            
        sliding_expires_at = datetime.fromtimestamp(self.token['sliding_window_expires_at'])
        buffer_time = timedelta(hours=self.refresh_buffer_hours)
        
        return datetime.now() < (sliding_expires_at - buffer_time)
    
    def should_refresh_proactively(self) -> bool:
        """Check if token should be refreshed proactively.
        
        Returns:
            True if token should be refreshed proactively
        """
        if not self.token:
            return False
            
        # Check if token expires within 2 hours (more aggressive than standard buffer)
        if self.token.is_expired(leeway=7200):  # 2 hours
            return True
            
        return False

    def is_authenticated(self) -> bool:
        """Check if we have a valid token using sliding window approach.
        
        Returns:
            True if authenticated with valid token
        """
        if not self.token:
            return False
            
        # First check sliding window validity (90 days)
        if self.is_in_sliding_window():
            return True
            
        # Fallback to standard token expiration (1 hour with 5 minute buffer)
        if not self.token.is_expired(leeway=300):
            return True
            
        return False

    def authenticate(self) -> bool:
        """Perform OAuth2 authentication flow.
        
        Returns:
            True if authentication was successful
        """
        try:
            # Generate authorization URL
            authorization_url, state = self.session.create_authorization_url(
                self.authorization_endpoint
            )
            
            print(f"Please visit this URL to authorize the application:")
            print(authorization_url)
            print()
            
            # Try to open browser automatically
            try:
                webbrowser.open(authorization_url)
                print("Browser opened automatically. If not, copy the URL above.")
            except:
                print("Could not open browser automatically. Please copy the URL above.")
            
            print()
            
            # Start callback server to receive authorization code
            print("Waiting for authorization callback...")
            
            # Find available port starting from 8080
            port = 8080
            while port < 8090:
                try:
                    server = HTTPServer(('localhost', port), CallbackHandler)
                    break
                except OSError:
                    port += 1
            else:
                raise Exception("Could not find available port for callback server")
            
            # Initialize server attributes
            server.auth_code = None
            server.auth_state = None
            server.auth_error = None
            
            # Handle one request (the callback)
            server.handle_request()
            
            # Check for errors
            if server.auth_error:
                raise Exception(f"Authorization error: {server.auth_error}")
            
            if not server.auth_code:
                raise Exception("No authorization code received")
            
            if server.auth_state != state:
                raise Exception("State parameter mismatch - possible CSRF attack")
            
            print("✅ Authorization code received successfully!")
            
            # Exchange code for token using overridable method
            token = self._exchange_code_for_token(server.auth_code, server.auth_state)
            
            # Save token
            self._save_token(OAuth2Token(token))
            
            # Update session with new token
            self.session.token = self.token
            
            return True
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def _exchange_code_for_token(self, code: str, state: str) -> dict:
        """Exchange authorization code for access token.
        
        This method can be overridden by subclasses to handle API-specific token exchange.
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter from callback
            
        Returns:
            Token dictionary
            
        Raises:
            Exception: If token exchange fails
        """
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        response = requests.post(self.token_endpoint, data=token_data)
        response.raise_for_status()
        return response.json()

    def _is_authentication_error(self, error: Exception, response=None) -> bool:
        """Check if an error indicates authentication failure using the configured strategy.
        
        Args:
            error: The exception that was raised
            response: Optional response object
            
        Returns:
            True if this appears to be an authentication error
        """
        return self.error_strategy.is_authentication_error(error, response)

    def refresh_token_if_needed(self, force: bool = False) -> bool:
        """Refresh token if needed using sliding window approach.
        
        Args:
            force: If True, force refresh even if token appears valid
        
        Returns:
            True if token is valid (either was already valid or successfully refreshed)
        """
        if not self.token:
            return False
            
        # If force is True, skip sliding window checks and refresh immediately
        if force:
            print("🔄 Forcing token refresh...")
        else:
            # Check sliding window validity first
            if self.is_in_sliding_window():
                # Token is within 90-day window, check if we should refresh proactively
                if not self.should_refresh_proactively():
                    return True  # Token is still good
        
        # Token needs refresh - check if we have a refresh token
        if 'refresh_token' not in self.token:
            return False
            
        try:
            # Use overridable method for token refresh
            new_token = self._refresh_access_token()
            
            self._save_token(OAuth2Token(new_token))
            
            # Update session with new token
            self.session.token = self.token
            
            return True
            
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False

    def _refresh_access_token(self) -> dict:
        """Refresh the access token using the refresh token.
        
        This method can be overridden by subclasses to handle API-specific token refresh.
        
        Returns:
            New token dictionary
            
        Raises:
            Exception: If token refresh fails
        """
        refresh_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.token['refresh_token'],
            "grant_type": "refresh_token",
        }
        
        response = requests.post(self.token_endpoint, data=refresh_data)
        response.raise_for_status()
        return response.json()

    def get_valid_token(self) -> Optional[str]:
        """Get a valid access token.
        
        Returns:
            Valid access token or None if authentication failed
        """
        # First check if we're already authenticated (respects sliding window)
        if self.is_authenticated():
            return self.token['access_token']
            
        # If not authenticated, try to refresh token
        if self.refresh_token_if_needed():
            return self.token['access_token']
            
        # If refresh failed, try full authentication
        if self.authenticate():
            return self.token['access_token']
            
        return None

    def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: dict = None,
        json_data: dict = None,
        **kwargs
    ) -> requests.Response:
        """Make an authenticated API request.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            method: HTTP method
            params: Query parameters
            json_data: JSON data for POST/PUT requests
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            Exception: If authentication fails or request fails
        """
        # Ensure we have a valid token
        token = self.get_valid_token()
        if not token:
            raise Exception("Failed to obtain valid access token")
            
        # Ensure session token is up to date
        self.session.token = self.token
            
        # Build full URL
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Make request with automatic retry on auth errors
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    **kwargs
                )
                
                response.raise_for_status()
                
                # Allow error strategy to validate successful responses (e.g., Withings status != 0)
                if hasattr(self.error_strategy, 'validate_response'):
                    self.error_strategy.validate_response(response)
                
                return response
                
            except Exception as e:
                # Check if this is an authentication error
                response_for_error = getattr(e, 'response', None)
                is_auth_error = self._is_authentication_error(e, response_for_error)
                
                # Only retry on auth errors and if we have retries left
                if is_auth_error and attempt < max_retries - 1:
                    print(f"⚠️  Authentication error (attempt {attempt + 1}): {e}")
                    
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
                        raise Exception(f"Failed to re-authenticate: {e}")
                else:
                    # Not an auth error, or out of retries
                    raise
