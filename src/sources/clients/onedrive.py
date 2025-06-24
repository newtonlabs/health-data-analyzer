"""OneDrive integration for storing analysis results using MSAL device flow authentication."""

import json
import os
from datetime import datetime
from typing import Any, Optional

import msal
import requests
from msal import PublicClientApplication

from src.sources.base import APIClient, APIClientError
from src.utils.progress_indicators import ProgressIndicator


class OneDriveClient(APIClient):
    """OneDrive client for storing analysis results using MSAL device flow authentication."""

    def __init__(
        self, client_id: str = None, client_secret: str = None, token_file: str = None
    ):
        """Initialize OneDrive storage with MSAL authentication.

        Args:
            client_id: Optional client ID. If not provided, will look for ONEDRIVE_CLIENT_ID in environment.
            client_secret: Optional client secret. Not required for OneDrive but included for API consistency.
            token_file: Optional path to token storage file.

        Raises:
            ValueError: If client_id is not provided or found in environment.
        """
        # Initialize base class
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file,
            env_client_id="ONEDRIVE_CLIENT_ID",
            env_client_secret="ONEDRIVE_CLIENT_SECRET",
            default_token_path="~/.onedrive_tokens.json",
            base_url="https://graph.microsoft.com/v1.0",
        )

        # Microsoft Graph API configuration
        self.tenant_id = "consumers"  # Use 'consumers' for personal accounts
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/Files.ReadWrite"]

        # Initialize MSAL token cache
        self.msal_token_cache = msal.SerializableTokenCache()

        # Try to load cached tokens
        cached_tokens_data = self.token_manager.get_tokens()
        if cached_tokens_data and "msal_cache" in cached_tokens_data:
            try:
                self.msal_token_cache.deserialize(cached_tokens_data["msal_cache"])
                self.logger.debug("Loaded MSAL token cache from file")
                
                # Extract access token from cached tokens
                if "access_token" in cached_tokens_data:
                    self.access_token = cached_tokens_data["access_token"]
                    self.token_type = cached_tokens_data.get("token_type", "Bearer")
                    self.expires_in = cached_tokens_data.get("expires_in", 3600)
                    self.logger.debug("Loaded access token from cache")
            except Exception as e:
                self.logger.warning(f"Failed to load MSAL token cache: {e}")

        # Initialize MSAL app with the token cache
        self.app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.msal_token_cache,
        )

    def authenticate(self) -> bool:
        """Authenticate with OneDrive using MSAL device code flow.

        Returns:
            bool: True if authentication was successful, False otherwise
        """
        # Try to use existing tokens first
        if super().handle_authentication():
            self.logger.info("Using existing OneDrive authentication")
            return True

        # Start device code flow
        self.logger.info("Starting new OneDrive authentication flow")
        flow = self.app.initiate_device_flow(scopes=self.scopes)

        if "user_code" not in flow:
            self.logger.error(
                f"Failed to start device code flow: {flow.get('error', 'Unknown error')}"
            )
            return False

        # Display instructions to user
        ProgressIndicator.bullet_item(
            f"[OneDrive Auth] Please visit this URL to authorize the application: {flow['verification_uri']}"
        )
        ProgressIndicator.bullet_item(
            f"[OneDrive Auth] Enter the code: {flow['user_code']}"
        )

        # Wait for user to complete the flow
        result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            self.logger.error(
                f"Failed to acquire token: {result.get('error', 'Unknown error')}"
            )
            return False

        # Use extended expiration (7 days)
        original_expires_in = result.get("expires_in", 3600)
        extended_expires_in = 7 * 24 * 3600  # 7 days in seconds
        
        # Save tokens with extended expiration
        self.token_manager.save_tokens(
            {
                "msal_cache": self.msal_token_cache.serialize(),
                "access_token": result["access_token"],
                "refresh_token": None,  # MSAL handles refresh internally
                "token_type": result.get("token_type", "Bearer"),
                "expires_in": extended_expires_in,  # Use extended expiration
                "original_expires_in": original_expires_in,  # Store original for reference
            }
        )

        # Update instance variables
        self.access_token = result["access_token"]
        self.token_type = result.get("token_type", "Bearer")
        self.expires_in = extended_expires_in

        # Use step_complete instead of checkmark
        ProgressIndicator.step_complete("OneDrive authentication successful")
        self.logger.info(f"OneDrive authentication successful, token valid for 7 days")
        return True

    def refresh_access_token(self) -> bool:
        """Refresh the access token using MSAL's silent token acquisition.

        Returns:
            bool: True if refresh was successful, False otherwise
        """
        self.logger.info("Refreshing OneDrive access token")

        try:
            # MSAL handles token refresh differently - it uses the token cache
            accounts = self.app.get_accounts()
            
            # Log account information for debugging
            self.logger.debug(f"Found {len(accounts)} accounts in MSAL cache")
            for i, account in enumerate(accounts):
                self.logger.debug(f"Account {i}: {account.get('username', 'unknown')}")
            
            if not accounts:
                self.logger.warning("No accounts found in MSAL cache")
                return False

            # Try silent token acquisition with extended timeout
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            
            if result and "access_token" in result:
                # Log success with token expiration time
                expires_in = result.get("expires_in", 3600)
                self.logger.info(f"Successfully refreshed token, expires in {expires_in} seconds")
                
                # Update tokens with extended expiration (7 days)
                extended_expires_in = 7 * 24 * 3600  # 7 days in seconds
                
                self.token_manager.save_tokens(
                    {
                        "msal_cache": self.msal_token_cache.serialize(),
                        "access_token": result["access_token"],
                        "refresh_token": None,  # MSAL handles refresh internally
                        "token_type": "Bearer",
                        "expires_in": extended_expires_in,  # Use extended expiration
                        "original_expires_in": expires_in,  # Store original for reference
                    }
                )
                self.access_token = result["access_token"]
                self.token_type = "Bearer"
                self.expires_in = extended_expires_in
                return True
            else:
                # Log more details about the failure
                error = result.get("error") if result else "No result"
                error_desc = result.get("error_description") if result else "No error description"
                self.logger.warning(f"Silent token acquisition failed: {error} - {error_desc}")
                
                # Try to recover by clearing the token cache and forcing re-authentication
                self.logger.info("Attempting to recover by clearing token cache")
                self.msal_token_cache.clear()
                return False
        except Exception as e:
            self.logger.error(f"Error refreshing token: {str(e)}")
            # Add more detailed error information
            import traceback
            self.logger.debug(f"Token refresh error details: {traceback.format_exc()}")
            return False

    def _get_token(self) -> str:
        """Get a valid access token.

        Returns:
            str: Access token

        Raises:
            ValueError: If no valid token is available
        """
        try:
            # Use the base class implementation
            return self._get_access_token()
        except APIClientError as e:
            # Convert APIClientError to ValueError for backward compatibility
            raise ValueError(f"Failed to get access token: {str(e)}")

    def _ensure_folder_path(self, folder_path: str) -> str:
        """Ensure a folder path exists in OneDrive, creating any missing folders.

        Args:
            folder_path: Path to ensure exists (e.g. 'Health Data/2025-06-15')

        Returns:
            ID of the final folder in the path

        Raises:
            Exception: If folder creation fails
        """
        parts = folder_path.split("/")
        current_path = ""
        parent_id = None

        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part

            # Check if folder exists
            headers = {"Authorization": f"Bearer {self._get_token()}"}
            response = requests.get(
                f"{self.base_url}/me/drive/root:/{current_path}", headers=headers
            )

            if response.status_code == 200:
                # Folder exists, get its ID
                parent_id = response.json()["id"]
            else:
                # Create folder
                headers["Content-Type"] = "application/json"
                folder_data = {
                    "name": part,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "replace",
                }

                if parent_id:
                    # Create in parent folder
                    response = requests.post(
                        f"{self.base_url}/me/drive/items/{parent_id}/children",
                        headers=headers,
                        json=folder_data,
                    )
                else:
                    # Create in root
                    response = requests.post(
                        f"{self.base_url}/me/drive/root/children",
                        headers=headers,
                        json=folder_data,
                    )

                if response.status_code not in [200, 201]:
                    raise Exception(
                        f"Failed to create folder '{part}': {response.text}"
                    )

                parent_id = response.json()["id"]

        return parent_id

    def create_folder(self, folder_path: str) -> str:
        """Create a folder in OneDrive, including parent folders.

        Args:
            folder_path: Path to create (e.g. 'Health Data/2025-06-15')

        Returns:
            ID of the created folder
        """
        return self._ensure_folder_path(folder_path)

    def upload_file(self, file_path: str, folder_name: str = None) -> str:
        """Upload a file to OneDrive.

        Args:
            file_path: Path to the file to upload
            folder_name: Optional folder name to upload to

        Returns:
            URL to the uploaded file
        """
        # Token validity is checked by _get_token

        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")

        filename = os.path.basename(file_path)

        # Create folder structure if needed
        if folder_name:
            folder_id = self.create_folder(folder_name)

            # Upload file to folder
            with open(file_path, "rb") as f:
                file_content = f.read()

            upload_url = (
                f"{self.base_url}/me/drive/items/{folder_id}:/{filename}:/content"
            )
        else:
            # Upload file to root
            with open(file_path, "rb") as f:
                file_content = f.read()

            upload_url = f"{self.base_url}/me/drive/root:/{filename}:/content"

        # Upload the file
        response = requests.put(
            upload_url,
            headers={"Authorization": f"Bearer {self._get_token()}"},
            data=file_content,
        )
        response.raise_for_status()
        file_id = response.json()["id"]

        # Get sharing link
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{self.base_url}/me/drive/items/{file_id}/createLink",
            headers=headers,
            json={"type": "view", "scope": "anonymous"},
        )
        response.raise_for_status()

        return response.json()["link"]["webUrl"]
