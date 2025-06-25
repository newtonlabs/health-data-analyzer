"""OneDrive service for storing analysis results using MSAL device flow authentication."""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import msal
import requests
from msal import PublicClientApplication

from src.api.services.base_service import BaseAPIService


class OneDriveService(BaseAPIService):
    """OneDrive service for storing analysis results using MSAL device flow authentication."""

    def __init__(
        self, 
        client_id: Optional[str] = None, 
        client_secret: Optional[str] = None, 
        token_file: Optional[str] = None
    ):
        """Initialize OneDrive service with MSAL authentication.

        Args:
            client_id: Optional client ID. If not provided, will look for ONEDRIVE_CLIENT_ID in environment.
            client_secret: Optional client secret. Not required for OneDrive but included for API consistency.
            token_file: Optional path to token storage file.

        Raises:
            ValueError: If client_id is not provided or found in environment.
        """
        super().__init__(
            base_url="https://graph.microsoft.com/v1.0",
            service_name="onedrive"
        )

        # Get credentials from parameters or environment
        self.client_id = client_id or os.getenv("ONEDRIVE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("ONEDRIVE_CLIENT_SECRET")
        
        if not self.client_id:
            raise ValueError(
                "Client ID is required. Set ONEDRIVE_CLIENT_ID environment variable."
            )

        # Microsoft Graph API configuration
        self.tenant_id = "consumers"  # Use 'consumers' for personal accounts
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/Files.ReadWrite"]

        # Initialize MSAL token cache
        self.msal_token_cache = msal.SerializableTokenCache()
        
        # Set up token storage
        from src.utils.token_manager import TokenManager
        self.token_manager = TokenManager(
            token_file or os.path.expanduser("~/.onedrive_tokens.json")
        )

        # Load existing token cache if available
        self._load_token_cache()

        # Initialize MSAL app
        self.msal_app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.msal_token_cache,
        )

    def _load_token_cache(self) -> None:
        """Load token cache from file if it exists."""
        try:
            saved_tokens = self.token_manager.get_tokens()
            if saved_tokens and "msal_cache" in saved_tokens:
                self.msal_token_cache.deserialize(saved_tokens["msal_cache"])
                self.logger.debug("Loaded MSAL token cache from file")
        except Exception as e:
            self.logger.debug(f"Could not load token cache: {e}")

    def _save_token_cache(self) -> None:
        """Save token cache to file."""
        try:
            cache_data = self.msal_token_cache.serialize()
            if cache_data:
                self.token_manager.save_tokens({"msal_cache": cache_data})
                self.logger.debug("Saved MSAL token cache to file")
        except Exception as e:
            self.logger.warning(f"Could not save token cache: {e}")

    def authenticate(self) -> bool:
        """Authenticate with OneDrive using MSAL device flow.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Try to get token silently first
            accounts = self.msal_app.get_accounts()
            if accounts:
                self.logger.info("Found existing account, attempting silent authentication")
                result = self.msal_app.acquire_token_silent(
                    scopes=self.scopes, account=accounts[0]
                )
                if result and "access_token" in result:
                    self.access_token = result["access_token"]
                    self._save_token_cache()
                    self.logger.info("Silent authentication successful")
                    return True

            # If silent auth fails, use device flow
            self.logger.info("Starting device flow authentication")
            flow = self.msal_app.initiate_device_flow(scopes=self.scopes)

            if "user_code" not in flow:
                raise Exception("Failed to create device flow")

            # Display user code and URL
            print(f"\nTo authenticate with OneDrive:")
            print(f"1. Go to: {flow['verification_uri']}")
            print(f"2. Enter code: {flow['user_code']}")
            print("3. Complete authentication in your browser")
            print("Waiting for authentication...")

            # Wait for user to complete authentication
            result = self.msal_app.acquire_token_by_device_flow(flow)

            if "access_token" in result:
                self.access_token = result["access_token"]
                self._save_token_cache()
                self.logger.info("Device flow authentication successful")
                return True
            else:
                error = result.get("error_description", "Unknown error")
                self.logger.error(f"Authentication failed: {error}")
                return False

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False

    def refresh_access_token(self) -> bool:
        """Refresh the access token using MSAL.

        Returns:
            True if refresh successful, False otherwise
        """
        try:
            accounts = self.msal_app.get_accounts()
            if not accounts:
                self.logger.warning("No accounts found for token refresh")
                return False

            result = self.msal_app.acquire_token_silent(
                scopes=self.scopes, account=accounts[0]
            )

            if result and "access_token" in result:
                self.access_token = result["access_token"]
                self._save_token_cache()
                self.logger.info("Token refresh successful")
                return True
            else:
                self.logger.warning("Token refresh failed")
                return False

        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return False

    def _prepare_request_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests.
        
        Returns:
            Dictionary of headers to include in requests
        """
        if not self.access_token:
            # Try to refresh token
            if not self.refresh_access_token():
                raise Exception("No valid access token available")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _ensure_folder_path(self, folder_path: str) -> str:
        """Ensure folder path exists in OneDrive.

        Args:
            folder_path: Path to the folder

        Returns:
            OneDrive item ID of the folder

        Raises:
            Exception: If folder creation fails
        """
        try:
            # Check if folder exists
            response = self._make_request(
                method="GET",
                endpoint=f"me/drive/root:/{folder_path}"
            )
            return response["id"]

        except Exception:
            # Folder doesn't exist, create it
            return self.create_folder(folder_path)

    def create_folder(self, folder_path: str) -> str:
        """Create a folder in OneDrive.

        Args:
            folder_path: Path where to create the folder

        Returns:
            OneDrive item ID of the created folder
        """
        folder_data = {
            "name": os.path.basename(folder_path),
            "folder": {},
            "@microsoft.graph.conflictBehavior": "replace"
        }

        parent_path = os.path.dirname(folder_path)
        if parent_path:
            endpoint = f"me/drive/root:/{parent_path}:/children"
        else:
            endpoint = "me/drive/root/children"

        response = self._make_request(
            method="POST",
            endpoint=endpoint,
            json=folder_data
        )
        
        return response["id"]

    def upload_file(self, file_path: str, folder_name: Optional[str] = None) -> str:
        """Upload a file to OneDrive.

        Args:
            file_path: Local path to the file to upload
            folder_name: Optional folder name in OneDrive

        Returns:
            OneDrive URL of the uploaded file

        Raises:
            Exception: If upload fails
        """
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        
        # Determine upload path
        if folder_name:
            folder_id = self._ensure_folder_path(folder_name)
            upload_endpoint = f"me/drive/items/{folder_id}:/{filename}:/content"
        else:
            upload_endpoint = f"me/drive/root:/{filename}:/content"

        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Upload file
        headers = self._prepare_request_headers()
        headers["Content-Type"] = "application/octet-stream"

        response = self._make_request(
            method="PUT",
            endpoint=upload_endpoint,
            data=file_content,
            headers=headers
        )

        web_url = response.get("webUrl", "")
        self.logger.info(f"File uploaded successfully: {web_url}")
        return web_url

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return bool(self.access_token) or bool(self.msal_app.get_accounts())
