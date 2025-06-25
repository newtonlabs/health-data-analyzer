#!/usr/bin/env python3
"""
Token cleanup and repair utility.

This script fixes common token issues:
1. Corrupted OneDrive JWT tokens
2. Inconsistent token states
3. Token validation
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.token_manager import TokenManager


def fix_onedrive_tokens():
    """Fix corrupted OneDrive tokens."""
    print("🔧 Fixing OneDrive tokens...")
    
    try:
        token_manager = TokenManager("~/.onedrive_tokens.json")
        tokens = token_manager.get_tokens()
        
        if tokens:
            print("⚠️  Found existing OneDrive tokens, checking validity...")
            
            # Check if tokens look corrupted
            access_token = tokens.get("access_token", "")
            if access_token and "." not in access_token:
                print("❌ OneDrive JWT token is malformed (no dots found)")
                print("🗑️  Clearing corrupted tokens...")
                token_manager.clear_tokens()
                print("✅ Corrupted OneDrive tokens cleared")
                return True
            else:
                print("✅ OneDrive tokens appear to be properly formatted")
                return False
        else:
            print("ℹ️  No OneDrive tokens found")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing OneDrive tokens: {e}")
        return False


def validate_all_tokens():
    """Validate all stored tokens."""
    print("\n🔍 Validating all stored tokens...")
    
    # Check centralized token directory
    centralized_dir = Path.home() / ".health_analyzer_tokens"
    if not centralized_dir.exists():
        print("⚠️  No centralized token directory found")
        return
    
    token_files = list(centralized_dir.glob("*.json"))
    print(f"📄 Found {len(token_files)} token files to validate")
    
    for token_file in token_files:
        service_name = token_file.stem.replace(".", "").replace("_tokens", "")
        print(f"\n🔍 Validating {service_name} tokens...")
        
        try:
            token_manager = TokenManager(str(token_file))
            tokens = token_manager.get_tokens()
            
            if tokens:
                # Check token structure
                required_fields = ["access_token"]
                missing_fields = [field for field in required_fields if field not in tokens]
                
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                else:
                    print("✅ Token structure is valid")
                
                # Check expiration status
                is_expired = token_manager.is_token_expired()
                status = "EXPIRED" if is_expired else "VALID"
                print(f"📅 Token status: {status}")
                
                # Check token format for JWT tokens
                access_token = tokens.get("access_token", "")
                if access_token:
                    if "." in access_token and len(access_token.split(".")) == 3:
                        print("✅ JWT token format is valid")
                    elif len(access_token) > 50:  # Likely a valid token but not JWT
                        print("✅ Token format appears valid (non-JWT)")
                    else:
                        print("⚠️  Token format may be invalid")
                
            else:
                print("❌ No valid tokens found")
                
        except Exception as e:
            print(f"❌ Error validating {service_name} tokens: {e}")


def test_token_refresh():
    """Test token refresh functionality."""
    print("\n🔄 Testing token refresh functionality...")
    
    try:
        from src.sources.whoop import WhoopClient
        
        print("🏃 Testing Whoop token refresh...")
        client = WhoopClient()
        
        if client.is_authenticated():
            print("✅ Whoop client is authenticated")
            
            # Check if token needs refresh
            if client.token_manager.is_token_expired():
                print("⚠️  Whoop token is expired, attempting refresh...")
                success = client.refresh_access_token()
                if success:
                    print("✅ Whoop token refresh successful")
                else:
                    print("❌ Whoop token refresh failed")
            else:
                print("ℹ️  Whoop token is still valid, no refresh needed")
        else:
            print("⚠️  Whoop client is not authenticated")
            
    except Exception as e:
        print(f"❌ Error testing token refresh: {e}")


def main():
    """Run all token fixes and validations."""
    print("🔧 Token Cleanup and Repair Utility")
    print("=" * 50)
    
    # Fix specific issues
    onedrive_fixed = fix_onedrive_tokens()
    
    # Validate all tokens
    validate_all_tokens()
    
    # Test refresh functionality
    test_token_refresh()
    
    print("\n" + "=" * 50)
    if onedrive_fixed:
        print("🎉 Token issues fixed!")
        print("✅ OneDrive tokens cleared and ready for re-authentication")
    else:
        print("✅ Token validation complete!")
    
    print("📝 Next steps:")
    print("   1. Run the main application to test automatic token refresh")
    print("   2. OneDrive will require re-authentication on next use")
    print("   3. All other services should work without re-authentication")


if __name__ == "__main__":
    main()
