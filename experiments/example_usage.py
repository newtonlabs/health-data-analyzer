#!/usr/bin/env python3
"""
Example usage of the OAuth2 health data clients.
This script demonstrates basic usage for Whoop, Withings, and OneDrive APIs.
"""

import sys
import os
from datetime import datetime, timedelta
import json

# Import the clients from the clients directory
from clients.whoop_client import WhoopClient
from clients.withings_client import WithingsClient
from clients.onedrive_client import OneDriveClient


def test_whoop_client():
    """Test the Whoop client with basic data retrieval."""
    print("🏃 Testing Whoop Client")
    print("-" * 30)
    
    try:
        # Initialize client (reads WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET from environment)
        client = WhoopClient()
        
        # Get workouts for the last 3 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        print(f"📅 Fetching workouts from {start_date.date()} to {end_date.date()}")
        
        # This will automatically handle authentication if needed
        workouts = client.get_workouts(start_date, end_date, limit=5)
        
        print(f"✅ Retrieved {len(workouts['records'])} workouts")
        
        # Show workout details
        for i, workout in enumerate(workouts['records'][:3], 1):
            score = workout.get('score', {})
            print(f"   {i}. Workout {workout['id']}")
            print(f"      Sport: {workout['sport_id']}")
            print(f"      Strain: {score.get('strain', 'N/A')}")
            print(f"      Avg HR: {score.get('average_heart_rate', 'N/A')}")
            print(f"      Date: {workout['start']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Whoop client failed: {e}")
        return False

def test_withings_client():
    """Test the Withings client with basic data retrieval."""
    print("⚖️ Testing Withings Client")
    print("-" * 30)
    
    try:
        # Initialize client (reads WITHINGS_CLIENT_ID and WITHINGS_CLIENT_SECRET from environment)
        client = WithingsClient()
        
        # Get weight data for the last week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"📅 Fetching weight data from {start_date.date()} to {end_date.date()}")
        
        # This will automatically handle authentication if needed
        weight_data = client.get_weight_data(start_date, end_date)
        
        measurements = weight_data.get('measuregrps', [])
        print(f"✅ Retrieved {len(measurements)} weight measurements")
        
        # Show recent measurements
        for i, measurement in enumerate(measurements[:5], 1):
            date = datetime.fromtimestamp(measurement['date'])
            measures = measurement.get('measures', [])
            
            print(f"   {i}. Measurement {measurement['grpid']}")
            print(f"      Date: {date.strftime('%Y-%m-%d %H:%M')}")
            
            for measure in measures:
                if measure['type'] == 1:  # Weight
                    weight_kg = measure['value'] * (10 ** measure['unit'])
                    print(f"      Weight: {weight_kg:.1f} kg")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Withings client failed: {e}")
        return False

def test_onedrive_client():
    """Test the OneDrive client with basic operations."""
    print("☁️ Testing OneDrive Client")
    print("-" * 30)
    
    try:
        # Initialize client (reads ONEDRIVE_CLIENT_ID from environment)
        client = OneDriveClient()
        
        print(f"📋 Testing OneDrive connectivity...")
        
        # List files in root folder
        files = client.list_files()
        print(f"✅ Connected to OneDrive - {len(files)} items in root folder")
        
        # Show first few items
        for i, file_info in enumerate(files[:3], 1):
            name = file_info.get('name', 'Unknown')
            file_type = 'Folder' if 'folder' in file_info else 'File'
            size = file_info.get('size', 0)
            print(f"   {i}. {name} ({file_type}) - {size:,} bytes")
        
        if len(files) > 3:
            print(f"   ... and {len(files) - 3} more items")
        print()
        
        # Test creating a demo folder
        demo_folder = f"Health-Data-Demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        print(f"📁 Creating demo folder: {demo_folder}")
        client._ensure_folder_exists(demo_folder)
        print(f"✅ Demo folder created successfully")
        
        # Create and upload a demo file
        demo_file = "health_demo.txt"
        demo_content = f"""Health Data Analyzer Demo
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a demonstration file created by the OneDrive client.
The file shows integration between health data collection and cloud storage.

Features demonstrated:
- 90-day authentication sessions
- Automatic token refresh
- Folder creation
- File upload with sharing links
"""
        
        print(f"📄 Creating demo file: {demo_file}")
        with open(demo_file, "w") as f:
            f.write(demo_content)
        
        print(f"📤 Uploading to OneDrive...")
        share_url = client.upload_file(demo_file, demo_folder)
        
        print(f"✅ File uploaded successfully!")
        print(f"🔗 Shareable link: {share_url}")
        
        # Clean up local file
        os.remove(demo_file)
        print(f"🗑️  Local demo file cleaned up")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in error_str or "SSLError" in error_str:
            print(f"⚠️  OneDrive client failed due to SSL certificate issue")
            print(f"    This is a known issue on some macOS systems")
            print(f"    The authentication works, but API calls may fail")
            print(f"    Authentication status: {'✅ Authenticated' if client.is_authenticated() else '❌ Not authenticated'}")
            return False
        else:
            print(f"❌ OneDrive client failed: {e}")
            return False

def check_authentication_status():
    """Check the authentication status of all clients."""
    print("🔐 Authentication Status")
    print("-" * 30)
    
    # Check Whoop
    try:
        whoop = WhoopClient()
        whoop_auth = whoop.is_authenticated()
        whoop_sliding = whoop.is_in_sliding_window()
        
        print(f"Whoop:")
        print(f"   Authenticated: {'✅ Yes' if whoop_auth else '❌ No'}")
        print(f"   In sliding window: {'✅ Yes' if whoop_sliding else '❌ No'}")
        if whoop_sliding:
            print(f"   Days remaining: ~89 days")
        
    except Exception as e:
        print(f"Whoop status check failed: {e}")
    
    # Check Withings
    try:
        withings = WithingsClient()
        withings_auth = withings.is_authenticated()
        withings_sliding = withings.is_in_sliding_window()
        
        print(f"Withings:")
        print(f"   Authenticated: {'✅ Yes' if withings_auth else '❌ No'}")
        print(f"   In sliding window: {'✅ Yes' if withings_sliding else '❌ No'}")
        if withings_sliding:
            print(f"   Days remaining: ~89 days")
        
    except Exception as e:
        print(f"Withings status check failed: {e}")
    
    # Check OneDrive
    try:
        onedrive = OneDriveClient()
        onedrive_auth = onedrive.is_authenticated()
        onedrive_sliding = onedrive.is_in_sliding_window()
        
        print(f"OneDrive:")
        print(f"   Authenticated: {'✅ Yes' if onedrive_auth else '❌ No'}")
        print(f"   In sliding window: {'✅ Yes' if onedrive_sliding else '❌ No'}")
        if onedrive_sliding:
            print(f"   Days remaining: ~89 days")
        
    except Exception as e:
        print(f"OneDrive status check failed: {e}")

def main():
    """Main function to run all tests."""
    print("🚀 OAuth2 Health Data Clients - Clean Implementation")
    print("=" * 60)
    print()
    
    # Check authentication status first
    check_authentication_status()
    print()
    
    # Test all three clients
    whoop_success = test_whoop_client()
    print()
    
    withings_success = test_withings_client()
    print()
    
    onedrive_success = test_onedrive_client()
    print()
    
    # Summary
    print("📋 Summary")
    print("-" * 30)
    print(f"Whoop: {'✅ Success' if whoop_success else '❌ Failed'}")
    print(f"Withings: {'✅ Success' if withings_success else '❌ Failed'}")
    print(f"OneDrive: {'✅ Success' if onedrive_success else '❌ Failed'}")
    
    success_count = sum([whoop_success, withings_success, onedrive_success])
    
    if success_count > 0:
        print(f"\n🎉 {success_count}/3 clients are working!")
        print("\n💡 Tips:")
        print("   - Tokens are saved locally and persist across runs")
        print("   - Sessions last up to 89 days with sliding window")
        print("   - Re-authentication is automatic when needed")
        print("   - OneDrive provides cloud storage for health reports")
        print("   - All clients use the same authentication patterns")
        print("\n🏗️ Architecture:")
        print("   - Clean naming (no 'experimental' suffixes)")
        print("   - Production-ready structure")
        print("   - Modular design with shared base classes")
        print("   - Standard token file names (~/.service_tokens.json)")
    else:
        print("\n⚠️ All clients failed. Check your environment variables:")
        print("   - WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET")
        print("   - WITHINGS_CLIENT_ID and WITHINGS_CLIENT_SECRET")
        print("   - ONEDRIVE_CLIENT_ID")
        print("   - Ensure .env file is properly configured")

if __name__ == "__main__":
    main()
