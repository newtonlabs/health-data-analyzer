#!/usr/bin/env python3
"""Test script to validate the legacy shim functionality."""

import sys
from datetime import datetime, timedelta

from src.pipeline.legacy_shim import LegacyAggregatorAdapter
from src.reporting.report_generator import ReportGenerator


def test_legacy_shim():
    """Test the legacy shim with actual aggregated data."""
    print("🔧 Testing Legacy Shim Functionality")
    print("=" * 50)
    
    # Initialize the shim adapter
    adapter = LegacyAggregatorAdapter()
    
    # Set up date range (last 7 days)
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 Date Range: {start_date.date()} to {end_date.date()}")
    print()
    
    # Test macros and activity data
    print("📊 Testing Macros & Activity Data:")
    try:
        macros_df = adapter.weekly_macros_and_activity(start_date, end_date)
        print(f"   ✅ Loaded {len(macros_df)} macros records")
        if not macros_df.empty:
            print(f"   📋 Columns: {list(macros_df.columns)}")
            print(f"   📈 Sample data:")
            print(macros_df.head(2).to_string(index=False))
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test recovery metrics data
    print("💤 Testing Recovery Metrics Data:")
    try:
        recovery_df = adapter.recovery_metrics(start_date, end_date)
        print(f"   ✅ Loaded {len(recovery_df)} recovery records")
        if not recovery_df.empty:
            print(f"   📋 Columns: {list(recovery_df.columns)}")
            print(f"   📈 Sample data:")
            print(recovery_df.head(2).to_string(index=False))
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test training metrics data
    print("🏋️ Testing Training Metrics Data:")
    try:
        training_df = adapter.training_metrics(start_date, end_date)
        print(f"   ✅ Loaded {len(training_df)} training records")
        if not training_df.empty:
            print(f"   📋 Columns: {list(training_df.columns)}")
            print(f"   📈 Sample data:")
            print(training_df.head(2).to_string(index=False))
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test report generation
    print("📄 Testing Report Generation:")
    try:
        report_gen = ReportGenerator(adapter)
        report_content = report_gen.generate_weekly_status(start_date, end_date)
        
        print(f"   ✅ Generated report ({len(report_content)} characters)")
        print(f"   📝 Report preview (first 500 chars):")
        print("-" * 50)
        print(report_content[:500] + "..." if len(report_content) > 500 else report_content)
        print("-" * 50)
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    print("🎉 Legacy Shim Test Complete!")


if __name__ == "__main__":
    test_legacy_shim()
