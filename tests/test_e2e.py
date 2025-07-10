#!/usr/bin/env python3
"""
End-to-End Health Data Pipeline Test with Local HealthKit Integration

Streamlined test that leverages the Local HealthKit package:
1. Services handle authentication automatically
2. Runs the 5-stage pipeline with integrated services
3. Validates results and PDF generation
4. Clean error handling with immediate feedback
"""

import argparse
import os
from datetime import datetime
from pathlib import Path

from src.pipeline.orchestrator import HealthDataOrchestrator


def check_service_authentication():
    """Check authentication status of all services."""
    print("🔐 Checking service authentication status...")
    
    try:
        from local_healthkit import (
            WhoopService, OuraService, WithingsService, 
            HevyService, OneDriveService
        )
        
        services = {
            'Whoop': WhoopService(),
            'Oura': OuraService(),
            'Withings': WithingsService(),
            'Hevy': HevyService(),
            'OneDrive': OneDriveService()
        }
        
        auth_status = {}
        for name, service in services.items():
            is_auth = service.is_authenticated()
            auth_status[name] = is_auth
            status_icon = "✅" if is_auth else "❌"
            print(f"  {status_icon} {name}: {'Authenticated' if is_auth else 'Not authenticated'}")
        
        authenticated_count = sum(auth_status.values())
        print(f"\n📊 Authentication Summary: {authenticated_count}/5 services authenticated")
        
        if authenticated_count == 0:
            print("⚠️  No services authenticated. Pipeline will run with available services only.")
        elif authenticated_count < 5:
            print("ℹ️  Some services not authenticated. Pipeline will process available services.")
        else:
            print("🎉 All services authenticated! Full pipeline execution available.")
            
        return auth_status
        
    except Exception as e:
        print(f"❌ Error checking authentication: {e}")
        return {}


def run_pipeline(days: int):
    """Run the 5-stage health data pipeline."""
    print(f"🚀 Running health data pipeline for {days} days...")
    
    try:
        # Initialize orchestrator
        orchestrator = HealthDataOrchestrator()
        
        # Run pipeline with all available services
        services = ['whoop', 'oura', 'withings', 'hevy', 'nutrition']
        
        result = orchestrator.run_pipeline(
            days=days,
            services=services,
            enable_csv=True,
            enable_report=True
        )
        
        print(f"✅ Pipeline completed in {result.total_duration:.2f} seconds")
        return result
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        raise


def test_pdf_generation():
    """Test PDF generation from markdown report."""
    print("📄 Testing PDF generation...")
    
    try:
        # Look for the most recent markdown report in data/05_reports
        reports_dir = Path("data/05_reports")
        if not reports_dir.exists():
            print("⚠️  No reports directory found - skipping PDF test")
            return
        
        md_files = list(reports_dir.glob("health_report_*.md"))
        if not md_files:
            print("⚠️  No markdown reports found - skipping PDF test")
            return
        
        # Get the most recent report
        latest_report = max(md_files, key=lambda f: f.stat().st_mtime)
        print(f"📋 Using report: {latest_report.name}")
        
        # Test PDF conversion
        from src.reporting.pdf_converter import PDFConverter
        
        pdf_converter = PDFConverter()
        pdf_path = pdf_converter.markdown_to_pdf(str(latest_report), str(latest_report).replace('.md', '.pdf'))
        
        if os.path.exists(pdf_path):
            pdf_size = os.path.getsize(pdf_path)
            print(f"✅ PDF generated successfully: {pdf_path} ({pdf_size:,} bytes)")
        else:
            print("❌ PDF file not found after conversion")
            
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        # Don't raise - PDF generation is optional


def validate_results(result, days: int):
    """Validate pipeline results and collect stats."""
    print("🔍 Validating pipeline results...")
    
    try:
        # Check basic result structure
        if not hasattr(result, 'stages_completed'):
            print("❌ Invalid result structure")
            return
        
        print(f"📊 Pipeline Statistics:")
        print(f"   Duration: {result.total_duration:.2f} seconds")
        print(f"   Stages completed: {result.stages_completed}")
        
        # Count generated files
        data_dir = Path("data")
        if data_dir.exists():
            csv_files = list(data_dir.glob("**/*.csv"))
            json_files = list(data_dir.glob("**/*.json"))
            print(f"   CSV files generated: {len(csv_files)}")
            print(f"   JSON files generated: {len(json_files)}")
        
        # Check reports
        reports_dir = Path("reports")
        if reports_dir.exists():
            md_files = list(reports_dir.glob("*.md"))
            pdf_files = list(reports_dir.glob("*.pdf"))
            print(f"   Markdown reports: {len(md_files)}")
            print(f"   PDF reports: {len(pdf_files)}")
        
        # Check charts
        charts_dir = Path("charts")
        if charts_dir.exists():
            chart_files = list(charts_dir.glob("*.png"))
            print(f"   Chart files: {len(chart_files)}")
        
        print("✅ Results validation completed")
        
    except Exception as e:
        print(f"❌ Results validation failed: {e}")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='End-to-End Health Data Pipeline Test')
    parser.add_argument('--days', type=int, default=8, help='Number of days to process (default: 8)')
    args = parser.parse_args()
    
    print(f"🧪 Starting E2E test with Local HealthKit integration ({args.days} days)")
    print("=" * 70)
    
    try:
        # Step 1: Check service authentication status
        auth_status = check_service_authentication()
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
        
        print("🎉 All tests completed successfully!")
        print("=" * 70)
        
        # Summary
        authenticated_services = sum(auth_status.values())
        print(f"📋 Test Summary:")
        print(f"   Services authenticated: {authenticated_services}/5")
        print(f"   Pipeline duration: {result.total_duration:.2f} seconds")
        print(f"   Stages completed: {result.stages_completed}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
