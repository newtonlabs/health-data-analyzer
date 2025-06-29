#!/usr/bin/env python3
"""Test the shim conversion directly."""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline.legacy_shim import MemoryBasedLegacyShim
from src.models.aggregations import TrainingMetricsRecord
from src.models.enums import SportType

def test_shim_conversion():
    """Test the shim conversion directly."""
    
    # Create sample training data
    sample_data = {
        'training': [
            TrainingMetricsRecord(
                date=datetime.now().date(),
                day='Fri',
                sport=SportType.WALKING,
                duration=30,
                workout_count=1
            ),
            TrainingMetricsRecord(
                date=datetime.now().date(),
                day='Fri', 
                sport=SportType.STRENGTH_TRAINING,
                duration=45,
                workout_count=1
            )
        ]
    }
    
    # Create shim
    shim = MemoryBasedLegacyShim(sample_data)
    
    # Test training metrics conversion
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    print("🔍 Testing training metrics conversion...")
    print(f"Sample training data workout_count values: {[r.workout_count for r in sample_data['training']]}")
    try:
        df = shim.training_metrics(start_date, end_date)
        print(f"✅ Conversion successful! Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        if not df.empty:
            print("Sample data:")
            print(df.head())
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_shim_conversion()
