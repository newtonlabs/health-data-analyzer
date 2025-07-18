"""Base class for API services.

This module provides the base class for all API service implementations,
defining the common interface and shared functionality.
"""

from abc import ABC
from datetime import datetime, date
from typing import Any, Dict, Optional
import logging


class BaseAPIService(ABC):
    """Base class for all API services.
    
    API services are responsible for making raw API calls and returning
    unprocessed responses. They should not perform any data transformation
    or processing - that is handled by extractors and transformers.
    """
    
    def __init__(self, client):
        """Initialize the API service.
        
        Args:
            client: The authenticated API client instance
        """
        self.client = client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def fetch_data(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Fetch all available data from the API.
        
        This is the main entry point for fetching data from an API service.
        Implementations should call specific fetch methods and return a
        dictionary containing all fetched data.
        
        Args:
            start_date: Start date for data range (if applicable)
            end_date: End date for data range (if applicable)
            
        Returns:
            Dictionary containing raw API responses
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement fetch_data method")
    
    def convert_dates_to_datetime(
        self, start_date: Optional[date], end_date: Optional[date]
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """Convert date objects to datetime objects for API calls.
        
        Many APIs expect datetime objects rather than date objects.
        This utility method handles the conversion consistently.
        
        Args:
            start_date: Start date to convert
            end_date: End date to convert
            
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
        
        if end_date:
            # For end dates, use end of day to be inclusive
            end_datetime = datetime.combine(end_date, datetime.max.time().replace(microsecond=0))
        
        return start_datetime, end_datetime
    
    def log_api_call(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        response_size: Optional[int] = None
    ) -> None:
        """Log API call details for debugging and monitoring.
        
        Args:
            endpoint: API endpoint that was called
            params: Parameters sent with the request
            response_size: Size of the response (number of records, bytes, etc.)
        """
        log_msg = f"API call to {endpoint}"
        if params:
            log_msg += f" with params: {params}"
        if response_size is not None:
            log_msg += f" returned {response_size} items"
        
        self.logger.info(log_msg)
    
    def handle_api_error(self, error: Exception, endpoint: str) -> None:
        """Handle and log API errors consistently.
        
        Args:
            error: The exception that occurred
            endpoint: The API endpoint that failed
            
        Raises:
            The original exception after logging
        """
        self.logger.error(f"API call to {endpoint} failed: {str(error)}")
        raise error
    
    def is_authenticated(self) -> bool:
        """Check if the underlying client is authenticated.
        
        Returns:
            True if client is authenticated, False otherwise
        """
        if hasattr(self.client, 'is_authenticated'):
            return self.client.is_authenticated()
        return True  # Assume authenticated if method not available
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about this service.
        
        Returns:
            Dictionary containing service metadata
        """
        return {
            "service_name": self.__class__.__name__,
            "client_type": self.client.__class__.__name__,
            "is_authenticated": self.is_authenticated(),
            "base_url": getattr(self.client, 'base_url', 'unknown')
        }
