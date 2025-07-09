"""OneDrive API service for cloud storage operations."""

from datetime import date
from typing import Dict, Any, Optional

from experiments.services.base_service import BaseAPIService
from experiments.clients.onedrive_client import OneDriveClient


class OneDriveService(BaseAPIService):
    """Service for OneDrive API communication.
    
    This service provides a clean interface to OneDrive operations while delegating
    all actual API communication to the existing OneDriveClient.
    """

    def __init__(self):
        """Initialize the OneDrive service."""
        self.onedrive_client = OneDriveClient()
        super().__init__(self.onedrive_client)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.onedrive_client.is_authenticated()

    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Dict[str, Any]:
        """Create a folder in OneDrive.

        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Optional parent folder ID

        Returns:
            Raw API response containing folder creation result
        """
        return self.onedrive_client.create_folder(folder_name, parent_folder_id)

    def upload_file(self, file_path: str, remote_path: str) -> Dict[str, Any]:
        """Upload a file to OneDrive.

        Args:
            file_path: Local path to the file to upload
            remote_path: Remote path where the file should be stored

        Returns:
            Raw API response containing upload result
        """
        return self.onedrive_client.upload_file(file_path, remote_path)

    def list_files(self, folder_id: str = None) -> Dict[str, Any]:
        """List files in a OneDrive folder.

        Args:
            folder_id: Optional folder ID (defaults to root)

        Returns:
            Raw API response containing file list
        """
        return self.onedrive_client.list_files(folder_id)

    def fetch_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Fetch OneDrive information (not date-based).
        
        Args:
            start_date: Not used for OneDrive (included for interface consistency)
            end_date: Not used for OneDrive (included for interface consistency)
            
        Returns:
            Dictionary containing OneDrive information
        """
        data = {}
        
        try:
            data['files'] = self.list_files()
            self.log_api_call('list_files', {}, 
                            len(data['files'].get('value', [])))
        except Exception as e:
            self.handle_api_error(e, 'list_files')
        
        return data
