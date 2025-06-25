"""Token management for API clients."""

import json
import os
import stat
from datetime import datetime, timedelta
from typing import Any, Optional

from src.utils.logging_utils import HealthLogger


class TokenManager:
    """Singleton per token file path for managing OAuth tokens."""

    # Default token validity period (90 days)
    DEFAULT_TOKEN_VALIDITY_DAYS = 90

    # Default buffer time before expiration to trigger refresh (1 day)
    DEFAULT_REFRESH_BUFFER_HOURS = 24

    def __init__(
        self,
        token_file: str = None,
        validity_days: int = None,
        refresh_buffer_hours: int = None,
    ):
        """Initialize TokenManager.

        Args:
            token_file: Path to token storage file
            validity_days: Number of days tokens are considered valid (default: 90)
            refresh_buffer_hours: Hours before expiration to trigger refresh (default: 24)
        """
        if token_file is None:
            raise ValueError("token_file is required for TokenManager")
            
        # Initialize logger first so we can use it in other methods
        self.logger = HealthLogger(__name__)

        # Create a dedicated token directory with proper permissions
        self.token_file = self._ensure_token_file_path(token_file)
        self.tokens: dict[str, Any] = {}
        self.token_expiry: Optional[datetime] = None
        self.token_created: Optional[datetime] = None

        # Get validity period from environment or use default
        self.validity_days = validity_days or int(
            os.getenv("TOKEN_VALIDITY_DAYS", self.DEFAULT_TOKEN_VALIDITY_DAYS)
        )
        self.refresh_buffer_hours = refresh_buffer_hours or int(
            os.getenv("TOKEN_REFRESH_BUFFER_HOURS", self.DEFAULT_REFRESH_BUFFER_HOURS)
        )

        self._load_tokens()
        
    def _ensure_token_file_path(self, token_file: str) -> str:
        """Ensure the token file path exists with proper permissions.
        
        Args:
            token_file: Path to token storage file
            
        Returns:
            Absolute path to the token file
        """
        # Expand user directory if needed
        original_path = token_file
        token_file = os.path.expanduser(token_file)
        self.logger.debug(f"[TokenManager] Original token path: {original_path}, expanded to: {token_file}")
        
        # Always use the dedicated token directory in user's home
        token_basename = os.path.basename(token_file)
        new_token_dir = os.path.join(os.path.expanduser("~"), ".health_analyzer_tokens")
        new_token_file = os.path.join(new_token_dir, token_basename)
        
        self.logger.debug(f"[TokenManager] Using dedicated token directory: {new_token_dir}")
        self.logger.debug(f"[TokenManager] New token file path: {new_token_file}")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(new_token_dir):
            try:
                self.logger.debug(f"[TokenManager] Creating directory: {new_token_dir}")
                os.makedirs(new_token_dir, exist_ok=True)
                # Set permissions to user read/write only (0o700)
                os.chmod(new_token_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                self.logger.debug(f"[TokenManager] Created token directory with secure permissions: {new_token_dir}")
            except Exception as e:
                self.logger.warning(f"[TokenManager] Failed to create token directory with secure permissions: {e}")
        else:
            self.logger.debug(f"[TokenManager] Directory already exists: {new_token_dir}")
        
        # Check if there's an existing token file in the old location
        if os.path.exists(token_file) and token_file != new_token_file:
            try:
                # Read the existing token file
                with open(token_file, "r") as f:
                    token_data = json.load(f)
                
                # Write to the new location
                with open(new_token_file, "w") as f:
                    json.dump(token_data, f)
                
                self.logger.debug(f"[TokenManager] Migrated token file from {token_file} to {new_token_file}")
                
                # Remove the old token file
                os.remove(token_file)
                self.logger.debug(f"[TokenManager] Removed old token file: {token_file}")
            except Exception as e:
                self.logger.warning(f"[TokenManager] Failed to migrate token file: {e}")
                
        return new_token_file

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

                self.logger.debug(
                    f"[TokenManager] Loaded tokens with expiry: {self.token_expiry}"
                )
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
        # Add timestamp if not present
        current_time = datetime.now()
        tokens["timestamp"] = current_time.timestamp()

        # Add validity period for reference
        tokens["validity_days"] = self.validity_days

        # Implement sliding window for refresh tokens
        # If this is a token refresh (not initial auth), update the last_refresh_time
        if self.tokens and "access_token" in self.tokens:
            # This is a refresh, not initial auth
            tokens["last_refresh_time"] = current_time.isoformat()
            
            # Keep the original creation timestamp
            if "created_at" in self.tokens:
                tokens["created_at"] = self.tokens.get("created_at")
            else:
                # Fallback if somehow we don't have a created_at
                tokens["created_at"] = current_time.isoformat()
        else:
            # This is initial authentication
            tokens["created_at"] = current_time.isoformat()
            tokens["last_refresh_time"] = current_time.isoformat()

        # Update instance variables
        self.tokens = tokens

        # Calculate expiry time
        expires_in = tokens.get("expires_in", 0)
        if expires_in > 0:
            # Convert to timedelta and add to current time
            self.token_expiry = current_time + timedelta(seconds=expires_in)
            self.token_created = current_time

        # Save to file
        try:
            # Ensure the directory exists
            token_dir = os.path.dirname(self.token_file)
            if token_dir and not os.path.exists(token_dir):
                os.makedirs(token_dir, exist_ok=True)

            with open(self.token_file, "w") as f:
                json.dump(tokens, f)

            self.logger.debug(f"[TokenManager] Saved tokens to {self.token_file}")
        except Exception as e:
            self.logger.error(f"[TokenManager] Failed to save tokens: {e}")

    def get_tokens(self) -> Optional[dict[str, Any]]:
        """Get current tokens if they exist and are valid.

        Returns:
            Token data if valid, None if expired or not present
        """
        if not self.tokens:
            return None

        # Use consistent expiration check with is_token_expired()
        if self.is_token_expired():
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
            
        current_time = datetime.now()
        
        # Check if refresh token is past our sliding window validity period
        # Only check if the last refresh was more than 90 days ago
        if "last_refresh_time" in self.tokens:
            try:
                last_refresh = datetime.fromisoformat(self.tokens["last_refresh_time"])
                days_since_refresh = (current_time - last_refresh).days
                
                if days_since_refresh > self.validity_days:
                    self.logger.debug(
                        f"[TokenManager] Refresh token expired: {days_since_refresh} days since last refresh (limit: {self.validity_days} days)"
                    )
                    return True
            except (ValueError, TypeError) as e:
                self.logger.warning(f"[TokenManager] Error parsing last_refresh_time: {e}")
        
        # For access tokens, use a 1-hour buffer before expiry
        # This helps prevent unnecessary token refreshes
        buffer = timedelta(hours=1)
        is_expiring_soon = current_time + buffer >= self.token_expiry

        if is_expiring_soon:
            self.logger.debug(f"[TokenManager] Access token will expire within 1 hour")

        return is_expiring_soon

    def clear_tokens(self) -> None:
        """Clear all stored tokens and delete the token file."""
        self.tokens = {}
        self.token_expiry = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            self.logger.debug(f"[TokenManager] Deleted token file {self.token_file}")
