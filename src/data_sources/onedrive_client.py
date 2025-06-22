"""OneDrive integration for storing analysis results using MSAL device flow authentication."""

import json
import os
from datetime import datetime
from typing import Any, Optional

import msal
import requests
from msal import PublicClientApplication

from src.data_sources.token_manager import TokenManager
from src.utils.logging_utils import HealthLogger
from src.utils.progress_indicators import ProgressIndicator


class OneDriveClient:
    def __init__(self, client_id: str = None):
        """Initialize OneDrive storage with MSAL authentication.

        Args:
            client_id: Optional client ID. If not provided, will look for ONEDRIVE_CLIENT_ID in environment.

        Raises:
            ValueError: If client_id is not provided or found in environment.
        """
        self.client_id = client_id or os.getenv("ONEDRIVE_CLIENT_ID")
        if not self.client_id:
            raise ValueError("OneDrive client ID is required")

        # Microsoft Graph API configuration
        self.tenant_id = "consumers"  # Use 'consumers' for personal accounts
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/Files.ReadWrite"]
        self.base_url = "https://graph.microsoft.com/v1.0"

        self.token_manager = TokenManager(os.path.expanduser("~/.onedrive_tokens.json"))

        # Initialize MSAL token cache
        self.msal_token_cache = msal.SerializableTokenCache()
        # Load existing tokens from TokenManager if available
        cached_tokens_data = self.token_manager.get_tokens()
        if cached_tokens_data and "msal_cache" in cached_tokens_data:
            self.msal_token_cache.deserialize(cached_tokens_data["msal_cache"])

        # Initialize MSAL app
        self.app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.msal_token_cache,  # Use OneDriveClient's own MSAL cache
        )
        self.access_token = None
        self.logger = HealthLogger(__name__)

    def authenticate(self) -> bool:
        """Authenticate with OneDrive using device flow or cached tokens.

        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        try:
            # Try silent acquisition with MSAL
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    self.token_manager.save_tokens(
                        {
                            "msal_cache": self.msal_token_cache.serialize(),
                            "access_token": result["access_token"],
                            "expires_in": result.get("expires_in", 3600),
                        }
                    )  # Save serialized cache
                    self.access_token = result["access_token"]
                    return True

            # If silent acquisition fails, initiate device flow
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            if "user_code" not in flow:
                raise Exception("Failed to start device flow")

            # Show instructions to user using ProgressIndicator for consistent UI
            ProgressIndicator.bullet_item(
                f"[OneDrive Auth] Please visit this URL to authorize the application: {flow['verification_uri']}"
            )
            ProgressIndicator.bullet_item(
                f"[OneDrive Auth] Enter the code: {flow['user_code']}"
            )
            ProgressIndicator.bullet_item("Waiting for authentication...")
            
            # Wait for user to complete authentication
            result = self.app.acquire_token_by_device_flow(flow)

            if "access_token" not in result:
                self.logger.error("Authentication failed")
                return False

            self.token_manager.save_tokens(
                {
                    "msal_cache": self.msal_token_cache.serialize(),
                    "access_token": result["access_token"],
                    "expires_in": result.get("expires_in", 3600),
                }
            )  # Save serialized cache
            self.access_token = result["access_token"]
            # Log success to debug only - progress indicators will show success elsewhere
            self.logger.debug("Successfully authenticated with OneDrive!")
            ProgressIndicator.step_complete("OneDrive authentication successful")
            return True

        except Exception as e:
            self.logger.error(f"Error during authentication: {str(e)}")
            return False

    def _get_token(self) -> str:
        """Get a valid access token.

        Returns:
            str: Access token

        Raises:
            ValueError: If no valid token is available
        """
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                self.token_manager.save_tokens(
                    {
                        "msal_cache": self.msal_token_cache.serialize(),
                        "access_token": result["access_token"],
                        "expires_in": result.get("expires_in", 3600),
                    }
                )  # Save serialized cache
                return result["access_token"]

        if not self.authenticate():
            raise ValueError("Failed to get access token")

        # After successful authentication, the token should be in the cache
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                return result["access_token"]

        raise ValueError("Failed to retrieve access token after authentication")

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
