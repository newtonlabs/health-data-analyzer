"""Centralized configuration for all health data clients."""

import os
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ClientConfig:
    """Base configuration for all clients."""
    validity_days: int = 90
    refresh_buffer_hours: int = 24
    max_retries: int = 3
    timeout: int = 30
    retry_delays: List[int] = None
    
    def __post_init__(self):
        if self.retry_delays is None:
            self.retry_delays = [1, 2, 4, 8]
    
    @classmethod
    def from_env(cls) -> 'ClientConfig':
        """Create configuration from environment variables."""
        return cls(
            validity_days=int(os.getenv("TOKEN_VALIDITY_DAYS", 90)),
            refresh_buffer_hours=int(os.getenv("TOKEN_REFRESH_BUFFER_HOURS", 24)),
            max_retries=int(os.getenv("API_MAX_RETRIES", 3)),
            timeout=int(os.getenv("API_TIMEOUT", 30))
        )


# Global configuration instance
CLIENT_CONFIG = ClientConfig.from_env()


class ServiceConfig:
    """Service-specific configurations."""
    
    @staticmethod
    def WHOOP():
        return {
            "base_url": "https://api.prod.whoop.com/developer",
            "auth_url": "https://api.prod.whoop.com/oauth/oauth2/auth", 
            "token_url": "https://api.prod.whoop.com/oauth/oauth2/token",
            "scopes": ["read:recovery", "read:cycles", "read:sleep", "read:workout", "read:profile", "offline"],
            "default_page_size": 50
        }
    
    @staticmethod
    def WITHINGS():
        return {
            "base_url": "https://wbsapi.withings.net",
            "auth_url": "https://account.withings.com/oauth2_user/authorize2",
            "token_url": "https://wbsapi.withings.net/v2/oauth2", 
            "scopes": ["user.metrics", "user.activity", "user.sleepevents"],
            "default_page_size": 100
        }
    
    @staticmethod
    def ONEDRIVE():
        return {
            "base_url": "https://graph.microsoft.com/v1.0",
            "authority": "https://login.microsoftonline.com/consumers",
            "scopes": ["https://graph.microsoft.com/Files.ReadWrite"],
        }
    
    @staticmethod
    def HEVY():
        return {
            "base_url": "https://api.hevyapp.com", 
            "default_page_size": 50
        }
    
    @staticmethod
    def OURA():
        return {
            "base_url": "https://api.ouraring.com/v2",
            "default_page_size": 100
        }


class ClientFactory:
    """Factory for creating configured client instances."""
    
    @staticmethod
    def get_service_config(service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service.
        
        Args:
            service_name: Name of the service (whoop, withings, oura, hevy, onedrive)
            
        Returns:
            Dictionary containing service-specific configuration
            
        Raises:
            ValueError: If service_name is not supported
        """
        service_configs = {
            'whoop': ServiceConfig.WHOOP(),
            'withings': ServiceConfig.WITHINGS(), 
            'oura': ServiceConfig.OURA(),
            'hevy': ServiceConfig.HEVY(),
            'onedrive': ServiceConfig.ONEDRIVE()
        }
        
        if service_name.lower() not in service_configs:
            raise ValueError(f"Unsupported service: {service_name}. Supported services: {list(service_configs.keys())}")
            
        return service_configs[service_name.lower()]
    
    @staticmethod
    def get_client_config() -> ClientConfig:
        """Get the global client configuration.
        
        Returns:
            ClientConfig instance with environment-based settings
        """
        return CLIENT_CONFIG