"""Exception classes for Local HealthKit package."""


class LocalHealthKitError(Exception):
    """Base exception for all Local HealthKit errors."""
    pass


class APIClientError(LocalHealthKitError):
    """Exception raised for API client errors.
    
    This includes HTTP errors, authentication failures, rate limiting,
    and other API-related issues.
    """
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(APIClientError):
    """Exception raised for authentication-related errors.
    
    This includes invalid credentials, expired tokens, and OAuth2 flow failures.
    """
    pass


class RateLimitError(APIClientError):
    """Exception raised when API rate limits are exceeded.
    
    This exception includes information about when the rate limit resets.
    """
    
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ConfigurationError(LocalHealthKitError):
    """Exception raised for configuration-related errors.
    
    This includes missing environment variables, invalid configuration values,
    and other setup issues.
    """
    pass


class DataProcessingError(LocalHealthKitError):
    """Exception raised for data processing errors.
    
    This includes data validation failures, transformation errors,
    and other data-related issues.
    """
    pass
