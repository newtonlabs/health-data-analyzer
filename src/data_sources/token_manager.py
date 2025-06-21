"""Token management for API clients."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.utils.logging_utils import HealthLogger


class TokenManager:
    """Singleton per token file path for managing OAuth tokens."""

    def __init__(self, token_file: str = None):
        if token_file is None:
            raise ValueError("token_file is required for TokenManager")
        self.token_file = token_file
        self.tokens: Dict[str, Any] = {}
        self.token_expiry: Optional[datetime] = None
        self.logger = HealthLogger(__name__)
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from file and set expiry."""
        self.logger.debug(
            f"[TokenManager] Attempting to read tokens from {self.token_file}"
        )
        try:
            with open(self.token_file, "r") as f:
                self.tokens = json.load(f)
                self.logger.debug(
                    f"[TokenManager] Read tokens from {self.token_file}: {self.tokens}"
                )
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
        except FileNotFoundError:
            self.logger.debug(
                f"[TokenManager] Token file {self.token_file} does not exist"
            )
            self.tokens = {}
            self.token_expiry = None
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(
                f"[TokenManager] Failed to read tokens from {self.token_file}: {str(e)}"
            )
            self.tokens = {}
            self.token_expiry = None

    def save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Save tokens to file with timestamp.

        Args:
            tokens: Token data to save. Must include 'expires_in' and 'access_token' for proper management.
        """
        # Add timestamp for expiry tracking
        tokens["timestamp"] = datetime.now().isoformat()

        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=4)  # Use indent for readability

        self.tokens = tokens
        if "expires_in" in tokens:
            self.token_expiry = datetime.fromisoformat(tokens["timestamp"]) + timedelta(
                seconds=tokens["expires_in"]
            )
        else:
            self.token_expiry = None  # Clear expiry if not provided

    def get_tokens(self) -> Optional[Dict[str, Any]]:
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
            True if token is expired or will expire in the next 5 minutes
        """
        if not self.token_expiry:
            return True  # No expiry info, assume expired or never set

        # Consider token expired if it will expire in the next 5 minutes
        return datetime.now() + timedelta(minutes=5) >= self.token_expiry

    def clear_tokens(self) -> None:
        """Clear all stored tokens and delete the token file."""
        self.tokens = {}
        self.token_expiry = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            self.logger.debug(f"[TokenManager] Deleted token file {self.token_file}")
