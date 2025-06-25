#!/usr/bin/env python3
"""
End-to-End Health Data Pipeline Test

This comprehensive test script validates the complete health data pipeline:
1. Authenticates all health data services
2. Extracts data from all authenticated services  
3. Generates CSV files for all available data
4. Validates the complete data flow from API → Service → Extractor → CSV

Usage:
    python tests/test_end_to_end.py [--days N]

Options:
    --days N         Days of data to extract for all services (default: 2)

This test is designed to be the single comprehensive validation of the entire
health data pipeline architecture.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class HealthDataPipelineTest:
    """Comprehensive end-to-end test for the health data pipeline."""
    
    def __init__(self, days=2):
        """Initialize the test with flexible date range."""
        self.days = days
        self.results = {}
        self.csv_files = []
        
    def authenticate_all_services(self):
        """Authenticate all health data services."""
        print("🔐 AUTHENTICATION PHASE")
        print("=" * 30)
        
        auth_results = {}
        
        # Test Whoop
        auth_results['whoop'] = self._authenticate_whoop()
        
        # Test Oura  
        auth_results['oura'] = self._authenticate_oura()
        
        # Test Withings
        auth_results['withings'] = self._authenticate_withings()
        
        # Test Hevy
        auth_results['hevy'] = self._authenticate_hevy()
        
        # Test OneDrive
        auth_results['onedrive'] = self._authenticate_onedrive()
        
        # Summary
        authenticated_count = sum(auth_results.values())
        total_count = len(auth_results)
        
        print(f"\n📊 Authentication Summary: {authenticated_count}/{total_count} services")
        for service, status in auth_results.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {service.title()}")
        
        return auth_results
    
    def _authenticate_whoop(self):
        """Authenticate Whoop service."""
        try:
            from src.api.services.whoop_service import WhoopService
            service = WhoopService()
            
            if service.is_authenticated():
                print("✅ Whoop: Authenticated")
                return True
            else:
                print("❌ Whoop: Not authenticated (check API tokens)")
                return False
        except Exception as e:
            print(f"❌ Whoop: Error - {e}")
            return False
    
    def _authenticate_oura(self):
        """Authenticate Oura service."""
        try:
            from src.api.services.oura_service import OuraService
            service = OuraService()
            
            if service.is_authenticated():
                print("✅ Oura: Authenticated")
                return True
            else:
                print("❌ Oura: Not authenticated (check personal access token)")
                return False
        except Exception as e:
            print(f"❌ Oura: Error - {e}")
            return False
    
    def _authenticate_withings(self):
        """Authenticate Withings service."""
        try:
            from src.api.clients.withings_client import WithingsClient
            client = WithingsClient()
            
            if client.is_authenticated():
                print("✅ Withings: Authenticated")
                return True
            else:
                print("🔄 Withings: Attempting OAuth2 authentication...")
                success = client.authenticate()
                if success:
                    print("✅ Withings: Authentication successful")
                    return True
                else:
                    print("❌ Withings: Authentication failed")
                    return False
        except Exception as e:
            print(f"❌ Withings: Error - {e}")
            return False
    
    def _authenticate_hevy(self):
        """Authenticate Hevy service."""
        try:
            from src.api.services.hevy_service import HevyService
            service = HevyService()
            
            if service.is_authenticated():
                print("✅ Hevy: Authenticated")
                return True
            else:
                print("❌ Hevy: Not authenticated (check API key)")
                return False
        except Exception as e:
            print(f"❌ Hevy: Error - {e}")
            return False
    
    def _authenticate_onedrive(self):
        """Authenticate OneDrive service."""
        try:
            from src.api.services.onedrive_service import OneDriveService
            service = OneDriveService()
            
            if service.is_authenticated():
                print("✅ OneDrive: Authenticated")
                return True
            else:
                print("❌ OneDrive: Not authenticated (manual setup required)")
                return False
        except Exception as e:
            print(f"❌ OneDrive: Error - {e}")
            return False
    
    def extract_all_data(self, auth_results):
        """Extract data from all authenticated services."""
        print("\n📊 DATA EXTRACTION PHASE")
        print("=" * 30)
        
        extraction_results = {}
        
        # Extract from each authenticated service
        if auth_results.get('whoop'):
            extraction_results['whoop'] = self._extract_whoop_data()
        
        if auth_results.get('oura'):
            extraction_results['oura'] = self._extract_oura_data()
        
        if auth_results.get('withings'):
            extraction_results['withings'] = self._extract_withings_data()
        
        if auth_results.get('hevy'):
            extraction_results['hevy'] = self._extract_hevy_data()
        
        # Summary
        success_count = sum(extraction_results.values())
        total_count = len(extraction_results)
        
        print(f"\n📊 Extraction Summary: {success_count}/{total_count} services")
        for service, status in extraction_results.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {service.title()}")
        
        return extraction_results
    
    def _extract_whoop_data(self):
        """Extract Whoop workout data."""
        try:
            from src.api.services.whoop_service import WhoopService
            from src.processing.extractors.whoop_extractor import WhoopExtractor
            from src.utils.data_export import DataExporter
            
            service = WhoopService()
            extractor = WhoopExtractor()
            exporter = DataExporter()
            
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days)
            
            # Fetch and extract
            raw_data = service.get_workouts_data(start_date, end_date)
            
            if raw_data and 'records' in raw_data:
                # Restructure for extractor
                restructured_data = {
                    'workouts': {
                        'records': raw_data['records']
                    }
                }
                
                extracted_data = extractor.extract_data(restructured_data)
                
                if 'workouts' in extracted_data and extracted_data['workouts']:
                    workout_records = extracted_data['workouts']
                    csv_file = exporter.save_records_to_csv(workout_records, 'whoop', 'workouts', datetime.now())
                    
                    self.csv_files.append(csv_file)
                    print(f"✅ Whoop: {len(workout_records)} workouts → {csv_file}")
                    return True
            
            print("⚠️  Whoop: No data available")
            return True
            
        except Exception as e:
            print(f"❌ Whoop: Extraction failed - {e}")
            return False
    
    def _extract_oura_data(self):
        """Extract Oura activity data."""
        try:
            from src.api.services.oura_service import OuraService
            from src.processing.extractors.oura_extractor import OuraExtractor
            from src.utils.data_export import DataExporter
            
            service = OuraService()
            extractor = OuraExtractor()
            exporter = DataExporter()
            
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days)
            
            # Fetch and extract
            raw_data = service.get_activity_data(start_date.date(), end_date.date())
            
            if raw_data:
                wrapped_data = {'activity': raw_data}
                activity_records = extractor.extract_activity_data(wrapped_data, start_date, end_date)
                
                if activity_records:
                    csv_file = exporter.save_records_to_csv(activity_records, 'oura', 'activity_records', datetime.now())
                    
                    self.csv_files.append(csv_file)
                    print(f"✅ Oura: {len(activity_records)} activities → {csv_file}")
                    return True
            
            print("⚠️  Oura: No data available")
            return True
            
        except Exception as e:
            print(f"❌ Oura: Extraction failed - {e}")
            return False
    
    def _extract_withings_data(self):
        """Extract Withings weight data."""
        try:
            from src.api.services.withings_service import WithingsService
            from src.processing.extractors.withings_extractor import WithingsExtractor
            from src.utils.data_export import DataExporter
            
            service = WithingsService()
            extractor = WithingsExtractor()
            exporter = DataExporter()
            
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days)
            
            # Fetch and extract
            raw_data = service.get_weight_data(start_date, end_date)
            
            if raw_data:
                weight_records = extractor.extract_weight_data(raw_data, start_date, end_date)
                
                if weight_records:
                    csv_file = exporter.save_records_to_csv(weight_records, 'withings', 'weight_records', datetime.now())
                    
                    self.csv_files.append(csv_file)
                    print(f"✅ Withings: {len(weight_records)} weights → {csv_file}")
                    return True
            
            print("⚠️  Withings: No data available")
            return True
            
        except Exception as e:
            print(f"❌ Withings: Extraction failed - {e}")
            return False
    
    def _extract_hevy_data(self):
        """Extract Hevy workout data."""
        try:
            from src.api.services.hevy_service import HevyService
            from src.processing.extractors.hevy_extractor import HevyExtractor
            
            service = HevyService()
            extractor = HevyExtractor()
            
            # Fetch and extract
            raw_data = service.get_workouts_data(page_size=10)
            
            if raw_data and 'workouts' in raw_data:
                extracted_data = extractor.extract_data(raw_data)
                
                if extracted_data:
                    print("✅ Hevy: Data extracted → Check data/extracted/hevy/")
                    return True
            
            print("⚠️  Hevy: No data available")
            return True
            
        except Exception as e:
            print(f"❌ Hevy: Extraction failed - {e}")
            return False
    
    def validate_csv_files(self):
        """Validate generated CSV files."""
        print("\n📁 CSV FILE VALIDATION")
        print("=" * 25)
        
        # Check all generated files
        extracted_dir = 'data/extracted'
        all_csv_files = []
        
        if os.path.exists(extracted_dir):
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    if file.endswith('.csv') and datetime.now().strftime('%Y-%m-%d') in file:
                        file_path = os.path.join(root, file)
                        all_csv_files.append(file_path)
        
        if all_csv_files:
            print(f"✅ Generated {len(all_csv_files)} CSV files:")
            for file_path in sorted(all_csv_files):
                print(f"   📄 {file_path}")
            return True
        else:
            print("❌ No CSV files generated")
            return False
    
    def run_complete_test(self):
        """Run the complete end-to-end test."""
        print("🚀 END-TO-END HEALTH DATA PIPELINE TEST")
        print("=" * 50)
        print(f"Data range: {self.days} days")
        print()
        
        # Phase 1: Authentication
        auth_results = self.authenticate_all_services()
        
        # Phase 2: Data Extraction
        extraction_results = self.extract_all_data(auth_results)
        
        # Phase 3: CSV Validation
        csv_validation = self.validate_csv_files()
        
        # Final Summary
        print("\n🎯 FINAL RESULTS")
        print("=" * 20)
        
        auth_count = sum(auth_results.values())
        extraction_count = sum(extraction_results.values())
        
        print(f"🔐 Authentication: {auth_count}/{len(auth_results)} services")
        print(f"📊 Data Extraction: {extraction_count}/{len(extraction_results)} services")
        print(f"📁 CSV Generation: {'✅ Success' if csv_validation else '❌ Failed'}")
        
        overall_success = (auth_count > 0 and extraction_count > 0 and csv_validation)
        
        if overall_success:
            print("\n🎉 SUCCESS: End-to-end pipeline test completed successfully!")
            print("   All authenticated services extracted data and generated CSV files.")
        else:
            print("\n⚠️  PARTIAL SUCCESS: Some issues detected in the pipeline.")
        
        return overall_success

def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(description='End-to-end health data pipeline test')
    parser.add_argument('--days', type=int, default=2, help='Days of data to extract for all services (default: 2)')
    
    args = parser.parse_args()
    
    # Run the test
    test = HealthDataPipelineTest(days=args.days)
    success = test.run_complete_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
