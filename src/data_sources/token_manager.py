"""Token management for API clients."""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class TokenManager:
    _instance = None
    _initialized = False
    
    def __new__(cls, token_file: str = None):
        if cls._instance is None:
            cls._instance = super(TokenManager, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, token_file: str = None):
        """Initialize token manager.
        
        Args:
            token_file: Path to token storage file. Only used on first initialization.
        """
        # Skip if already initialized
        if TokenManager._initialized:
            return
            
        if token_file is None:
            raise ValueError("token_file is required for first initialization")
            
        TokenManager._initialized = True
        self.token_file = token_file
        self.tokens: Dict[str, Any] = {}
        self.token_expiry: Optional[datetime] = None
        self._load_tokens()
        
    def _load_tokens(self) -> None:
        """Load tokens from file and set expiry."""
        try:
            with open(self.token_file, 'r') as f:
                self.tokens = json.load(f)
                # Calculate token expiry if we have expires_in
                if 'expires_in' in self.tokens and 'timestamp' in self.tokens:
                    expires_in = self.tokens['expires_in']
                    timestamp = datetime.fromisoformat(self.tokens['timestamp'])
                    self.token_expiry = timestamp + timedelta(seconds=expires_in)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tokens = {}
            self.token_expiry = None
            
    def save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Save tokens to file with timestamp.
        
        Args:
            tokens: Token data to save
        """
        # Add timestamp for expiry tracking
        tokens['timestamp'] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f)
        
        self.tokens = tokens
        if 'expires_in' in tokens:
            self.token_expiry = datetime.fromisoformat(tokens['timestamp']) + timedelta(seconds=tokens['expires_in'])
            
    def get_tokens(self) -> Optional[Dict[str, Any]]:
        """Get current tokens if they exist and are valid.
        
        Returns:
            Token data if valid, None if expired or not present
        """
        if not self.tokens:
            return None
            
        # Check if tokens are expired
        if self.token_expiry and datetime.now() >= self.token_expiry:
            return None
            
        return self.tokens
        
    def is_token_expired(self) -> bool:
        """Check if the current token is expired.
        
        Returns:
            True if token is expired or will expire in the next 5 minutes
        """
        if not self.token_expiry:
            return True
            
        # Consider token expired if it will expire in the next 5 minutes
        return datetime.now() + timedelta(minutes=5) >= self.token_expiry
        
    def clear_tokens(self) -> None:
        """Clear all stored tokens."""
        self.tokens = {}
        self.token_expiry = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
