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
    DataSource, 
    SportType, 
    RecoveryLevel
)
from src.config import default_config


class WhoopExtractor(BaseExtractor):
    """Extractor for Whoop API responses.
    
    Converts raw Whoop API responses into structured data records
    using configuration for sport ID mappings.
    """
    
    def __init__(self):
        """Initialize the Whoop extractor."""
        super().__init__(DataSource.WHOOP)
        self.config = default_config
    
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
        
        # Extract workouts (pure conversion, no transformation)
        if 'workouts' in raw_data:
            extracted['workouts'] = self.extract_workouts(raw_data['workouts'])
            self.logger.info(f"Extracted {len(extracted['workouts'])} raw workout records")
        
        # Extract recovery (pure conversion, no transformation)
        if 'recovery' in raw_data:
            cycles_data = raw_data.get('cycles')  # Get cycles data for timestamp lookup
            extracted['recovery'] = self.extract_recovery(raw_data['recovery'], cycles_data)
            self.logger.info(f"Extracted {len(extracted['recovery'])} raw recovery records")
        
        # Extract sleep (pure conversion, no transformation)
        if 'sleep' in raw_data:
            extracted['sleep'] = self.extract_sleep(raw_data['sleep'])
            self.logger.info(f"Extracted {len(extracted['sleep'])} raw sleep records")
        
        # Extract cycles (raw data for research - no processing)
        if 'cycles' in raw_data:
            extracted['cycles'] = raw_data['cycles']  # Store raw cycle data as-is
            cycle_count = len(raw_data['cycles'].get('records', [])) if isinstance(raw_data['cycles'], dict) else len(raw_data['cycles'])
            self.logger.info(f"Extracted {cycle_count} raw cycle records for research")
        
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
        
        self.log_extraction_stats('workouts', len(workouts), len(raw_workouts))
        return workouts
    
    def _extract_single_workout(self, workout_data: Dict[str, Any]) -> WorkoutRecord:
        """Extract a single workout record.
        
        Args:
            workout_data: Raw workout data from API
            
        Returns:
            WorkoutRecord instance or None if extraction fails
        """
        # Get sport information using configuration
        sport_id = self.safe_get(workout_data, 'sport_id', 0, int)
        sport_info = self.config.get_whoop_sport_info(sport_id)
        
        # Parse timestamp
        start_time = self.parse_timestamp(workout_data.get('start'))
        if not start_time:
            self.logger.warning(f"Invalid start time in workout: {workout_data.get('start')}")
            return None
        
        # Calculate duration from start and end times
        end_time = self.parse_timestamp(workout_data.get('end'))
        if not end_time:
            self.logger.warning(f"Invalid end time in workout: {workout_data.get('end')}")
            return None
        
        duration_seconds = (end_time - start_time).total_seconds()
        duration_minutes = int(duration_seconds // 60) if duration_seconds > 0 else 0
        
        # Extract score data
        score_data = self.safe_get(workout_data, 'score', {}, dict)
        strain_score = self.safe_get(score_data, 'strain', None, (int, float))
        kilojoules = self.safe_get(score_data, 'kilojoule', None, (int, float))
        
        # Convert kilojoules to calories (1 kJ = 0.239 calories)
        calories = int(kilojoules * 0.239) if kilojoules else None
        
        # Extract heart rate data
        average_heart_rate = self.safe_get(score_data, 'average_heart_rate', None, (int, float))
        max_heart_rate = self.safe_get(score_data, 'max_heart_rate', None, (int, float))
        
        # Extract heart rate zone durations (convert from seconds to minutes)
        zone_duration = self.safe_get(score_data, 'zone_duration', {}, dict)
        zone_0_minutes = self.safe_get(zone_duration, 'zone_zero_milli', 0, int) / 60000.0 if zone_duration else None
        zone_1_minutes = self.safe_get(zone_duration, 'zone_one_milli', 0, int) / 60000.0 if zone_duration else None
        zone_2_minutes = self.safe_get(zone_duration, 'zone_two_milli', 0, int) / 60000.0 if zone_duration else None
        zone_3_minutes = self.safe_get(zone_duration, 'zone_three_milli', 0, int) / 60000.0 if zone_duration else None
        zone_4_minutes = self.safe_get(zone_duration, 'zone_four_milli', 0, int) / 60000.0 if zone_duration else None
        zone_5_minutes = self.safe_get(zone_duration, 'zone_five_milli', 0, int) / 60000.0 if zone_duration else None
        
        # Get sport name and determine type using config system
        sport_name = sport_info.get('name')
        sport_type = self.config.get_sport_type_from_name(sport_name)
        
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
        
        self.log_extraction_stats('recovery', len(recovery_records), len(raw_recovery))
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
        cycle_id = self.safe_get(recovery_data, 'cycle_id', '', (str, int))
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
            created_at = self.safe_get(recovery_data, 'created_at', '', str)
            if created_at:
                record_date = self.parse_timestamp(created_at).date()
            else:
                self.logger.warning(f"Invalid cycle_id format and no created_at: {cycle_id}")
                return None
        
        # Extract score data
        score_data = self.safe_get(recovery_data, 'score', {}, dict)
        recovery_score = self.safe_get(score_data, 'recovery_score', None, (int, float))
        hrv_rmssd = self.safe_get(score_data, 'hrv_rmssd_milli', None, (int, float))
        resting_hr = self.safe_get(score_data, 'resting_heart_rate', None, (int, float))
        
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
                    cycle_timestamp = self.safe_get(cycle_record, 'start', None, str)
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
        
        self.log_extraction_stats('sleep', len(sleep_records), len(raw_sleep))
        return sleep_records
    
    def _extract_single_sleep(self, sleep_data: Dict[str, Any]) -> SleepRecord:
        """Extract a single sleep record.
        
        Args:
            sleep_data: Raw sleep data from API
            
        Returns:
            SleepRecord instance or None if extraction fails
        """
        # Parse date from start time
        start_time = self.parse_timestamp(sleep_data.get('start'))
        if not start_time:
            self.logger.warning("Invalid start time in sleep data")
            return None
        
        # Extract score data
        score_data = self.safe_get(sleep_data, 'score', {}, dict)
        sleep_score = self.safe_get(score_data, 'sleep_performance_percentage', None, (int, float))
        
        # Extract sleep stages from nested stage_summary (convert from milliseconds to minutes)
        stage_summary = self.safe_get(score_data, 'stage_summary', {}, dict)
        
        light_sleep_ms = self.safe_get(stage_summary, 'total_light_sleep_time_milli', None, int)
        light_sleep_minutes = light_sleep_ms // 60000 if light_sleep_ms else None
        
        deep_sleep_ms = self.safe_get(stage_summary, 'total_slow_wave_sleep_time_milli', None, int)
        deep_sleep_minutes = deep_sleep_ms // 60000 if deep_sleep_ms else None
        
        rem_sleep_ms = self.safe_get(stage_summary, 'total_rem_sleep_time_milli', None, int)
        rem_sleep_minutes = rem_sleep_ms // 60000 if rem_sleep_ms else None
        
        # Calculate total sleep time from sleep stages
        total_sleep_minutes = None
        if light_sleep_minutes is not None and deep_sleep_minutes is not None and rem_sleep_minutes is not None:
            total_sleep_minutes = light_sleep_minutes + deep_sleep_minutes + rem_sleep_minutes
        
        # Extract time in bed from stage_summary (convert from milliseconds to minutes)
        time_in_bed_ms = self.safe_get(stage_summary, 'total_in_bed_time_milli', None, int)
        time_in_bed_minutes = time_in_bed_ms // 60000 if time_in_bed_ms else None
        
        # Extract awake time from stage_summary (convert from milliseconds to minutes)
        awake_time_ms = self.safe_get(stage_summary, 'total_awake_time_milli', None, int)
        awake_minutes = awake_time_ms // 60000 if awake_time_ms else None
        
        # Calculate sleep need from nested sleep_needed components (convert from milliseconds to minutes)
        sleep_needed = self.safe_get(score_data, 'sleep_needed', {}, dict)
        sleep_need_minutes = None
        
        baseline_ms = self.safe_get(sleep_needed, 'baseline_milli', None, int)
        need_from_debt_ms = self.safe_get(sleep_needed, 'need_from_sleep_debt_milli', None, int)
        need_from_strain_ms = self.safe_get(sleep_needed, 'need_from_recent_strain_milli', None, int)
        need_from_nap_ms = self.safe_get(sleep_needed, 'need_from_recent_nap_milli', None, int)
        
        if baseline_ms is not None:
            sleep_need_minutes = baseline_ms // 60000
            if need_from_debt_ms:
                sleep_need_minutes += need_from_debt_ms // 60000
            if need_from_strain_ms:
                sleep_need_minutes += need_from_strain_ms // 60000
            if need_from_nap_ms:
                sleep_need_minutes += need_from_nap_ms // 60000
        
        # Parse bedtime and wake time
        bedtime = self.parse_timestamp(sleep_data.get('start'))
        wake_time = self.parse_timestamp(sleep_data.get('end'))
        
        # Get nap field directly from Whoop API data
        is_nap = self.safe_get(sleep_data, 'nap', None, bool)
        
        # Calculate date using Whoop-specific 4 AM cutoff rule
        sleep_timestamp = self.safe_get(sleep_data, 'start', None, str)
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
