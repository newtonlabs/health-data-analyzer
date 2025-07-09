#!/usr/bin/env python3
"""Test script to verify the restored local-healthkit package works correctly."""

import sys
import traceback
from datetime import datetime, timedelta

def test_imports():
    """Test that all clients and services can be imported."""
    print("🔍 Testing package imports...")
    
    try:
        # Test main package import
        import local_healthkit
        print(f"✅ Main package imported - version {local_healthkit.__version__}")
        
        # Test client imports
        from local_healthkit import (
            OuraClient, HevyClient, WhoopClient, 
            WithingsClient, OneDriveClient
        )
        print("✅ All clients imported successfully")
        
        # Test service imports
        from local_healthkit import (
            OuraService, HevyService, WhoopService,
            WithingsService, OneDriveService
        )
        print("✅ All services imported successfully")
        
        # Test exception imports
        from local_healthkit import (
            LocalHealthKitError, APIClientError,
            AuthenticationError, RateLimitError
        )
        print("✅ All exceptions imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_client_initialization():
    """Test that clients can be initialized."""
    print("\n🔍 Testing client initialization...")
    
    try:
        # Test API key clients
        from local_healthkit import OuraClient, HevyClient
        
        try:
            oura = OuraClient()
            print(f"✅ OuraClient initialized - authenticated: {oura.is_authenticated()}")
        except ValueError as e:
            print(f"✅ OuraClient correctly requires API key: {str(e)[:50]}...")
        
        try:
            hevy = HevyClient()
            print(f"✅ HevyClient initialized - authenticated: {hevy.is_authenticated()}")
        except ValueError as e:
            print(f"✅ HevyClient correctly requires API key: {str(e)[:50]}...")
        
        # Test OAuth2 clients
        from local_healthkit import WhoopClient, WithingsClient, OneDriveClient
        
        try:
            whoop = WhoopClient()
            print(f"✅ WhoopClient initialized - authenticated: {whoop.is_authenticated()}")
        except ValueError as e:
            print(f"✅ WhoopClient correctly requires credentials: {str(e)[:50]}...")
        
        try:
            withings = WithingsClient()
            print(f"✅ WithingsClient initialized - authenticated: {withings.is_authenticated()}")
        except ValueError as e:
            print(f"✅ WithingsClient correctly requires credentials: {str(e)[:50]}...")
        
        try:
            onedrive = OneDriveClient()
            print(f"✅ OneDriveClient initialized - authenticated: {onedrive.is_authenticated()}")
        except ValueError as e:
            print(f"✅ OneDriveClient correctly requires credentials: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Client initialization test failed: {e}")
        traceback.print_exc()
        return False

def test_service_initialization():
    """Test that services can be initialized (they wrap clients)."""
    print("\n🔍 Testing service initialization...")
    
    try:
        from local_healthkit import (
            OuraService, HevyService, WhoopService,
            WithingsService, OneDriveService
        )
        
        # Test service initialization
        services = [
            ("OuraService", OuraService),
            ("HevyService", HevyService), 
            ("WhoopService", WhoopService),
            ("WithingsService", WithingsService),
            ("OneDriveService", OneDriveService)
        ]
        
        for name, service_class in services:
            try:
                service = service_class()
                print(f"✅ {name} initialized - authenticated: {service.is_authenticated()}")
            except ValueError as e:
                print(f"✅ {name} correctly requires credentials: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization test failed: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test that configuration classes work."""
    print("\n🔍 Testing configuration...")
    
    try:
        from local_healthkit.clients.base.config import ClientFactory
        
        # Test client config
        config = ClientFactory.get_client_config()
        print(f"✅ Client config loaded - max_retries: {config.max_retries}")
        
        # Test service configs (they return dictionaries)
        whoop_config = ClientFactory.get_service_config("WHOOP")
        print(f"✅ Whoop config loaded - base_url: {whoop_config['base_url']}")
        
        withings_config = ClientFactory.get_service_config("WITHINGS")
        print(f"✅ Withings config loaded - base_url: {withings_config['base_url']}")
        
        oura_config = ClientFactory.get_service_config("OURA")
        print(f"✅ Oura config loaded - base_url: {oura_config['base_url']}")
        
        hevy_config = ClientFactory.get_service_config("HEVY")
        print(f"✅ Hevy config loaded - base_url: {hevy_config['base_url']}")
        
        onedrive_config = ClientFactory.get_service_config("ONEDRIVE")
        print(f"✅ OneDrive config loaded - base_url: {onedrive_config['base_url']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing restored Local HealthKit package...")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_client_initialization,
        test_service_initialization,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n❌ Test {test.__name__} failed!")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The restored package is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
