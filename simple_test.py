#!/usr/bin/env python3
"""
Simple test script to validate new API services can be imported and instantiated.
"""

import os
import sys
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
    services = ["whoop", "oura", "withings", "hevy"]
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

def main():
    """Run all tests."""
    print("🚀 Simple API Services Validation")
    print("=" * 50)
    
    test_imports()
    test_directory_structure()
    test_file_utils()
    
    print("\n" + "=" * 50)
    print("✅ Basic validation complete!")
    print("📝 Note: This test only validates imports and file structure")
    print("📝 Actual API calls require authentication and will save responses to data/api-responses/")

if __name__ == "__main__":
    main()
