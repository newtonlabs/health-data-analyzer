#!/usr/bin/env python3
"""Test script for Oura resilience extractor."""

import json
from datetime import datetime, timedelta
from src.processing.extractors.oura_extractor import OuraExtractor

def main():
    """Test the resilience extractor with real API data."""
    print("🧠 TESTING OURA RESILIENCE EXTRACTOR")
    print("=" * 45)
    
    # Load the raw resilience data
    try:
        with open("data/01_raw/oura_resilience_raw_2025-06-26.json", 'r') as f:
            raw_data = json.load(f)
        
        print(f"📊 Loaded raw data with {len(raw_data.get('data', []))} records")
        
        # Initialize extractor
        extractor = OuraExtractor()
        
        # Set date range (7 days back)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Extract resilience records
        print("\n🔄 Extracting resilience records...")
        resilience_records = extractor.extract_resilience_data(raw_data, start_date, end_date)
        
        print(f"\n✅ Extraction complete!")
        print(f"   Records extracted: {len(resilience_records)}")
        
        if resilience_records:
            print("\n📋 Sample resilience record:")
            sample = resilience_records[0]
            print(f"   Timestamp: {sample.timestamp}")
            print(f"   Date: {sample.date}")
            print(f"   Source: {sample.source}")
            print(f"   Sleep Recovery: {sample.sleep_recovery}")
            print(f"   Daytime Recovery: {sample.daytime_recovery}")
            print(f"   Stress: {sample.stress}")
            print(f"   Level: {sample.level}")
            
            print(f"\n📊 All records:")
            for i, record in enumerate(resilience_records):
                print(f"   {i+1}. {record.timestamp} - Level: {record.level}, Sleep: {record.sleep_recovery}, Stress: {record.stress}")
        
    except FileNotFoundError:
        print("❌ Raw resilience data file not found. Run test_oura_api_responses.py first.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
