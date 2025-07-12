"""Whoop data extractor for converting raw API responses to structured records.

This extractor handles the conversion of raw Whoop API responses into
structured data records using the new data models.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional

from .base_extractor import BaseExtractor
from src.models import (
    WorkoutRecord, 
    RecoveryRecord, 
    SleepRecord,
    ActivityRecord,
    DataSource, 
    SportType, 
    RecoveryLevel
)
from src.app_config import AppConfig
from src.utils.date_utils import DateUtils


class WhoopExtractor(BaseExtractor):
    """Extractor for Whoop API responses.
    
    Converts raw Whoop API responses into structured data records
    using configuration for sport ID mappings.
    """
    
    def __init__(self):
        """Initialize the Whoop extractor."""
        super().__init__(DataSource.WHOOP)
    
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract all data types from raw Whoop API response.
        
        This is pure extraction - converts raw API data to basic data models
        without any transformation, cleaning, or persistence.
        
        Args:
            raw_data: Raw API response data containing workouts, recovery, sleep, cycles
            
        Returns:
            Dictionary with keys 'workouts', 'recovery', 'sleep', 'cycles' and lists of raw records
        """
        extracted = {
            'workouts': [],
            'recovery': [],
            'sleep': [],
            'cycles': []
        }
        
        if 'workouts' in raw_data:
            extracted['workouts'] = self.extract_workouts(raw_data['workouts'])
            self.logger.info(f"Extracted {len(extracted['workouts'])} raw workout records")
        
        if 'recovery' in raw_data:
            cycles_data = raw_data.get('cycles')  # Get cycles data for timestamp lookup
            extracted['recovery'] = self.extract_recovery(raw_data['recovery'], cycles_data)
            self.logger.info(f"Extracted {len(extracted['recovery'])} raw recovery records")
        
        if 'sleep' in raw_data:
            extracted['sleep'] = self.extract_sleep(raw_data['sleep'])
            self.logger.info(f"Extracted {len(extracted['sleep'])} raw sleep records")
        
        if 'cycles' in raw_data:
            extracted['activity'] = self.extract_cycles_as_activity(raw_data['cycles'])
            self.logger.info(f"Extracted {len(extracted['activity'])} activity records from cycles data")
        
        self.logger.info("Pure extraction completed - no transformation or persistence")
        return extracted
    
    def extract_workouts(self, raw_data: Dict[str, Any]) -> List[WorkoutRecord]:
        """Extract workout records from raw Whoop workout data.
        
        Args:
            raw_data: Raw workout API response
            
        Returns:
            List of WorkoutRecord instances
        """
        workouts = []
        raw_workouts = raw_data.get('records', [])  # Whoop API uses 'records' not 'data'
        
        for workout_data in raw_workouts:
            workout_record = self._extract_single_workout(workout_data)
            if workout_record:
                workouts.append(workout_record)
        

        return workouts
    
    def _extract_single_workout(self, workout_data: Dict[str, Any]) -> WorkoutRecord:
        """Extract a single workout record.
        
        Args:
            workout_data: Raw workout data from API
            
        Returns:
            WorkoutRecord instance or None if extraction fails
        """
        # Get sport information using configuration
        sport_id = workout_data.get('sport_id', 0)
        sport_info = AppConfig.get_whoop_sport_info(sport_id)
        
        # Parse timestamp
        start_time = DateUtils.parse_timestamp(workout_data.get('start'))
        if not start_time:
            self.logger.warning(f"Invalid start time in workout: {workout_data.get('start')}")
            return None
        
        # Calculate duration from start and end times
        end_time = DateUtils.parse_timestamp(workout_data.get('end'))
        if not end_time:
            self.logger.warning(f"Invalid end time in workout: {workout_data.get('end')}")
            return None
        
        duration_seconds = (end_time - start_time).total_seconds()
        duration_minutes = int(duration_seconds // 60) if duration_seconds > 0 else 0
        
        # Extract score data
        score_data = workout_data.get('score', {})
        strain_score = score_data.get('strain')
        kilojoules = score_data.get('kilojoule')
        
        # Convert kilojoules to calories (1 kJ = 0.239 calories)
        calories = int(kilojoules * 0.239) if kilojoules else None
        
        # Extract heart rate data
        average_heart_rate = score_data.get('average_heart_rate')
        max_heart_rate = score_data.get('max_heart_rate')
        
        # Extract heart rate zone durations (convert from seconds to minutes)
        zone_duration = score_data.get('zone_duration', {})
        zone_0_minutes = zone_duration.get('zone_zero_milli', 0) / 60000.0 if zone_duration else None
        zone_1_minutes = zone_duration.get('zone_one_milli', 0) / 60000.0 if zone_duration else None
        zone_2_minutes = zone_duration.get('zone_two_milli', 0) / 60000.0 if zone_duration else None
        zone_3_minutes = zone_duration.get('zone_three_milli', 0) / 60000.0 if zone_duration else None
        zone_4_minutes = zone_duration.get('zone_four_milli', 0) / 60000.0 if zone_duration else None
        zone_5_minutes = zone_duration.get('zone_five_milli', 0) / 60000.0 if zone_duration else None
        
        # Get sport name and determine type using config system
        sport_name = sport_info.get('name')
        sport_type = AppConfig.get_sport_type_from_name(sport_name)
        
        # Calculate date using Whoop-specific 4 AM cutoff rule
        final_date = self._normalize_whoop_date(start_time, "workout")
        
        # Create workout record
        workout = WorkoutRecord(
            timestamp=start_time,
            date=final_date,  # Apply Whoop-specific 4 AM cutoff rule
            source=DataSource.WHOOP,
            sport_type=sport_type,
            sport_name=sport_name,
            title=None,  # Whoop doesn't provide workout titles
            duration_minutes=duration_minutes,
            strain_score=strain_score,
            calories=calories,
            average_heart_rate=int(average_heart_rate) if average_heart_rate else None,
            max_heart_rate=int(max_heart_rate) if max_heart_rate else None,
            zone_0_minutes=zone_0_minutes,
            zone_1_minutes=zone_1_minutes,
            zone_2_minutes=zone_2_minutes,
            zone_3_minutes=zone_3_minutes,
            zone_4_minutes=zone_4_minutes,
            zone_5_minutes=zone_5_minutes
        )
        
        return workout
    
    def extract_recovery(self, raw_data: Dict[str, Any], cycles_data: Dict[str, Any] = None) -> List[RecoveryRecord]:
        """Extract recovery records from raw Whoop recovery data.
        
        Args:
            raw_data: Raw recovery API response
            cycles_data: Raw cycles API response for timestamp lookup
            
        Returns:
            List of RecoveryRecord instances
        """
        recovery_records = []
        raw_recovery = raw_data.get('records', [])  # Whoop API uses 'records' not 'data'
        
        for recovery_data in raw_recovery:
            recovery_record = self._extract_single_recovery(recovery_data, cycles_data)
            if recovery_record:
                recovery_records.append(recovery_record)
        

        return recovery_records
    
    def _extract_single_recovery(self, recovery_data: Dict[str, Any], cycles_data: Dict[str, Any] = None) -> RecoveryRecord:
        """Extract a single recovery record.
        
        Args:
            recovery_data: Raw recovery data from API
            cycles_data: Raw cycles data for timestamp lookup
            
        Returns:
            RecoveryRecord instance or None if extraction fails
        """
        # Parse date from cycle_id (format: YYYY-MM-DD or integer)
        cycle_id = recovery_data.get('cycle_id', '')
        if not cycle_id:
            self.logger.warning("Missing cycle_id in recovery data")
            return None
        
        # Convert cycle_id to string if it's an integer
        cycle_id_str = str(cycle_id)
        
        # Try parsing cycle_id as date first
        if len(cycle_id_str) == 10 and '-' in cycle_id_str:
            record_date = datetime.strptime(cycle_id_str, '%Y-%m-%d').date()
        else:
            # If cycle_id is not in date format, try to extract date from created_at
            created_at = recovery_data.get('created_at', '')
            if created_at:
                record_date = DateUtils.parse_timestamp(created_at).date()
            else:
                self.logger.warning(f"Invalid cycle_id format and no created_at: {cycle_id}")
                return None
        
        # Extract score data
        score_data = recovery_data.get('score', {})
        recovery_score = score_data.get('recovery_score')
        hrv_rmssd = score_data.get('hrv_rmssd_milli')
        resting_hr = score_data.get('resting_heart_rate')
        
        # Convert to integers if they exist
        if recovery_score is not None:
            recovery_score = int(recovery_score)
        if resting_hr is not None:
            resting_hr = int(resting_hr)
        
        # Convert HRV from milliseconds to standard units if needed
        if hrv_rmssd:
            hrv_rmssd = hrv_rmssd / 1000.0 if hrv_rmssd > 100 else hrv_rmssd
        
        # Look up timestamp from corresponding cycle record
        cycle_timestamp = None
        if cycles_data and cycle_id:
            cycle_records = cycles_data.get('records', []) if isinstance(cycles_data, dict) else []
            for cycle_record in cycle_records:
                if str(cycle_record.get('id', '')) == str(cycle_id):
                    cycle_timestamp = cycle_record.get('start')
                    break
        
        # Use cycle start timestamp only (no fallback)
        timestamp = cycle_timestamp
        
        # Calculate date using Whoop-specific 4 AM cutoff rule
        final_date = self._normalize_whoop_date(timestamp, "recovery")
        
        # Create recovery record
        recovery = RecoveryRecord(
            timestamp=timestamp,  # Use cycle start timestamp or fallback
            date=final_date,  # Apply Whoop-specific 4 AM cutoff rule
            source=DataSource.WHOOP,
            recovery_score=recovery_score,  # Map directly from API
            hrv_rmssd=hrv_rmssd,
            resting_hr=resting_hr
        )
        
        return recovery
    
    def extract_sleep(self, raw_data: Dict[str, Any]) -> List[SleepRecord]:
        """Extract sleep records from raw Whoop sleep data.
        
        Args:
            raw_data: Raw sleep API response
            
        Returns:
            List of SleepRecord instances
        """
        sleep_records = []
        raw_sleep = raw_data.get('records', [])  # Whoop API uses 'records' not 'data'
        
        for sleep_data in raw_sleep:
            sleep_record = self._extract_single_sleep(sleep_data)
            if sleep_record:
                sleep_records.append(sleep_record)
        

        return sleep_records
    
    def _extract_single_sleep(self, sleep_data: Dict[str, Any]) -> SleepRecord:
        """Extract a single sleep record.
        
        Args:
            sleep_data: Raw sleep data from API
            
        Returns:
            SleepRecord instance or None if extraction fails
        """
        # Parse date from start time
        start_time = DateUtils.parse_timestamp(sleep_data.get('start'))
        if not start_time:
            self.logger.warning("Invalid start time in sleep data")
            return None
        
        # Extract score data
        score_data = sleep_data.get('score', {})
        sleep_score = score_data.get('sleep_performance_percentage')
        
        # Extract sleep stages from nested stage_summary (convert from milliseconds to minutes)
        stage_summary = score_data.get('stage_summary', {})
        
        light_sleep_ms = stage_summary.get('total_light_sleep_time_milli')
        light_sleep_minutes = light_sleep_ms // 60000 if light_sleep_ms else None
        
        deep_sleep_ms = stage_summary.get('total_slow_wave_sleep_time_milli')
        deep_sleep_minutes = deep_sleep_ms // 60000 if deep_sleep_ms else None
        
        rem_sleep_ms = stage_summary.get('total_rem_sleep_time_milli')
        rem_sleep_minutes = rem_sleep_ms // 60000 if rem_sleep_ms else None
        
        # Calculate total sleep time from sleep stages
        total_sleep_minutes = None
        if light_sleep_minutes is not None and deep_sleep_minutes is not None and rem_sleep_minutes is not None:
            total_sleep_minutes = light_sleep_minutes + deep_sleep_minutes + rem_sleep_minutes
        
        # Extract time in bed from stage_summary (convert from milliseconds to minutes)
        time_in_bed_ms = stage_summary.get('total_in_bed_time_milli')
        time_in_bed_minutes = time_in_bed_ms // 60000 if time_in_bed_ms else None
        
        # Extract awake time from stage_summary (convert from milliseconds to minutes)
        awake_time_ms = stage_summary.get('total_awake_time_milli')
        awake_minutes = awake_time_ms // 60000 if awake_time_ms else None
        
        # Calculate sleep need from nested sleep_needed components (convert from milliseconds to minutes)
        sleep_needed = score_data.get('sleep_needed', {})
        sleep_need_minutes = None
        
        baseline_ms = sleep_needed.get('baseline_milli')
        need_from_debt_ms = sleep_needed.get('need_from_sleep_debt_milli')
        need_from_strain_ms = sleep_needed.get('need_from_recent_strain_milli')
        need_from_nap_ms = sleep_needed.get('need_from_recent_nap_milli')
        
        if baseline_ms is not None:
            sleep_need_minutes = baseline_ms // 60000
            if need_from_debt_ms:
                sleep_need_minutes += need_from_debt_ms // 60000
            if need_from_strain_ms:
                sleep_need_minutes += need_from_strain_ms // 60000
            if need_from_nap_ms:
                sleep_need_minutes += need_from_nap_ms // 60000
        
        # Parse bedtime and wake time
        bedtime = DateUtils.parse_timestamp(sleep_data.get('start'))
        wake_time = DateUtils.parse_timestamp(sleep_data.get('end'))
        
        # Get nap field directly from Whoop API data
        is_nap = sleep_data.get('nap')
        
        # Calculate date using Whoop-specific 4 AM cutoff rule
        sleep_timestamp = sleep_data.get('start')
        final_date = self._normalize_whoop_date(sleep_timestamp, "sleep")
        
        # Create sleep record
        sleep_record = SleepRecord(
            timestamp=sleep_timestamp,  # Use start time for sleep timestamp
            date=final_date,  # Apply Whoop-specific 4 AM cutoff rule
            source=DataSource.WHOOP,
            total_sleep_minutes=total_sleep_minutes,
            time_in_bed_minutes=time_in_bed_minutes,
            light_sleep_minutes=light_sleep_minutes,
            deep_sleep_minutes=deep_sleep_minutes,
            rem_sleep_minutes=rem_sleep_minutes,
            awake_minutes=awake_minutes,
            sleep_score=int(sleep_score) if sleep_score else None,
            sleep_need_minutes=sleep_need_minutes,
            bedtime=bedtime,
            wake_time=wake_time,
            nap=is_nap
        )
        
        return sleep_record
    
    def _normalize_whoop_date(self, timestamp: str, data_type: str = "data") -> Optional[date]:
        """Apply Whoop-specific 4 AM cutoff rule to normalize dates.
        
        Whoop uses a 4 AM cutoff where data recorded before 4 AM is counted
        for the previous day. This applies to workouts, recovery, and sleep data.
        
        Args:
            timestamp: ISO timestamp string
            data_type: Type of data for logging (e.g., "workout", "recovery", "sleep")
            
        Returns:
            Normalized date or None if parsing fails
        """
        if not timestamp:
            return None
            
        from src.utils.date_utils import DateUtils
        # Parse timestamp and apply Whoop 4 AM cutoff rule
        parsed_datetime = DateUtils.parse_timestamp(timestamp, to_local=True)
        if parsed_datetime:
            normalized_datetime = DateUtils.normalize_recovery_date(parsed_datetime)
            return normalized_datetime.date()
        
        return None
    
    def extract_cycles_as_activity(self, cycles_data: Dict[str, Any]) -> List[ActivityRecord]:
        """Extract cycles data as activity records (daily activity summaries).
        
        Args:
            cycles_data: Raw cycles data from API
            
        Returns:
            List of ActivityRecord instances
        """
        records = []
        
        # Handle both dict format with 'records' key and direct list format
        cycle_records = cycles_data.get('records', []) if isinstance(cycles_data, dict) else cycles_data
        
        for cycle in cycle_records:
            if not isinstance(cycle, dict):
                continue
                
            # Extract basic cycle information
            cycle_id = cycle.get('id', '')
            if not cycle_id:
                continue
            
            # Convert to string for consistent handling
            cycle_id = str(cycle_id)
            
            # Parse date from cycle data
            start_time = cycle.get('start', '')
            if start_time:
                record_date = DateUtils.parse_timestamp(start_time).date()
            else:
                # Fallback to cycle_id if it's in date format
                try:
                    record_date = datetime.strptime(cycle_id[:10], '%Y-%m-%d').date()
                except (ValueError, IndexError):
                    self.logger.warning(f"Could not parse date from cycle {cycle_id}")
                    continue
            
            # Extract activity metrics from cycle data
            # Whoop cycles contain strain and activity data
            score_data = cycle.get('score', {})
            
            # Convert kilojoules to calories (1 kJ = 0.239006 calories)
            kilojoules = score_data.get('kilojoule', 0)
            total_calories = int(kilojoules * 0.239006) if kilojoules else None
            
            # Create activity record
            record = ActivityRecord(
                timestamp=start_time,
                date=record_date,
                source=DataSource.WHOOP,
                steps=None,  # Whoop doesn't track steps
                active_calories=None,  # Not available in cycles data
                total_calories=total_calories  # Converted from kilojoules
            )
            
            records.append(record)
            
        return records
