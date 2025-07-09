"""Health data API clients with OAuth2 and API key authentication.

This module provides production-ready clients for health and cloud storage APIs:
- OuraClient: Ring-based health tracking from Oura (API key)
- HevyClient: Workout tracking data from Hevy (API key)
- WhoopClient: Fitness tracking data from Whoop (OAuth2)
- WithingsClient: Health measurements from Withings (OAuth2)
- OneDriveClient: Cloud storage integration with Microsoft OneDrive (MSAL)

Features:
- Consistent interfaces across all clients
- Automatic retry logic with exponential backoff
- Comprehensive error handling
- Environment-based configuration
- Production-ready authentication flows
"""

from .oura import OuraClient
from .hevy import HevyClient
from .whoop import WhoopClient
from .withings import WithingsClient
from .onedrive import OneDriveClient

__all__ = [
    "OuraClient",
    "HevyClient",
    "WhoopClient",
    "WithingsClient",
    "OneDriveClient",
]
