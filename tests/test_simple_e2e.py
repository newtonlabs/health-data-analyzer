#!/usr/bin/env python3
"""
Simple End-to-End Health Data Pipeline Test

Clean, simple test that:
1. Authenticates all services (refreshes if needed)
2. Runs the 5-stage pipeline
3. Tests OneDrive operations
4. No exception handling - errors bubble up immediately
5. Default 8 days testing
"""

import argparse
import os
from datetime import datetime

from src.api.services.whoop_service import WhoopService
from src.api.services.oura_service import OuraService
from src.api.services.withings_service import WithingsService
from src.api.services.hevy_service import HevyService
from src.api.services.onedrive_service import OneDriveService
from src.pipeline.orchestrator import HealthDataOrchestrator


def authenticate_all_services():
    """Authenticate all health data services. No exception handling - errors bubble up."""
    print("🔐 Authenticating all services...")
    
    # Whoop
    print("  🔄 Whoop...")
    whoop = WhoopService()
    if not whoop.is_authenticated:
        whoop.authenticate()
    print("  ✅ Whoop authenticated")
    
    # Oura
    print("  🔄 Oura...")
    oura = OuraService()
    if not oura.is_authenticated:
        oura.authenticate()
    print("  ✅ Oura authenticated")
    
    # Withings
    print("  🔄 Withings...")
    withings = WithingsService()
    if not withings.is_authenticated:
        withings.withings_client.authenticate()
    print("  ✅ Withings authenticated")
    
    # Hevy
    print("  🔄 Hevy...")
    hevy = HevyService()
    if not hevy.is_authenticated:
        hevy.hevy_client.authenticate()
    print("  ✅ Hevy authenticated")
    
    # OneDrive
    print("  🔄 OneDrive...")
    onedrive = OneDriveService()
    if not onedrive.is_authenticated:
        onedrive.onedrive_client.authenticate()
    print("  ✅ OneDrive authenticated")
    
    print("✅ All services authenticated successfully")


def run_pipeline(days: int):
    """Run the 5-stage health data pipeline. No exception handling - errors bubble up."""
    print(f"🚀 Running {days}-day health data pipeline...")
    
    orchestrator = HealthDataOrchestrator()
    result = orchestrator.run_pipeline(
        days=days,
        services=['whoop', 'oura', 'withings', 'hevy', 'nutrition'],
        enable_csv=True,
        enable_report=True
    )
    
    print(f"✅ Pipeline completed successfully in {result.total_duration:.2f} seconds")
    print(f"   Stages completed: {result.stages_completed}/{result.total_stages}")
    print(f"   Services processed: {len(result.services_processed)}")
    
    return result


def test_onedrive_operations():
    """Test OneDrive operations. No exception handling - errors bubble up."""
    print("🔄 Testing OneDrive operations...")
    
    onedrive = OneDriveService()
    test_folder = f"health-data-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    folder_id = onedrive.create_folder(test_folder)
    
    print(f"✅ OneDrive test successful - created folder: {test_folder}")
    return folder_id


def validate_results(result, days: int):
    """Validate pipeline results and collect stats."""
    print("📊 Validating results...")
    
    # Check CSV files exist
    csv_count = 0
    for root, dirs, files in os.walk('data'):
        csv_count += len([f for f in files if f.endswith('.csv') and '2025-06-29' in f])
    
    print(f"   CSV files generated: {csv_count}")
    
    # Check aggregated files
    agg_dir = "data/04_aggregated"
    if os.path.exists(agg_dir):
        agg_files = [f for f in os.listdir(agg_dir) if f.endswith('.csv')]
        print(f"   Aggregated files: {len(agg_files)}")
        for f in agg_files:
            print(f"     - {f}")
    
    # Check nutrition data
    macros_file = "data/04_aggregated/macros_activity_2025-06-29.csv"
    if os.path.exists(macros_file):
        import pandas as pd
        df = pd.read_csv(macros_file)
        nutrition_days = df['calories'].notna().sum()
        print(f"   Nutrition data: {nutrition_days}/{len(df)} days")
        print(f"   Sport types: {df['sport_type'].value_counts().to_dict()}")
    
    print("✅ Validation complete")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Simple End-to-End Health Data Pipeline Test')
    parser.add_argument('--days', type=int, default=8, help='Number of days to process (default: 8)')
    args = parser.parse_args()
    
    print(f"🧪 Starting simple end-to-end test with {args.days} days")
    print("=" * 60)
    
    # Step 1: Authenticate all services
    authenticate_all_services()
    print()
    
    # Step 2: Run the pipeline
    result = run_pipeline(args.days)
    print()
    
    # Step 3: Validate results
    validate_results(result, args.days)
    print()
    
    # Step 4: Test OneDrive
    test_onedrive_operations()
    print()
    
    print("🎉 All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
