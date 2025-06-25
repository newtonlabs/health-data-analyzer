"""Data collection models for pipeline stages.

This module contains dataclass definitions for collections of data
used at different stages of the processing pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from .data_records import (
    WorkoutRecord,
    RecoveryRecord,
    SleepRecord,
    WeightRecord,
    NutritionRecord,
    ActivityRecord
)


@dataclass
class RawDataCollection:
    """Raw API responses from all data sources.
    
    This represents the unprocessed data directly from API calls
    before any extraction or transformation.
    """
    whoop_data: Dict[str, Any] = field(default_factory=dict)
    oura_data: Dict[str, Any] = field(default_factory=dict)
    withings_data: Dict[str, Any] = field(default_factory=dict)
    hevy_data: Dict[str, Any] = field(default_factory=dict)
    nutrition_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    fetch_timestamp: datetime = field(default_factory=datetime.now)
    date_range: Optional[tuple[date, date]] = None
    
    def is_empty(self) -> bool:
        """Check if all data sources are empty."""
        return not any([
            self.whoop_data,
            self.oura_data,
            self.withings_data,
            self.hevy_data,
            self.nutrition_data
        ])
    
    def get_source_count(self) -> int:
        """Get count of non-empty data sources."""
        return sum([
            bool(self.whoop_data),
            bool(self.oura_data),
            bool(self.withings_data),
            bool(self.hevy_data),
            bool(self.nutrition_data)
        ])


@dataclass
class ProcessedDataCollection:
    """Structured and normalized data records from all sources.
    
    This represents data that has been extracted from raw API responses
    and converted to structured records, but not yet aggregated.
    """
    workouts: List[WorkoutRecord] = field(default_factory=list)
    recovery: List[RecoveryRecord] = field(default_factory=list)
    sleep: List[SleepRecord] = field(default_factory=list)
    weight: List[WeightRecord] = field(default_factory=list)
    nutrition: List[NutritionRecord] = field(default_factory=list)
    activity: List[ActivityRecord] = field(default_factory=list)
    
    # Processing metadata
    processing_timestamp: datetime = field(default_factory=datetime.now)
    date_range: Optional[tuple[date, date]] = None
    
    def is_empty(self) -> bool:
        """Check if all record lists are empty."""
        return not any([
            self.workouts,
            self.recovery,
            self.sleep,
            self.weight,
            self.nutrition,
            self.activity
        ])
    
    def get_record_counts(self) -> Dict[str, int]:
        """Get count of records by type."""
        return {
            "workouts": len(self.workouts),
            "recovery": len(self.recovery),
            "sleep": len(self.sleep),
            "weight": len(self.weight),
            "nutrition": len(self.nutrition),
            "activity": len(self.activity)
        }
    
    def get_total_records(self) -> int:
        """Get total count of all records."""
        return sum(self.get_record_counts().values())
    
    def get_date_range(self) -> Optional[tuple[date, date]]:
        """Calculate actual date range from records."""
        all_dates = []
        
        # Collect dates from all record types
        for workout in self.workouts:
            all_dates.append(workout.timestamp.date())
        
        for record in self.recovery:
            all_dates.append(record.date)
        
        for record in self.sleep:
            all_dates.append(record.date)
        
        for weight in self.weight:
            all_dates.append(weight.timestamp.date())
        
        for record in self.nutrition:
            all_dates.append(record.date)
        
        for record in self.activity:
            all_dates.append(record.date)
        
        if not all_dates:
            return None
        
        return (min(all_dates), max(all_dates))


@dataclass
class AggregatedMetrics:
    """Calculated metrics and analysis results.
    
    This represents the final stage of processing where data has been
    aggregated, analyzed, and metrics calculated for reporting.
    """
    # Time period for metrics
    start_date: date
    end_date: date
    
    # Weekly summary statistics
    weekly_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Trend analysis
    trends: Dict[str, Any] = field(default_factory=dict)
    
    # Correlations between metrics
    correlations: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Recovery analysis
    recovery_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Nutrition analysis
    nutrition_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Training analysis
    training_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Aggregation metadata
    aggregation_timestamp: datetime = field(default_factory=datetime.now)
    data_quality_score: Optional[float] = None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get high-level summary of all metrics."""
        return {
            "period": f"{self.start_date} to {self.end_date}",
            "aggregation_time": self.aggregation_timestamp.isoformat(),
            "data_quality": self.data_quality_score,
            "has_weekly_stats": bool(self.weekly_stats),
            "has_trends": bool(self.trends),
            "has_correlations": bool(self.correlations),
            "has_performance": bool(self.performance_metrics),
            "has_recovery": bool(self.recovery_analysis),
            "has_nutrition": bool(self.nutrition_analysis),
            "has_training": bool(self.training_analysis)
        }


@dataclass
class PipelineResult:
    """Complete result of the data processing pipeline.
    
    This contains all stages of data processing for debugging,
    validation, and comprehensive analysis.
    """
    # All pipeline stages
    raw_data: RawDataCollection
    processed_data: ProcessedDataCollection
    aggregated_metrics: AggregatedMetrics
    
    # Pipeline execution metadata
    pipeline_start: datetime
    pipeline_end: datetime
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def execution_time_seconds(self) -> float:
        """Calculate pipeline execution time in seconds."""
        return (self.pipeline_end - self.pipeline_start).total_seconds()
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of pipeline execution."""
        return {
            "start_time": self.pipeline_start.isoformat(),
            "end_time": self.pipeline_end.isoformat(),
            "execution_time_seconds": self.execution_time_seconds,
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "raw_sources": self.raw_data.get_source_count(),
            "total_records": self.processed_data.get_total_records(),
            "data_quality": self.aggregated_metrics.data_quality_score
        }
