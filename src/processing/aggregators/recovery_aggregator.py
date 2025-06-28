"""Recovery aggregator for combining recovery, sleep, and resilience data."""

from datetime import date
from typing import List, Optional

from src.models.raw_data import RecoveryRecord, SleepRecord, ResilienceRecord
from src.models.aggregations import RecoveryMetricsRecord


class RecoveryAggregator:
    """Aggregator for combining recovery, sleep, and resilience data into daily summaries."""
    
    def aggregate_daily_recovery(
        self,
        target_date: date,
        recovery_records: List[RecoveryRecord],
        sleep_records: List[SleepRecord],
        resilience_records: List[ResilienceRecord]
    ) -> RecoveryMetricsRecord:
        """Aggregate daily recovery, sleep, and resilience data.
        
        Args:
            target_date: Date to aggregate data for
            recovery_records: Recovery data for the date
            sleep_records: Sleep data for the date
            resilience_records: Resilience data for the date
            
        Returns:
            Aggregated daily recovery metrics record
        """
        # Find records for target date
        recovery = self._find_recovery_for_date(recovery_records, target_date)
        sleep = self._find_sleep_for_date(sleep_records, target_date)
        resilience = self._find_resilience_for_date(resilience_records, target_date)
        
        return RecoveryMetricsRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            # Recovery metrics (from Whoop)
            recovery=float(recovery.recovery_score) if recovery and recovery.recovery_score else None,
            hrv=recovery.hrv_rmssd if recovery else None,
            rhr=recovery.resting_hr if recovery else None,
            # Sleep metrics (from Whoop)
            sleep_need=sleep.sleep_need_minutes if sleep else None,
            sleep_actual=sleep.total_sleep_minutes if sleep else None,
            # Resilience metrics
            resilience_level=resilience.level if resilience else None,
        )
    
    def _find_recovery_for_date(self, records: List[RecoveryRecord], target_date: date) -> Optional[RecoveryRecord]:
        """Find recovery record for specific date."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    def _find_sleep_for_date(self, records: List[SleepRecord], target_date: date) -> Optional[SleepRecord]:
        """Find sleep record for specific date."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    def _find_resilience_for_date(self, records: List[ResilienceRecord], target_date: date) -> Optional[ResilienceRecord]:
        """Find resilience record for specific date."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    # Business logic methods (moved from model)
    @staticmethod
    def calculate_sleep_debt(sleep_need: int, sleep_actual: int) -> int:
        """Calculate sleep debt in minutes (positive = debt, negative = surplus)."""
        return sleep_need - sleep_actual
    
    @staticmethod
    def calculate_sleep_efficiency(sleep_need: int, sleep_actual: int) -> float:
        """Calculate sleep efficiency as percentage of need met."""
        return round((sleep_actual / sleep_need) * 100, 1)
    
    @staticmethod
    def categorize_recovery(recovery_score: float) -> str:
        """Categorize recovery score into meaningful ranges."""
        if recovery_score >= 70:
            return "high"
        elif recovery_score >= 50:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    def categorize_hrv(hrv: float) -> str:
        """Categorize HRV relative to typical ranges (rough estimates)."""
        # These are rough categories - ideally would be personalized
        if hrv >= 50:
            return "high"
        elif hrv >= 30:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    def calculate_recovery_consistency_score(recovery: float, hrv: float, hr: int) -> float:
        """Calculate a composite recovery consistency score (0-100)."""
        # Normalize each metric to 0-100 scale (rough approximation)
        recovery_norm = recovery  # Already 0-100
        hrv_norm = min(100, (hrv / 60) * 100)  # Assume 60ms is "perfect"
        hr_norm = max(0, 100 - ((hr - 50) * 2))  # Lower HR is better
        
        # Weighted average (recovery is most important)
        composite = (recovery_norm * 0.5) + (hrv_norm * 0.3) + (hr_norm * 0.2)
        return round(composite, 1)
    
    @staticmethod
    def assess_sleep_quality(sleep_debt: int) -> str:
        """Overall sleep quality assessment."""
        if sleep_debt <= -30:  # 30+ min surplus
            return "excellent"
        elif sleep_debt <= 0:  # Met or slightly exceeded need
            return "good"
        elif sleep_debt <= 60:  # Up to 1 hour debt
            return "fair"
        else:  # More than 1 hour debt
            return "poor"
