#!/usr/bin/env python3
"""
Simple example of using the experimental OAuth2 clients.
This script demonstrates basic usage for both Whoop and Withings APIs.
"""

from whoop_client import WhoopClientExperimental
from withings_client import WithingsClientExperimental
from datetime import datetime, timedelta
import json

def test_whoop_client():
    """Test the Whoop client with basic data retrieval."""
    print("🏃 Testing Whoop Client")
    print("-" * 30)
    
    try:
        # Initialize client (reads WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET from environment)
        client = WhoopClientExperimental()
        
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
        client = WithingsClientExperimental()
        
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

def check_authentication_status():
    """Check the authentication status of both clients."""
    print("🔐 Authentication Status")
    print("-" * 30)
    
    # Check Whoop
    try:
        whoop = WhoopClientExperimental()
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
        withings = WithingsClientExperimental()
        withings_auth = withings.is_authenticated()
        withings_sliding = withings.is_in_sliding_window()
        
        print(f"Withings:")
        print(f"   Authenticated: {'✅ Yes' if withings_auth else '❌ No'}")
        print(f"   In sliding window: {'✅ Yes' if withings_sliding else '❌ No'}")
        if withings_sliding:
            print(f"   Days remaining: ~89 days")
        
    except Exception as e:
        print(f"Withings status check failed: {e}")

def main():
    """Main function to run all tests."""
    print("🚀 Experimental OAuth2 Clients - Example Usage")
    print("=" * 60)
    print()
    
    # Check authentication status first
    check_authentication_status()
    print()
    
    # Test both clients
    whoop_success = test_whoop_client()
    print()
    
    withings_success = test_withings_client()
    print()
    
    # Summary
    print("📋 Summary")
    print("-" * 30)
    print(f"Whoop: {'✅ Success' if whoop_success else '❌ Failed'}")
    print(f"Withings: {'✅ Success' if withings_success else '❌ Failed'}")
    
    if whoop_success or withings_success:
        print("\n🎉 At least one client is working!")
        print("\n💡 Tips:")
        print("   - Tokens are saved locally and persist across runs")
        print("   - Sessions last up to 89 days with sliding window")
        print("   - Re-authentication is automatic when needed")
        print("   - Use localhost callback for better UX")
    else:
        print("\n⚠️ Both clients failed. Check your environment variables:")
        print("   - WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET")
        print("   - WITHINGS_CLIENT_ID and WITHINGS_CLIENT_SECRET")

if __name__ == "__main__":
    main()
