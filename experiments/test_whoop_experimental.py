#!/usr/bin/env python3
"""Test script for experimental Whoop client using authlib."""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.whoop_client import WhoopClientExperimental


def main():
    """Test the experimental Whoop client."""
    print("🧪 Testing Experimental Whoop Client with Authlib")
    print("=" * 50)
    
    try:
        # Initialize the client (will read from environment variables)
        client = WhoopClientExperimental()
        
        print(f"✅ Client initialized successfully")
        print(f"📁 Token file: {client.token_file}")
        print(f"🔗 Redirect URI: {client.redirect_uri}")
        print(f"🎯 Scopes: {', '.join(client.scopes)}")
        print()
        
        # Check if already authenticated
        if client.is_authenticated():
            print("✅ Already authenticated with valid token")
        else:
            print("⚠️  Not authenticated or token expired")
            print("Starting authentication flow...")
            
            if not client.authenticate():
                print("❌ Authentication failed")
                return
            
            print("✅ Authentication successful!")
        
        print()
        print("🏋️  Testing workout data fetch...")
        
        # Test fetching workouts for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print("🏋️  Testing workout data fetch...")
        print(f"📅 Fetching workouts from {start_date.date()} to {end_date.date()}")
        
        workouts = client.get_workouts(start_date, end_date, limit=10)
        
        # Print the full JSON response for validation
        print("\n🔍 Full API Response:")
        import json
        print(json.dumps(workouts, indent=2, default=str))
        print()
        
        print(f"📊 Results:")
        print(f"   - Total workouts: {len(workouts['records'])}")
        
        if workouts['records']:
            first_workout = workouts['records'][0]
            print(f"   - First workout ID: {first_workout.get('id', 'N/A')}")
            print(f"   - First workout sport: {first_workout.get('sport_id', 'N/A')}")
        
        print()
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
