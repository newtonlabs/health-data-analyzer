#!/usr/bin/env python3
"""Debug script to test report generation with memory-based shim."""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline.orchestrator import HealthDataOrchestrator

def debug_report_generation():
    """Debug the report generation issue."""
    orchestrator = HealthDataOrchestrator()
    
    print("🔍 Running pipeline to debug report generation...")
    
    # Run pipeline with minimal data
    result = orchestrator.run_pipeline(
        days=2,
        services=['whoop', 'oura', 'withings', 'hevy', 'nutrition'],
        enable_csv=True,
        debug_mode=True,
        enable_report=True
    )
    
    print(f"Pipeline success: {result.success}")
    print(f"Stages completed: {result.stages_completed}/{result.total_stages}")
    
    # Check aggregated data
    if result.context.aggregated_data:
        print("\n📊 Aggregated data keys:")
        for key, data in result.context.aggregated_data.items():
            print(f"  - {key}: {len(data)} records")
            if data and len(data) > 0:
                print(f"    Sample: {data[0]}")
    
    # Check stage results
    if 'report' in result.context.stage_results:
        report_result = result.context.stage_results['report']
        print(f"\n📄 Report stage status: {report_result.status}")
        if report_result.error:
            print(f"Report error: {report_result.error}")

if __name__ == "__main__":
    debug_report_generation()
