#!/usr/bin/env python3
"""Test script for the complete 4-stage health data pipeline.

This script tests the new aggregation stage (stage 4) along with the existing
3-stage pipeline to create daily health data summaries.
"""

import sys
from datetime import date

from src.pipeline.clean_pipeline import CleanHealthPipeline


def test_4stage_pipeline(days: int = 1):
    """Test the complete 4-stage pipeline."""
    print("🚀 TESTING 4-STAGE HEALTH DATA PIPELINE")
    print("=" * 50)
    print(f"📅 Processing {days} day(s)")
    print()
    
    # Initialize pipeline
    pipeline = CleanHealthPipeline()
    
    # Run complete 4-stage pipeline
    results = pipeline.run_full_pipeline(days=days)
    
    # Display results
    print("🎯 PIPELINE RESULTS")
    print("=" * 30)
    print(f"📅 Date range: {results['start_date'].date()} to {results['end_date'].date()}")
    print(f"📊 Days processed: {results['days_processed']}")
    print(f"🔄 Stages completed: {results['stages_completed']}/4")
    print()
    
    # Service results
    print("📊 SERVICE PROCESSING RESULTS")
    print("-" * 35)
    for service, service_results in results['services_processed'].items():
        if 'error' in service_results:
            print(f"❌ {service.title()}: {service_results['error']}")
        else:
            print(f"✅ {service.title()}: Processed successfully")
    print()
    
    # Aggregation results
    print("🔄 AGGREGATION RESULTS")
    print("-" * 25)
    print(f"📊 Total aggregations created: {results['aggregations_created']}")
    print()
    
    # Check for aggregated files
    import os
    agg_dir = "data/04_aggregated"
    if os.path.exists(agg_dir):
        agg_files = [f for f in os.listdir(agg_dir) if f.endswith('.csv')]
        print(f"📁 Aggregated CSV files: {len(agg_files)}")
        for file in sorted(agg_files):
            print(f"   📄 {file}")
    else:
        print("📁 No aggregated files directory found")
    
    print()
    
    # Overall status
    if results['stages_completed'] == 4:
        print("🎉 SUCCESS: Complete 4-stage pipeline executed!")
    else:
        print(f"⚠️  PARTIAL: Only {results['stages_completed']}/4 stages completed")
    
    return results


if __name__ == "__main__":
    # Parse command line arguments
    days = 1
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Usage: python test_4stage_pipeline.py [days]")
            sys.exit(1)
    
    # Run the test
    test_4stage_pipeline(days=days)
