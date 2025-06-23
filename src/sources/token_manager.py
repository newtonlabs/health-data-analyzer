"""Token management for API clients."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from src.utils.logging_utils import HealthLogger


class TokenManager:
    """Singleton per token file path for managing OAuth tokens."""

    # Default token validity period (30 days)
    DEFAULT_TOKEN_VALIDITY_DAYS = 30
    
    # Default buffer time before expiration to trigger refresh (1 day)
    DEFAULT_REFRESH_BUFFER_HOURS = 24
    
    def __init__(self, token_file: str = None, validity_days: int = None, refresh_buffer_hours: int = None):
        """Initialize TokenManager.
        
        Args:
            token_file: Path to token storage file
            validity_days: Number of days tokens are considered valid (default: 30)
            refresh_buffer_hours: Hours before expiration to trigger refresh (default: 24)
        """
        if token_file is None:
            raise ValueError("token_file is required for TokenManager")
            
        self.token_file = token_file
        self.tokens: dict[str, Any] = {}
        self.token_expiry: Optional[datetime] = None
        self.token_created: Optional[datetime] = None
        
        # Get validity period from environment or use default
        self.validity_days = validity_days or int(os.getenv("TOKEN_VALIDITY_DAYS", self.DEFAULT_TOKEN_VALIDITY_DAYS))
        self.refresh_buffer_hours = refresh_buffer_hours or int(os.getenv("TOKEN_REFRESH_BUFFER_HOURS", self.DEFAULT_REFRESH_BUFFER_HOURS))
        
        self.logger = HealthLogger(__name__)
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from file and set expiry."""
        self.logger.debug(
            f"[TokenManager] Attempting to read tokens from {self.token_file}"
        )
        try:
            with open(self.token_file) as f:
                self.tokens = json.load(f)
                
                # Load custom validity period if present
                if "validity_days" in self.tokens:
                    self.validity_days = self.tokens["validity_days"]
                    
                # Load creation timestamp
                if "created_at" in self.tokens:
                    created_at_str = self.tokens["created_at"]
                    self.token_created = datetime.fromisoformat(created_at_str)
                elif "timestamp" in self.tokens:
                    # Fallback to timestamp for older token files
                    timestamp_str = self.tokens["timestamp"]
                    if isinstance(timestamp_str, str):
                        self.token_created = datetime.fromisoformat(timestamp_str)
                    else:  # Assume it's a Unix timestamp if not string
                        self.token_created = datetime.fromtimestamp(timestamp_str)
                        
                # Calculate token expiry if we have expires_in and timestamp
                if "expires_in" in self.tokens and "timestamp" in self.tokens:
                    expires_in = self.tokens["expires_in"]
                    # Handle both ISO format and direct timestamp if present
                    timestamp_str = self.tokens["timestamp"]
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str)
                    else:  # Assume it's a Unix timestamp if not string
                        timestamp = datetime.fromtimestamp(timestamp_str)
                    self.token_expiry = timestamp + timedelta(seconds=expires_in)
                    
                self.logger.debug(f"[TokenManager] Loaded tokens with expiry: {self.token_expiry}")
        except FileNotFoundError:
            self.logger.debug(
                f"[TokenManager] Token file {self.token_file} does not exist"
            )
            self.tokens = {}
            self.token_expiry = None
            self.token_created = None
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(
                f"[TokenManager] Failed to read tokens from {self.token_file}: {str(e)}"
            )
            self.tokens = {}
            self.token_expiry = None
            self.token_created = None

    def save_tokens(self, tokens: dict[str, Any]) -> None:
        """Save tokens to file with timestamp.

        Args:
            tokens: Token data to save. Must include 'expires_in' and 'access_token' for proper management.
        """
        # Add timestamp for expiry tracking
        now = datetime.now()
        tokens["timestamp"] = now.isoformat()
        
        # Add custom validity period (30 days by default)
        tokens["validity_days"] = self.validity_days
        tokens["created_at"] = now.isoformat()

        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=4)  # Use indent for readability

        self.tokens = tokens
        self.token_created = now
        
        # Calculate token expiry based on API's expires_in
        if "expires_in" in tokens:
            self.token_expiry = now + timedelta(seconds=tokens["expires_in"])
        else:
            # If no expires_in, use our validity period
            self.token_expiry = now + timedelta(days=self.validity_days)

    def get_tokens(self) -> Optional[dict[str, Any]]:
        """Get current tokens if they exist and are valid.

        Returns:
            Token data if valid, None if expired or not present
        """
        if not self.tokens:
            return None

        # Check if tokens are expired (consider a small buffer for network latency)
        if (
            self.token_expiry
            and datetime.now() + timedelta(minutes=1) >= self.token_expiry
        ):
            self.logger.debug(f"[TokenManager] Tokens expired for {self.token_file}")
            return None

        return self.tokens

    def get_access_token(self) -> Optional[str]:
        """Get the access token if it exists and is not expired."""
        tokens = self.get_tokens()
        return tokens.get("access_token") if tokens else None

    def get_refresh_token(self) -> Optional[str]:
        """Get the refresh token if it exists and is not expired."""
        tokens = self.get_tokens()
        return tokens.get("refresh_token") if tokens else None

    def is_token_expired(self) -> bool:
        """Check if the current token is expired.

        Returns:
            True if token is expired or will expire soon based on refresh buffer
        """
        if not self.token_expiry:
            return True  # No expiry info, assume expired or never set
            
        # Check if token is past our custom validity period
        if self.token_created and datetime.now() > self.token_created + timedelta(days=self.validity_days):
            self.logger.debug(f"[TokenManager] Token exceeded validity period of {self.validity_days} days")
            return True

        # Consider token expired if it will expire within the buffer period
        buffer = timedelta(hours=self.refresh_buffer_hours)
        is_expiring_soon = datetime.now() + buffer >= self.token_expiry
        
        if is_expiring_soon:
            self.logger.debug(f"[TokenManager] Token will expire within {self.refresh_buffer_hours} hours")
            
        return is_expiring_soon

    def clear_tokens(self) -> None:
        """Clear all stored tokens and delete the token file."""
        self.tokens = {}
        self.token_expiry = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            self.logger.debug(f"[TokenManager] Deleted token file {self.token_file}")
