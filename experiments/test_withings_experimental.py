#!/usr/bin/env python3
"""Test script for experimental Withings client using authlib."""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.withings_client import WithingsClientExperimental


def main():
    """Test the experimental Withings client."""
    print("🧪 Testing Experimental Withings Client with Authlib")
    print("=" * 55)
    
    try:
        # Initialize the client (will read from environment variables)
        client = WithingsClientExperimental()
        
        print(f"✅ Client initialized successfully")
        print(f"📁 Token file: {client.token_file}")
        print(f"🔗 Redirect URI: {client.redirect_uri}")
        print(f"🎯 Scopes: {', '.join(client.scopes)}")
        print(f"⏰ Validity period: {client.validity_days} days")
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
        
        # Test date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Test date range: {start_date.date()} to {end_date.date()}")
        print()
        
        # Test: Weight data
        print("⚖️  Testing weight data fetch...")
        weight_data = client.get_weight_data(start_date, end_date)
        print(f"📊 Weight data results:")
        
        # Print the full JSON response for validation
        print("\n🔍 Full API Response:")
        import json
        print(json.dumps(weight_data, indent=2, default=str))
        print()
        
        measuregrps = weight_data.get('measuregrps', [])
        print(f"   - Total measurement groups: {len(measuregrps)}")
        
        if measuregrps:
            # Show first measurement details
            first_measurement = measuregrps[0]
            print(f"   - First measurement date: {datetime.fromtimestamp(first_measurement.get('date', 0))}")
            print(f"   - Measurement group ID: {first_measurement.get('grpid', 'N/A')}")
            
            measures = first_measurement.get('measures', [])
            print(f"   - Number of measures in first group: {len(measures)}")
        
        print("   ✅ Weight data fetch successful!")
        print()
        
        # Test 5: Authentication persistence
        print("🔐 Test 5: Testing authentication persistence...")
        is_in_window = client.is_in_sliding_window()
        should_refresh = client.should_refresh_proactively()
        
        print(f"   - In sliding window: {'✅ Yes' if is_in_window else '❌ No'}")
        print(f"   - Should refresh proactively: {'✅ Yes' if should_refresh else '❌ No'}")
        
        if client.token and 'sliding_window_expires_at' in client.token:
            sliding_expires = datetime.fromtimestamp(client.token['sliding_window_expires_at'])
            days_remaining = (sliding_expires - datetime.now()).days
            print(f"   - Days until re-authentication needed: {days_remaining}")
        
        print("   ✅ Authentication persistence check complete!")
        
        print()
        print("✅ All Withings experimental client tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
