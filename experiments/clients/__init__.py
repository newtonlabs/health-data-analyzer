"""Clean OAuth2 and API key clients for health data integration.

This module provides standardized clients for health and cloud storage APIs:
- WhoopClient: Fitness tracking data from Whoop (OAuth2)
- WithingsClient: Health measurements from Withings (OAuth2)
- OneDriveClient: Cloud storage integration with Microsoft OneDrive (OAuth2)
- HevyClient: Workout tracking data from Hevy (API key)
- OuraClient: Ring-based health tracking from Oura (API key)

OAuth2 clients feature:
- 90-day sliding window authentication
- Automatic token refresh
- Persistent token storage
- Unified error handling
- Production-ready architecture

API key clients feature:
- Simple API key authentication
- Retry logic with exponential backoff
- Consistent interface with OAuth2 clients
"""

from .whoop_client import WhoopClient
from .withings_client import WithingsClient  
from .onedrive_client import OneDriveClient
from .hevy_client import HevyClient
from .oura_client import OuraClient
from .api_key_client import APIKeyClient

__all__ = [
    "WhoopClient",
    "WithingsClient", 
    "OneDriveClient",
    "HevyClient",
    "OuraClient",
    "APIKeyClient"
]
