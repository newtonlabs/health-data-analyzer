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
        """Find sleep record for specific date, ignoring naps."""
        for record in records:
            if record.date == target_date and not record.nap:
                return record
        return None
    
    def _find_resilience_for_date(self, records: List[ResilienceRecord], target_date: date) -> Optional[ResilienceRecord]:
        """Find resilience record for specific date."""
        for record in records:
            if record.date == target_date:
                return record
        return None
    

