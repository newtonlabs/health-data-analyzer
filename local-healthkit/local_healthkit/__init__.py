"""Local HealthKit - Production-ready clients and services for health data APIs.

This package provides standardized clients and services for health and cloud storage APIs:
- WhoopClient/WhoopService: Fitness tracking data from Whoop (OAuth2)
- OuraClient/OuraService: Ring-based health tracking from Oura (API key)
- WithingsClient/WithingsService: Health measurements from Withings (OAuth2)
- HevyClient/HevyService: Workout tracking data from Hevy (API key)
- OneDriveClient/OneDriveService: Cloud storage integration with Microsoft OneDrive (OAuth2)

Features:
- OAuth2 clients with 90-day sliding window authentication
- Automatic token refresh and persistent token storage
- API key clients with retry logic and exponential backoff
- Unified error handling and consistent interfaces
- Production-ready architecture with comprehensive logging
"""

from .clients import (
    OuraClient,
    HevyClient,
    WhoopClient,
    WithingsClient,
    OneDriveClient,
)

from .services import (
    OuraService,
    HevyService,
    WhoopService,
    WithingsService,
    OneDriveService,
)

from .exceptions import (
    LocalHealthKitError,
    APIClientError,
    AuthenticationError,
    RateLimitError,
)

__version__ = "2.0.0"
__author__ = "Thomas Newton"
__email__ = "thomas.newton@example.com"

__all__ = [
    # Clients
    "OuraClient", 
    "HevyClient",
    "WhoopClient",
    "WithingsClient",
    "OneDriveClient",
    # Services
    "OuraService",
    "HevyService",
    "WhoopService",
    "WithingsService",
    "OneDriveService",
    # Exceptions
    "LocalHealthKitError",
    "APIClientError",
    "AuthenticationError",
    "RateLimitError",
    # Metadata
    "__version__",
]
