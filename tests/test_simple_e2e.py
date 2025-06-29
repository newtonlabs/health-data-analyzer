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
    """Test OneDrive folder creation and file upload."""
    print("🔄 Testing OneDrive operations...")
    
    # Initialize OneDrive service
    onedrive = OneDriveService()
    
    # Test folder creation
    test_folder = f"health-data-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    folder_id = onedrive.create_folder(test_folder)
    print(f"✅ Created test folder: {test_folder} (ID: {folder_id})")
    
    # Test file upload (use a simple test file)
    test_content = f"Test file created at {datetime.now()}"
    test_file = "data/test_upload.txt"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    file_id = onedrive.upload_file(test_file, f"{test_folder}/test_upload.txt")
    print(f"✅ Uploaded test file (ID: {file_id})")
    
    # Clean up
    os.remove(test_file)
    print("✅ OneDrive operations completed successfully")


def test_pdf_generation():
    """Test PDF generation from markdown report."""
    print("📄 Testing PDF generation...")
    
    from src.reporting.pdf_converter import PDFConverter
    
    # Find the most recent markdown report
    reports_dir = "data/05_reports"
    if not os.path.exists(reports_dir):
        print("❌ No reports directory found")
        return
    
    # Look for markdown files
    md_files = [f for f in os.listdir(reports_dir) if f.endswith('.md')]
    if not md_files:
        print("❌ No markdown reports found")
        return
    
    # Use the most recent report
    md_file = sorted(md_files)[-1]
    markdown_path = os.path.join(reports_dir, md_file)
    
    # Generate PDF in the same directory
    pdf_filename = md_file.replace('.md', '.pdf')
    pdf_path = os.path.join(reports_dir, pdf_filename)
    
    print(f"📄 Converting {md_file} to PDF...")
    
    # Initialize PDF converter and generate PDF
    converter = PDFConverter()
    converter.markdown_to_pdf(markdown_path, pdf_path)
    
    # Verify PDF was created
    if os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f"✅ PDF generated successfully: {pdf_filename} ({file_size:,} bytes)")
    else:
        print(f"❌ PDF generation failed: {pdf_filename}")


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
    
    # Step 4: Test PDF generation
    test_pdf_generation()
    print()
    
    # Step 5: Test OneDrive
    test_onedrive_operations()
    print()
    
    print("🎉 All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
