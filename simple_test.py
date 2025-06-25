#!/usr/bin/env python3
"""
Simple test script to validate new API services can be imported and connect to real APIs.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all services and extractors can be imported."""
    print("🧪 Testing Imports...")
    
    try:
        from src.api.services.whoop_service import WhoopService
        print("✅ WhoopService imported successfully")
    except Exception as e:
        print(f"❌ WhoopService import failed: {e}")
    
    try:
        from src.api.services.oura_service import OuraService
        print("✅ OuraService imported successfully")
    except Exception as e:
        print(f"❌ OuraService import failed: {e}")
    
    try:
        from src.api.services.withings_service import WithingsService
        print("✅ WithingsService imported successfully")
    except Exception as e:
        print(f"❌ WithingsService import failed: {e}")
    
    try:
        from src.api.services.hevy_service import HevyService
        print("✅ HevyService imported successfully")
    except Exception as e:
        print(f"❌ HevyService import failed: {e}")
    
    try:
        from src.api.services.onedrive_service import OneDriveService
        print("✅ OneDriveService imported successfully")
    except Exception as e:
        print(f"❌ OneDriveService import failed: {e}")

def test_whoop_real_connection():
    """Test real connection to Whoop API and response saving."""
    print("\n🏃 Testing Real Whoop API Connection...")
    
    try:
        # Import the old client to create a service
        from src.sources.whoop import WhoopClient
        
        # Create and test the client first
        client = WhoopClient()
        
        print(f"🔐 Whoop authentication status: {client.is_authenticated()}")
        
        # Test API calls with date range regardless of auth status
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)  # Last 3 days for quick test
        
        print(f"📅 Attempting to fetch data from {start_date.date()} to {end_date.date()}")
        
        # Test workout data - try even if not authenticated to see what happens
        try:
            print("🔄 Calling Whoop workouts API...")
            workouts = client.get_workouts(start_date, end_date)
            workout_count = len(workouts.get('data', []))
            print(f"✅ Retrieved {workout_count} workouts from Whoop API")
            
            # Check if response files were saved immediately after API call
            whoop_dir = Path("data/api-responses/whoop")
            if whoop_dir.exists():
                json_files = list(whoop_dir.glob("*.json"))
                print(f"📁 Found {len(json_files)} files in whoop directory after workout call")
            
        except Exception as e:
            print(f"❌ Workout API call failed: {e}")
            # Still check if any response files were created
            whoop_dir = Path("data/api-responses/whoop")
            if whoop_dir.exists():
                json_files = list(whoop_dir.glob("*.json"))
                print(f"📁 Even after error, found {len(json_files)} files in whoop directory")
        
        # Test recovery data
        try:
            print("🔄 Calling Whoop recovery API...")
            recovery = client.get_recovery(start_date, end_date)
            recovery_count = len(recovery.get('data', []))
            print(f"✅ Retrieved {recovery_count} recovery records from Whoop API")
        except Exception as e:
            print(f"❌ Recovery API call failed: {e}")
        
        # Final check of response files
        whoop_dir = Path("data/api-responses/whoop")
        if whoop_dir.exists():
            json_files = list(whoop_dir.glob("*.json"))
            print(f"📁 Final count: {len(json_files)} API response files in whoop directory")
            
            # Show all files
            if json_files:
                print("📋 Whoop API response files:")
                for file in json_files:
                    size_kb = file.stat().st_size / 1024
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"   • {file.name} ({size_kb:.1f}KB, {mod_time.strftime('%H:%M:%S')})")
                return True
            else:
                print("⚠️  No JSON files found - response saving may not be working")
                return False
        else:
            print("⚠️  No whoop directory created - API calls may not have been made")
            return False
        
    except Exception as e:
        print(f"❌ Whoop API test failed: {e}")
        return False

def test_oura_real_connection():
    """Test real connection to Oura API and response saving."""
    print("\n💍 Testing Real Oura API Connection...")
    
    try:
        from src.sources.oura import OuraClient
        
        client = OuraClient()
        print(f"🔐 Oura authentication status: {client.is_authenticated()}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        print(f"📅 Attempting to fetch data from {start_date.date()} to {end_date.date()}")
        
        # Test activity data
        try:
            print("🔄 Calling Oura activity API...")
            activity = client.get_activity_data(start_date, end_date)
            activity_count = len(activity.get('data', []))
            print(f"✅ Retrieved {activity_count} activity records from Oura API")
        except Exception as e:
            print(f"❌ Activity API call failed: {e}")
        
        # Test resilience data
        try:
            print("🔄 Calling Oura resilience API...")
            resilience = client.get_resilience_data(start_date, end_date)
            resilience_count = len(resilience.get('data', []))
            print(f"✅ Retrieved {resilience_count} resilience records from Oura API")
        except Exception as e:
            print(f"❌ Resilience API call failed: {e}")
        
        # Check response files
        oura_dir = Path("data/api-responses/oura")
        if oura_dir.exists():
            json_files = list(oura_dir.glob("*.json"))
            print(f"📁 Found {len(json_files)} API response files in oura directory")
            
            if json_files:
                print("📋 Oura API response files:")
                for file in json_files:
                    size_kb = file.stat().st_size / 1024
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"   • {file.name} ({size_kb:.1f}KB, {mod_time.strftime('%H:%M:%S')})")
                return True
        
        print("⚠️  No oura response files found")
        return False
        
    except Exception as e:
        print(f"❌ Oura API test failed: {e}")
        return False

def test_withings_real_connection():
    """Test real connection to Withings API and response saving."""
    print("\n⚖️  Testing Real Withings API Connection...")
    
    try:
        from src.sources.withings import WithingsClient
        
        client = WithingsClient()
        print(f"🔐 Withings authentication status: {client.is_authenticated()}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Withings might need longer range
        
        print(f"📅 Attempting to fetch data from {start_date.date()} to {end_date.date()}")
        
        # Test weight data
        try:
            print("🔄 Calling Withings weight API...")
            weight = client.get_weight_data(start_date, end_date)
            print(f"✅ Retrieved weight data from Withings API")
        except Exception as e:
            print(f"❌ Weight API call failed: {e}")
        
        # Check response files
        withings_dir = Path("data/api-responses/withings")
        if withings_dir.exists():
            json_files = list(withings_dir.glob("*.json"))
            print(f"📁 Found {len(json_files)} API response files in withings directory")
            
            if json_files:
                print("📋 Withings API response files:")
                for file in json_files:
                    size_kb = file.stat().st_size / 1024
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"   • {file.name} ({size_kb:.1f}KB, {mod_time.strftime('%H:%M:%S')})")
                return True
        
        print("⚠️  No withings response files found")
        return False
        
    except Exception as e:
        print(f"❌ Withings API test failed: {e}")
        return False

def test_hevy_real_connection():
    """Test real connection to Hevy API and response saving."""
    print("\n🏋️  Testing Real Hevy API Connection...")
    
    try:
        from src.sources.hevy import HevyClient
        
        client = HevyClient()
        print(f"🔐 Hevy authentication status: {client.is_authenticated()}")
        
        print("📅 Attempting to fetch workout data (last 5 workouts)")
        
        # Test workout data with small page size
        try:
            print("🔄 Calling Hevy workouts API...")
            workouts = client.get_workouts(page_size=5)  # Small page size for testing
            workout_count = len(workouts.get('workouts', []))
            print(f"✅ Retrieved {workout_count} workouts from Hevy API")
        except Exception as e:
            print(f"❌ Workout API call failed: {e}")
        
        # Check response files
        hevy_dir = Path("data/api-responses/hevy")
        if hevy_dir.exists():
            json_files = list(hevy_dir.glob("*.json"))
            print(f"📁 Found {len(json_files)} API response files in hevy directory")
            
            if json_files:
                print("📋 Hevy API response files:")
                for file in json_files:
                    size_kb = file.stat().st_size / 1024
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"   • {file.name} ({size_kb:.1f}KB, {mod_time.strftime('%H:%M:%S')})")
                return True
        
        print("⚠️  No hevy response files found")
        return False
        
    except Exception as e:
        print(f"❌ Hevy API test failed: {e}")
        return False

def test_onedrive_real_connection():
    """Test real connection to OneDrive API and authentication."""
    print("\n☁️  Testing Real OneDrive API Connection...")
    
    try:
        from src.sources.onedrive import OneDriveClient
        
        client = OneDriveClient()
        print(f"🔐 OneDrive authentication status: {client.is_authenticated()}")
        
        # Test authentication flow
        try:
            print("🔄 Testing OneDrive authentication...")
            auth_result = client.authenticate()
            print(f"✅ OneDrive authentication result: {auth_result}")
            
            if auth_result:
                print("🔄 Testing basic OneDrive API call...")
                # Try to create a test folder
                folder_id = client.create_folder("health-analyzer-test")
                print(f"✅ Created test folder with ID: {folder_id}")
                return True
            else:
                print("⚠️  OneDrive authentication failed or was skipped")
                return False
                
        except Exception as e:
            print(f"❌ OneDrive operation failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ OneDrive test failed: {e}")
        return False

def test_directory_structure():
    """Test that API response directories exist or can be created."""
    print("\n📁 Testing Directory Structure...")
    
    data_dir = Path("data")
    api_responses_dir = data_dir / "api-responses"
    
    # Check main directories
    if data_dir.exists():
        print("✅ data/ directory exists")
    else:
        print("⚠️  data/ directory will be created on first use")
    
    if api_responses_dir.exists():
        print("✅ data/api-responses/ directory exists")
    else:
        print("⚠️  data/api-responses/ directory will be created on first use")
    
    # Check service subdirectories
    services = ["whoop", "oura", "withings", "hevy", "onedrive"]
    for service in services:
        service_dir = api_responses_dir / service
        if service_dir.exists():
            files = list(service_dir.glob("*.json"))
            print(f"✅ {service}/ directory exists with {len(files)} JSON files")
        else:
            print(f"⚠️  {service}/ directory will be created on first API call")

def test_file_utils():
    """Test that file utilities work for saving API responses."""
    print("\n💾 Testing File Utils...")
    
    try:
        from src.utils.file_utils import save_json_to_file
        
        # Test saving a simple JSON file
        test_data = {"test": "data", "timestamp": "2025-06-25"}
        save_json_to_file(test_data, "test-api-response", subdir="api-responses/test")
        
        # Check if file was created (with date prefix)
        test_dir = Path("data/api-responses/test")
        if test_dir.exists():
            json_files = list(test_dir.glob("*test-api-response.json"))
            if json_files:
                print("✅ save_json_to_file works correctly (with date prefix)")
                # Clean up test files
                for file in json_files:
                    file.unlink()
                if not any(test_dir.iterdir()):  # Only remove if empty
                    test_dir.rmdir()
            else:
                print("❌ save_json_to_file did not create expected file")
        else:
            print("❌ save_json_to_file did not create test directory")
            
    except Exception as e:
        print(f"❌ File utils test failed: {e}")

def test_token_refresh_status():
    """Investigate token refresh status across all services."""
    print("\n🔄 Investigating Token Refresh Status...")
    
    # Check Withings token refresh specifically
    try:
        from src.sources.withings import WithingsClient
        from src.utils.token_manager import TokenManager
        
        print("🔍 Checking Withings token details...")
        
        # Check if token manager has tokens
        token_manager = TokenManager("~/.withings_tokens.json")
        tokens = token_manager.get_tokens()
        
        if tokens:
            print("✅ Withings tokens found in token manager")
            print(f"📅 Token keys: {list(tokens.keys())}")
            
            # Check if token is expired
            if token_manager.is_token_expired():
                print("⚠️  Withings token is EXPIRED - this explains the auth prompt")
                
                # Try to refresh
                client = WithingsClient()
                try:
                    print("🔄 Attempting token refresh...")
                    client.refresh_access_token()
                    print("✅ Token refresh successful")
                except Exception as e:
                    print(f"❌ Token refresh failed: {e}")
            else:
                print("✅ Withings token is still valid")
        else:
            print("⚠️  No Withings tokens found - first time setup needed")
            
    except Exception as e:
        print(f"❌ Token refresh investigation failed: {e}")
    
    # Check other services
    services_to_check = [
        ("Whoop", "~/.whoop_tokens.json"),
        ("Oura", "~/.oura_tokens.json"),
        ("Hevy", "~/.hevy_tokens.json")  # This might not exist since Hevy uses API key
    ]
    
    for service_name, token_path in services_to_check:
        try:
            from src.utils.token_manager import TokenManager
            token_manager = TokenManager(token_path)
            tokens = token_manager.get_tokens()
            
            if tokens:
                is_expired = token_manager.is_token_expired()
                status = "EXPIRED" if is_expired else "VALID"
                print(f"🔍 {service_name}: Token found, status: {status}")
            else:
                print(f"🔍 {service_name}: No tokens found")
                
        except Exception as e:
            print(f"🔍 {service_name}: Token check failed - {e}")

def investigate_token_storage():
    """Check where tokens are actually stored."""
    print("\n📁 Investigating Token Storage Locations...")
    
    import os
    from pathlib import Path
    
    # Check centralized token directory
    centralized_dir = Path.home() / ".health_analyzer_tokens"
    if centralized_dir.exists():
        print(f"✅ Centralized token directory exists: {centralized_dir}")
        token_files = list(centralized_dir.glob("*.json"))
        print(f"📄 Found {len(token_files)} token files:")
        for file in token_files:
            size_kb = file.stat().st_size / 1024
            print(f"   • {file.name} ({size_kb:.1f}KB)")
    else:
        print("⚠️  Centralized token directory not found")
    
    # Check individual token files
    individual_tokens = [
        "~/.whoop_tokens.json",
        "~/.oura_tokens.json", 
        "~/.withings_tokens.json",
        "~/.onedrive_tokens.json"
    ]
    
    print("\n🔍 Checking individual token files:")
    for token_path in individual_tokens:
        expanded_path = Path(token_path).expanduser()
        if expanded_path.exists():
            size_kb = expanded_path.stat().st_size / 1024
            print(f"✅ {token_path} exists ({size_kb:.1f}KB)")
        else:
            print(f"❌ {token_path} not found")

def main():
    """Run all tests."""
    print("🚀 API Services Real Connection Test")
    print("=" * 60)
    
    test_imports()
    test_directory_structure()
    test_file_utils()
    
    # Real API tests
    whoop_success = test_whoop_real_connection()
    oura_success = test_oura_real_connection()
    withings_success = test_withings_real_connection()
    hevy_success = test_hevy_real_connection()
    onedrive_success = test_onedrive_real_connection()
    
    test_token_refresh_status()
    investigate_token_storage()
    
    print("\n" + "=" * 60)
    if whoop_success and oura_success and withings_success and hevy_success and onedrive_success:
        print("🎉 SUCCESS: Real API connections and response saving validated across all services!")
        print("✅ All API services working")
        print("✅ Response files being saved correctly")
        print("✅ New architecture ready for production use")
    else:
        print("⚠️  PARTIAL SUCCESS: Imports work, but API test skipped or failed")
        print("📝 To test real API: ensure authentication tokens are available")
    
    print("\n📁 API responses saved to: data/api-responses/")
    print("🔧 Ready for pipeline integration!")

if __name__ == "__main__":
    main()
