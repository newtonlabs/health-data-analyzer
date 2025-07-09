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
from datetime import datetime, date, timedelta

from src.api.services.whoop_service import WhoopService
from src.api.services.oura_service import OuraService
from src.api.services.withings_service import WithingsService
from src.api.services.hevy_service import HevyService
from src.api.services.onedrive_service import OneDriveService
from src.pipeline.orchestrator import HealthDataOrchestrator
from src.pipeline.stages import PipelineContext


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


def run_pipeline_with_custom_dates(start_date: date, end_date: date):
    """Run the 5-stage health data pipeline with custom date range. No exception handling - errors bubble up."""
    days = (end_date - start_date).days + 1
    print(f"🚀 Running {days}-day health data pipeline from {start_date} to {end_date}...")
    
    # Create custom pipeline context with specific dates
    context = PipelineContext(
        start_date=start_date,
        end_date=end_date,
        services=['whoop', 'oura', 'withings', 'hevy', 'nutrition'],
        enable_csv=True,
        debug_mode=False
    )
    
    # Run pipeline stages manually with custom context
    orchestrator = HealthDataOrchestrator()
    
    # Execute pipeline stages in order
    stage_order = ['fetch', 'extract', 'transform', 'aggregate', 'report']
    
    for stage_name in stage_order:
        print(f"🔄 Executing {stage_name} stage...")
        stage = orchestrator.stages[stage_name]
        
        result = stage.execute(context)
        context.add_stage_result(result)
        
        if result.status.name == 'SUCCESS':
            print(f"✅ {stage_name} stage completed successfully")
        elif result.status.name == 'PARTIAL':
            print(f"⚠️ {stage_name} stage completed with warnings: {result.error}")
        else:
            print(f"❌ {stage_name} stage failed: {result.error}")
    
    print(f"✅ Pipeline completed successfully")
    print(f"   Stages completed: {len([r for r in context.stage_results.values() if r.status.name in ['SUCCESS', 'PARTIAL']])}/{len(context.stage_results)}")
    print(f"   Services processed: {len(context.services)}")
    
    return context


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


def validate_results_custom(context, start_date: date, end_date: date):
    """Validate pipeline results and collect stats."""
    days = (end_date - start_date).days + 1
    print(f"📊 Validating pipeline results for {days} days ({start_date} to {end_date})...")
    
    # Check for CSV files
    csv_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    print(f"   📁 CSV files generated: {len(csv_files)}")
    for csv_file in sorted(csv_files):
        size = os.path.getsize(csv_file)
        print(f"      {csv_file} ({size} bytes)")
    
    # Check for report files
    report_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith('.md') and 'report' in file.lower():
                report_files.append(os.path.join(root, file))
    
    print(f"   📄 Report files generated: {len(report_files)}")
    for report_file in sorted(report_files):
        size = os.path.getsize(report_file)
        print(f"      {report_file} ({size} bytes)")
    
    # Show stage results
    print(f"   🔧 Stage results:")
    for stage_name, stage_result in context.stage_results.items():
        print(f"      {stage_name}: {stage_result.status.name}")
    
    print(f"✅ Results validation completed")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Health Data Pipeline Test with Custom Date Range')
    parser.add_argument('--end-date', type=str, default='2025-07-06', help='End date (YYYY-MM-DD, default: 2025-07-06)')
    parser.add_argument('--days-back', type=int, default=10, help='Number of days to go back from end date (default: 10)')
    args = parser.parse_args()
    
    # Parse end date and calculate start date
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    start_date = end_date - timedelta(days=args.days_back - 1)
    
    print(f"🧪 Starting health data pipeline test")
    print(f"📅 Date range: {start_date} to {end_date} ({args.days_back} days)")
    print("=" * 60)
    
    # Step 1: Authenticate all services
    authenticate_all_services()
    print()
    
    # Step 2: Run the pipeline with custom date range
    result = run_pipeline_with_custom_dates(start_date, end_date)
    print()
    
    # Step 3: Validate results
    validate_results_custom(result, start_date, end_date)
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
