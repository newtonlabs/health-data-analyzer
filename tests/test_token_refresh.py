"""Test token refresh functionality."""
import os
import json
from datetime import datetime, timedelta
from src.data_sources.token_manager import TokenManager
from src.data_sources.whoop_client import WhoopClient

def test_token_refresh():
    """Test token refresh functionality."""
    # Create a test token file with an expired token
    test_token_file = '/tmp/test_whoop_tokens.json'
    
    # Create expired tokens (set timestamp to 2 hours ago)
    expired_tokens = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'token_type': 'bearer',
        'expires_in': 3600,  # 1 hour
        'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()
    }
    
    # Save expired tokens
    os.makedirs(os.path.dirname(test_token_file), exist_ok=True)
    with open(test_token_file, 'w') as f:
        json.dump(expired_tokens, f)
    
    # Create token manager with expired tokens
    token_manager = TokenManager(test_token_file)
    
    # Verify token is considered expired
    assert token_manager.is_token_expired(), "Token should be considered expired"
    
    # Load tokens and verify expiration is detected
    tokens = token_manager.get_tokens()
    print("\nLoaded tokens:", tokens)
    print("Token expired:", token_manager.is_token_expired())
    
    # Clean up test file
    os.remove(test_token_file)
    print("\nTest completed successfully!")

if __name__ == '__main__':
    test_token_refresh()
