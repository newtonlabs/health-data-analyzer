"""OneDrive client using MSAL with 90-day token persistence."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict

import msal
import requests
from msal import PublicClientApplication

from .base.oauth2_auth_base import TokenFileManager, SlidingWindowValidator
from .base.config import ClientFactory


class OneDriveClient:
    """OneDrive client using MSAL with simplified 90-day authentication."""

    # Constants
    SECONDS_PER_DAY = 24 * 3600

    def __init__(self):
        """Initialize the OneDrive client.
        
        Reads ONEDRIVE_CLIENT_ID from environment variables.
        Client secret is not needed for OneDrive public client applications.
        Uses shared utilities for configuration and token management.
        """
        # Initialize shared utilities
        self.token_manager = TokenFileManager("onedrive")
        self.sliding_window = SlidingWindowValidator()
        
        # Get credentials from environment
        self.client_id = os.getenv("ONEDRIVE_CLIENT_ID")
        
        if not self.client_id:
            raise ValueError("Environment variable ONEDRIVE_CLIENT_ID is required")

        # Get service configuration
        service_config = ClientFactory.get_service_config("onedrive")
        client_config = ClientFactory.get_client_config()
        
        # Microsoft Graph API configuration
        self.tenant_id = "consumers"  # Use 'consumers' for personal accounts
        self.authority = service_config["authority"]
        self.scopes = service_config["scopes"]
        self.base_url = service_config["base_url"]
        
        # Token validity configuration using shared config
        self.validity_days = client_config.validity_days
        self.refresh_buffer_hours = client_config.refresh_buffer_hours
        
        # Token storage using shared token manager
        self.token_file = self.token_manager.token_file
        self.token = None
        self.access_token = None
        
        # Initialize MSAL token cache
        self.msal_token_cache = msal.SerializableTokenCache()
        
        # MSAL app will be initialized lazily when needed
        self.app = None
        
        # Load existing token if available
        self._load_token()

    def _ensure_msal_app(self) -> None:
        """Initialize MSAL app if not already done."""
        if self.app is None:
            self.app = PublicClientApplication(
                client_id=self.client_id,
                authority=self.authority,
                token_cache=self.msal_token_cache,
            )

    def _load_token(self) -> bool:
        """Load token from file using shared token manager.
        
        Returns:
            True if token was loaded successfully
        """
        token_data = self.token_manager.load_token()
        if not token_data:
            return False
            
        # Load MSAL cache if available
        if "msal_cache" in token_data:
            self.msal_token_cache.deserialize(token_data["msal_cache"])
        
        # Load access token
        if "access_token" in token_data:
            self.access_token = token_data["access_token"]
            
        self.token = token_data
        return True

    def _save_token(self, token_data: dict) -> None:
        """Save token to file."""
        # Add MSAL cache to extra data
        extra_data = {"msal_cache": self.msal_token_cache.serialize()}
        
        # Use shared token manager
        client_config = ClientFactory.get_client_config()
        self.token_manager.save_token(token_data, client_config, extra_data)
        self.token = {**token_data, **extra_data}

    def is_authenticated(self) -> bool:
        """Check if we have a valid authentication."""
        if not self.token or not self.access_token:
            return False
            
        # Use shared sliding window validation
        return SlidingWindowValidator.is_in_sliding_window(self.token)

    def is_in_sliding_window(self) -> bool:
        """Check if we're within the 90-day sliding window."""
        return self.sliding_window.is_in_sliding_window(self.token)

    def should_refresh_proactively(self) -> bool:
        """Check if we should refresh the token proactively."""
        client_config = ClientFactory.get_client_config()
        return self.sliding_window.should_refresh_proactively(
            self.token, client_config.refresh_buffer_hours
        )

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
        client_config = ClientFactory.get_client_config()
        should_refresh = self.sliding_window.should_refresh_proactively(
            token_data, client_config.refresh_buffer_hours
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
        self.access_token = None

    def authenticate(self) -> bool:
        """Authenticate with OneDrive using MSAL device code flow.
        
        Returns:
            bool: True if authentication was successful
        """
        # Ensure MSAL app is initialized
        self._ensure_msal_app()
        
        # Start device code flow
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        
        if "user_code" not in flow:
            return False
        
        # Display instructions to user (ESSENTIAL for device code flow)
        print(f"Please visit this URL to authorize the application:")
        print(f"🔗 {flow['verification_uri']}")
        print(f"📱 Enter the code: {flow['user_code']}")
        print()
        print("Waiting for authorization...")
        
        # Wait for user to complete the flow
        result = self.app.acquire_token_by_device_flow(flow)
        
        if "access_token" not in result:
            return False
        
        # Calculate extended expiration (90 days from now)
        expires_in = result.get("expires_in", 3600)
        extended_expires_in = self.validity_days * self.SECONDS_PER_DAY
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # Save tokens
        token_data = {
            "access_token": result["access_token"],
            "token_type": result.get("token_type", "Bearer"),
            "expires_in": expires_in,
            "extended_expires_in": extended_expires_in,
            "expires_at": expires_at.timestamp(),
        }
        
        self._save_token(token_data)
        self.access_token = result["access_token"]
        
        print("✅ OneDrive authentication successful!")
        return True

    def refresh_token_if_needed(self, force: bool = False) -> bool:
        """Refresh token if needed using MSAL silent acquisition.
        
        Args:
            force: Force refresh even if not needed
            
        Returns:
            bool: True if refresh was successful or not needed
        """
        if not force and not self.should_refresh_proactively():
            return True
            
        # Ensure MSAL app is initialized
        self._ensure_msal_app()
        
        # Get accounts from MSAL cache
        accounts = self.app.get_accounts()
        
        if not accounts:
            return False
        
        # Try silent token acquisition
        result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
        
        if result and "access_token" in result:
            # Calculate new expiration
            expires_in = result.get("expires_in", 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Update token data
            token_data = self.token.copy() if self.token else {}
            token_data.update({
                "access_token": result["access_token"],
                "token_type": result.get("token_type", "Bearer"),
                "expires_in": expires_in,
                "expires_at": expires_at.timestamp(),
                "last_refresh": datetime.now().isoformat()
            })
            
            self._save_token(token_data)
            self.access_token = result["access_token"]
            
            return True
        else:
            return False

    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token
            
        Raises:
            Exception: If no valid token can be obtained
        """
        # Check if we need to authenticate
        if not self.is_authenticated():
            if not self.authenticate():
                raise Exception("Authentication failed")
        
        # Try to refresh if needed
        if self.should_refresh_proactively():
            self.refresh_token_if_needed()
        
        if not self.access_token:
            raise Exception("No valid access token available")
            
        return self.access_token

    def make_request(self, endpoint: str, method: str = "GET", **kwargs) -> requests.Response:
        """Make an authenticated request to Microsoft Graph API.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            method: HTTP method
            **kwargs: Additional arguments passed to requests
            
        Returns:
            Response object
            
        Raises:
            Exception: If request fails after retry
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add authorization header
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self._get_access_token()}"
        kwargs["headers"] = headers
        
        # Make request
        response = requests.request(method, url, **kwargs)
        
        # Check for authentication errors and retry once
        if response.status_code == 401:
            if self.refresh_token_if_needed(force=True):
                headers["Authorization"] = f"Bearer {self._get_access_token()}"
                kwargs["headers"] = headers
                response = requests.request(method, url, **kwargs)
            else:
                raise Exception("Authentication failed and refresh unsuccessful")
        
        return response

    def upload_file(self, file_path: str, folder_name: str = None) -> str:
        """Upload a file to OneDrive.
        
        Args:
            file_path: Path to the file to upload
            folder_name: Optional folder name to upload to
            
        Returns:
            str: Shareable URL to the uploaded file
            
        Raises:
            Exception: If upload fails
        """
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        
        # Determine upload URL
        if folder_name:
            # Create folder if it doesn't exist
            self._ensure_folder_exists(folder_name)
            upload_endpoint = f"me/drive/root:/{folder_name}/{filename}:/content"
        else:
            upload_endpoint = f"me/drive/root:/{filename}:/content"
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Upload file
        response = self.make_request(upload_endpoint, method="PUT", data=file_content)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Upload failed: {response.text}")
        
        file_id = response.json()["id"]
        
        # Create sharing link
        response = self.make_request(
            f"me/drive/items/{file_id}/createLink",
            method="POST",
            json={"type": "view", "scope": "anonymous"}
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create sharing link: {response.text}")
        
        share_url = response.json()["link"]["webUrl"]
        
        return share_url

    def _ensure_folder_exists(self, folder_name: str) -> None:
        """Ensure a folder exists in OneDrive, creating if necessary.
        
        Args:
            folder_name: Name of the folder to ensure exists
        """
        # Check if folder exists
        response = self.make_request(f"me/drive/root:/{folder_name}")
        
        if response.status_code == 404:
            # Create folder
            response = self.make_request(
                "me/drive/root/children",
                method="POST",
                json={
                    "name": folder_name,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "replace"
                }
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to create folder: {response.text}")
        
        elif response.status_code != 200:
            raise Exception(f"Error checking folder: {response.text}")

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file in OneDrive.
        
        Args:
            file_path: Path to the file in OneDrive (e.g., "folder/file.txt")
            
        Returns:
            dict: File information from Microsoft Graph API
        """
        response = self.make_request(f"me/drive/root:/{file_path}")
        
        if response.status_code == 404:
            raise Exception(f"File not found: {file_path}")
        elif response.status_code != 200:
            raise Exception(f"Error getting file info: {response.text}")
        
        return response.json()

    def list_files(self, folder_name: str = None) -> list[Dict[str, Any]]:
        """List files in OneDrive.
        
        Args:
            folder_name: Optional folder name to list. If None, lists root folder.
            
        Returns:
            list: List of file information dictionaries
        """
        if folder_name:
            endpoint = f"me/drive/root:/{folder_name}:/children"
        else:
            endpoint = "me/drive/root/children"
        
        response = self.make_request(endpoint)
        
        if response.status_code != 200:
            raise Exception(f"Error listing files: {response.text}")
        
        return response.json().get("value", [])
