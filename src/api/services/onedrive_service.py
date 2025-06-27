"""OneDrive API service for clean separation of concerns."""

from typing import Optional

from src.api.services.base_service import BaseAPIService
from src.api.clients.onedrive_client import OneDriveClient


class OneDriveService(BaseAPIService):
    """Service for OneDrive API communication.
    
    This service provides a clean interface to OneDrive operations while delegating
    all actual API communication to the existing OneDriveClient.
    """

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        token_file: str = None,
    ):
        """Initialize the OneDrive service.

        Args:
            client_id: Optional client ID
            client_secret: Optional client secret  
            token_file: Optional path to token storage file
        """
        self.onedrive_client = OneDriveClient(
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file
        )
        super().__init__(self.onedrive_client)

    def create_folder(self, folder_path: str) -> str:
        """Create a folder in OneDrive.

        Args:
            folder_path: Path of folder to create

        Returns:
            OneDrive item ID of the created folder
        """
        return self.onedrive_client.create_folder(folder_path)

    def upload_file(self, file_path: str, folder_name: Optional[str] = None) -> str:
        """Upload a file to OneDrive.

        Args:
            file_path: Path to file to upload
            folder_name: Optional folder name in OneDrive

        Returns:
            OneDrive URL of uploaded file
        """
        return self.onedrive_client.upload_file(file_path, folder_name)
