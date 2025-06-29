#!/usr/bin/env python3
"""Debug script to test chart generation."""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline.legacy_shim import MemoryBasedLegacyShim
from src.reporting.report_generator import ReportGenerator
from src.pipeline.orchestrator import HealthDataOrchestrator

def debug_chart_generation():
    """Debug chart generation specifically."""
    print("🔍 Testing chart generation...")
    
    # Run pipeline to get aggregated data
    orchestrator = HealthDataOrchestrator()
    result = orchestrator.run_pipeline(
        days=8,
        services=['whoop', 'oura', 'withings', 'hevy', 'nutrition'],
        enable_csv=True,
        debug_mode=False,
        enable_report=False  # Don't generate report yet
    )
    
    if not result.success:
        print("❌ Pipeline failed, can't test charts")
        return
    
    print("✅ Pipeline completed, testing chart generation...")
    
    # Create shim and report generator
    shim = MemoryBasedLegacyShim(result.context.aggregated_data)
    report_gen = ReportGenerator(shim)
    
    # Test individual chart generation methods
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    print("\n📊 Testing individual chart methods...")
    
    # Test recovery data
    try:
        recovery_df = shim.recovery_metrics(start_date, end_date)
        print(f"Recovery data shape: {recovery_df.shape}")
        print(f"Recovery columns: {list(recovery_df.columns)}")
        if not recovery_df.empty:
            print("Sample recovery data:")
            print(recovery_df.head())
        
        # Test recovery chart generation
        recovery_chart = report_gen._generate_recovery_chart(recovery_df)
        print(f"Recovery chart result: {recovery_chart}")
        
    except Exception as e:
        print(f"❌ Recovery chart failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test macros data
    try:
        macros_df = shim.weekly_macros_and_activity(start_date, end_date)
        print(f"\nMacros data shape: {macros_df.shape}")
        print(f"Macros columns: {list(macros_df.columns)}")
        if not macros_df.empty:
            print("Sample macros data:")
            print(macros_df.head())
        
        # Test nutrition chart generation
        nutrition_chart = report_gen._generate_nutrition_chart(macros_df)
        print(f"Nutrition chart result: {nutrition_chart}")
        
    except Exception as e:
        print(f"❌ Nutrition chart failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_chart_generation()
