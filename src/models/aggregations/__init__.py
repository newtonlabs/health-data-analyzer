"""Aggregation models for specialized health data analysis.

These models combine data from multiple sources (Whoop, Oura, Withings, etc.)
into purpose-built structures for specific use cases like reporting, analysis,
and dashboard generation.
"""

from .macros_and_activity import MacrosAndActivityRecord
from .recovery_metrics import RecoveryMetricsRecord  
from .training_metrics import TrainingMetricsRecord

__all__ = [
    "MacrosAndActivityRecord",
    "RecoveryMetricsRecord", 
    "TrainingMetricsRecord",
]
