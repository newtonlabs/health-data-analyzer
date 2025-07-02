"""Clean OAuth2 clients for health data integration.

This module provides standardized OAuth2 clients for health and cloud storage APIs:
- WhoopClient: Fitness tracking data from Whoop
- WithingsClient: Health measurements from Withings
- OneDriveClient: Cloud storage integration with Microsoft OneDrive

All clients feature:
- 90-day sliding window authentication
- Automatic token refresh
- Persistent token storage
- Unified error handling
- Production-ready architecture
"""

from .whoop_client import WhoopClient
from .withings_client import WithingsClient  
from .onedrive_client import OneDriveClient

__all__ = [
    "WhoopClient",
    "WithingsClient", 
    "OneDriveClient"
]
