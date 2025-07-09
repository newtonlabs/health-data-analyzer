"""Health data API services providing high-level business logic.

This module provides service layer abstractions over the health data clients:
- OuraService: Ring-based health tracking service
- HevyService: Workout tracking service
- WhoopService: Fitness tracking service
- WithingsService: Health measurements service
- OneDriveService: Cloud storage service

Services provide:
- Unified data fetching interfaces
- Business logic and data aggregation
- Comprehensive logging and error handling
- Date range processing
- Multi-data type support
"""

from .base import BaseAPIService
from .oura import OuraService
from .hevy import HevyService
from .whoop import WhoopService
from .withings import WithingsService
from .onedrive import OneDriveService

__all__ = [
    "BaseAPIService",
    "OuraService",
    "HevyService",
    "WhoopService",
    "WithingsService",
    "OneDriveService",
]
