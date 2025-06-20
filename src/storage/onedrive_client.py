"""OneDrive integration for storing analysis results using MSAL device flow authentication."""
import os
import json
import requests
import msal
from datetime import datetime
from typing import Dict, Any, Optional
from msal import PublicClientApplication

class OneDriveClient:
    def __init__(self, client_id: str = None):
        """Initialize OneDrive storage with MSAL authentication.
        
        Args:
            client_id: Optional client ID. If not provided, will look for ONEDRIVE_CLIENT_ID in environment.
        
        Raises:
            ValueError: If client_id is not provided or found in environment.
        """
        self.client_id = client_id or os.getenv('ONEDRIVE_CLIENT_ID')
        if not self.client_id:
            raise ValueError("OneDrive client ID is required")
        
        # Microsoft Graph API configuration
        self.tenant_id = "consumers"  # Use 'consumers' for personal accounts
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/Files.ReadWrite"]
        self.base_url = "https://graph.microsoft.com/v1.0"
        
        # Initialize MSAL app with token cache
        self.token_cache = msal.SerializableTokenCache()
        
        # Load cached tokens if available
        cache_file = os.path.expanduser('~/.onedrive_token_cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                self.token_cache.deserialize(f.read())
                
        # Initialize MSAL app with token cache
        self.app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.token_cache
        )
        
        # Save token cache to file
        if self.token_cache.has_state_changed:
            with open(cache_file, 'w') as f:
                f.write(self.token_cache.serialize())
                
        self.access_token = None
        
    def authenticate(self) -> bool:
        """Authenticate with OneDrive using device flow or cached tokens.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        try:
            # Try to get token silently
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result:
                    self.access_token = result['access_token']
                    return True
                
            # Try to get a new token using device flow
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result:
                    self.access_token = result['access_token']
                    print("✓ Successfully authenticated with OneDrive using cached token!")
                    return True
            
            # If no cached token, start device flow
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            if 'user_code' not in flow:
                raise Exception("Failed to start device flow")
            
            # Show instructions to user
            print(f"\nTo authenticate with OneDrive, please:")
            print(f"1. Go to: {flow['verification_uri']}")
            print(f"2. Enter the code: {flow['user_code']}")
            print("\nWaiting for authentication...")
            
            # Wait for user to complete authentication
            result = self.app.acquire_token_by_device_flow(flow)
            
            if "access_token" not in result:
                print("Authentication failed")
                return False
            
            self.access_token = result['access_token']
            
            # Save token cache
            cache_file = os.path.expanduser('~/.onedrive_token_cache.json')
            with open(cache_file, 'w') as f:
                f.write(self.token_cache.serialize())
            
            print("✓ Successfully authenticated with OneDrive!")
            return True
            
        except Exception as e:
            print(f"Error during authentication: {str(e)}")
            return False
    
    def _get_token(self) -> str:
        """Get a valid access token.
        
        Returns:
            str: Access token
            
        Raises:
            ValueError: If no valid token is available
        """
        # Try to get token silently first
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result:
                return result['access_token']
                
        # If no token or expired, authenticate
        if not self.authenticate():
            raise ValueError("Failed to get access token")
            
        return self.access_token

    def _ensure_folder_path(self, folder_path: str) -> str:
        """Ensure a folder path exists in OneDrive, creating any missing folders.
        
        Args:
            folder_path: Path to ensure exists (e.g. 'Health Data/2025-06-15')
            
        Returns:
            ID of the final folder in the path
            
        Raises:
            Exception: If folder creation fails
        """
        parts = folder_path.split('/')
        current_path = ""
        parent_id = None
        
        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part
            
            # Check if folder exists
            headers = {"Authorization": f"Bearer {self._get_token()}"}
            response = requests.get(
                f"{self.base_url}/me/drive/root:/{current_path}",
                headers=headers
            )
            
            if response.status_code == 200:
                # Folder exists, get its ID
                parent_id = response.json()['id']
            else:
                # Create folder
                headers["Content-Type"] = "application/json"
                folder_data = {
                    "name": part,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "replace"
                }
                
                if parent_id:
                    # Create in parent folder
                    response = requests.post(
                        f"{self.base_url}/me/drive/items/{parent_id}/children",
                        headers=headers,
                        json=folder_data
                    )
                else:
                    # Create in root
                    response = requests.post(
                        f"{self.base_url}/me/drive/root/children",
                        headers=headers,
                        json=folder_data
                    )
                
                if response.status_code not in [200, 201]:
                    raise Exception(f"Failed to create folder '{part}': {response.text}")
                    
                parent_id = response.json()['id']
        
        return parent_id
        
    def create_folder(self, folder_path: str) -> str:
        """Create a folder in OneDrive, including parent folders.
        
        Args:
            folder_path: Path to create (e.g. 'Health Data/2025-06-15')
            
        Returns:
            ID of the created folder
        """
        return self._ensure_folder_path(folder_path)
    
    def create_folder_link(self, folder_path: str) -> str:
        """Create a sharing link for a folder in OneDrive.
        
        Args:
            folder_path: Path to the folder (e.g. 'Health Data/2025-06-15')
            
        Returns:
            Sharing URL for the folder
            
        Raises:
            Exception: If folder doesn't exist or link creation fails
        """
        folder_id = self._ensure_folder_path(folder_path)
        
        # Create sharing link
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{self.base_url}/me/drive/items/{folder_id}/createLink",
            headers=headers,
            json={
                'type': 'view',
                'scope': 'anonymous'
            }
        )
        response.raise_for_status()
        
        result = response.json()
        if not isinstance(result, dict):
            raise Exception(f"Invalid response format: {response.text}")
        
        link_data = result.get('link', {})
        web_url = link_data.get('webUrl')
        if not web_url:
            raise Exception(f"No web URL in response: {response.text}")
            
        return web_url

    def store_analysis(self, analysis_data: Dict[str, Any], filename: str = None) -> str:
        """Store analysis results in OneDrive.
        
        Args:
            analysis_data: Dictionary containing analysis results
            filename: Optional filename, will generate one if not provided
            
        Returns:
            str: URL of the uploaded file
            
        Raises:
            Exception: If upload fails
        """
        # Token validity is checked by _get_token
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_analysis_{timestamp}.json"
        
        # Create health-analysis folder
        folder_path = "health-analysis"
        folder_id = self.create_folder(folder_path)
        
        # Upload file to folder
        file_content = json.dumps(analysis_data, indent=2)
        upload_url = f"{self.base_url}/me/drive/items/{folder_id}:/{filename}:/content"
        
        response = requests.put(
            upload_url,
            headers={"Authorization": f"Bearer {self._get_token()}"},
            data=file_content.encode('utf-8')
        )
        response.raise_for_status()
        
        # Get file ID from upload response
        file_id = response.json()['id']
        
        # Create sharing link
        response = requests.post(
            f"{self.base_url}/me/drive/items/{file_id}/createLink",
            headers={"Authorization": f"Bearer {self._get_token()}", "Content-Type": "application/json"},
            json={
                'type': 'view',
                'scope': 'anonymous'
            }
        )
        response.raise_for_status()
        
        result = response.json()
        if not isinstance(result, dict):
            raise Exception(f"Invalid response format: {response.text}")
        
        link_data = result.get('link', {})
        web_url = link_data.get('webUrl')
        if not web_url:
            raise Exception(f"No web URL in response: {response.text}")
            
        return web_url

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
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            upload_url = f"{self.base_url}/me/drive/items/{folder_id}:/{filename}:/content"
        else:
            # Upload file to root
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            upload_url = f"{self.base_url}/me/drive/root:/{filename}:/content"
        
        # Upload the file
        response = requests.put(
            upload_url,
            headers={"Authorization": f"Bearer {self._get_token()}"},
            data=file_content
        )
        response.raise_for_status()
        file_id = response.json()['id']
        
        # Get sharing link
        headers = {"Authorization": f"Bearer {self._get_token()}", "Content-Type": "application/json"}
        response = requests.post(
            f"{self.base_url}/me/drive/items/{file_id}/createLink",
            headers=headers,
            json={
                'type': 'view',
                'scope': 'anonymous'
            }
        )
        response.raise_for_status()
        
        return response.json()['link']['webUrl']

    def get_analysis(self, filename: str) -> Dict[str, Any]:
        """Retrieve analysis results from OneDrive.
        
        Args:
            filename: Name of the file to retrieve
            
        Returns:
            Dict[str, Any]: The analysis data
            
        Raises:
            Exception: If file retrieval fails
        """
        # Token validity is checked by _get_token
        
        # Get file content
        download_url = f"{self.base_url}/me/drive/root:/health-analysis/{filename}:/content"
        response = requests.get(
            download_url,
            headers={"Authorization": f"Bearer {self._get_token()}"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve file: {response.text}")
        
        return json.loads(response.text)
