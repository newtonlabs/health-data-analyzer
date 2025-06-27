#!/usr/bin/env python3
"""Test script to examine Oura resilience and workout API responses."""

import json
from src.pipeline.clean_pipeline import CleanHealthPipeline

def main():
    """Run Oura pipeline and print API responses for analysis."""
    print("🔍 OURA API RESPONSE ANALYSIS")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = CleanHealthPipeline()
    
    # Run Oura pipeline (1 day to get recent data)
    print("🚀 Running Oura pipeline...")
    file_paths = pipeline.process_oura_data(days=7)  # 7 days for more data
    
    print("\n📁 FILES GENERATED:")
    for stage, path in file_paths.items():
        print(f"   {stage}: {path}")
    
    # Print resilience data if available
    if "01_raw_resilience" in file_paths:
        print("\n🧠 RESILIENCE API RESPONSE:")
        print("=" * 40)
        try:
            with open(file_paths["01_raw_resilience"], 'r') as f:
                resilience_data = json.load(f)
            
            print(f"📊 Total resilience records: {len(resilience_data.get('data', []))}")
            
            if resilience_data.get('data'):
                print("\n📋 Sample resilience record:")
                sample_record = resilience_data['data'][0]
                print(json.dumps(sample_record, indent=2))
                
                print("\n🔑 Available fields:")
                for key in sample_record.keys():
                    print(f"   - {key}")
            else:
                print("⚠️  No resilience records found")
                
        except Exception as e:
            print(f"❌ Error reading resilience data: {e}")
    
    # Print workout data if available
    if "01_raw_workouts" in file_paths:
        print("\n💪 WORKOUT API RESPONSE:")
        print("=" * 40)
        try:
            with open(file_paths["01_raw_workouts"], 'r') as f:
                workout_data = json.load(f)
            
            print(f"📊 Total workout records: {len(workout_data.get('data', []))}")
            
            if workout_data.get('data'):
                print("\n📋 Sample workout record:")
                sample_record = workout_data['data'][0]
                print(json.dumps(sample_record, indent=2))
                
                print("\n🔑 Available fields:")
                for key in sample_record.keys():
                    print(f"   - {key}")
            else:
                print("⚠️  No workout records found")
                
        except Exception as e:
            print(f"❌ Error reading workout data: {e}")
    
    print("\n🎯 ANALYSIS COMPLETE!")
    print("Review the API responses above to decide on data model structure.")

if __name__ == "__main__":
    main()
