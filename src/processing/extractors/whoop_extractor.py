"""Whoop data extractor for converting raw API responses to structured records.

This extractor handles the conversion of raw Whoop API responses into
structured data records using the new data models.
"""

from datetime import datetime, date
from typing import Dict, Any, List

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
            raw_data: Raw API response data containing workouts, recovery, sleep
            
        Returns:
            Dictionary with keys 'workouts', 'recovery', 'sleep' and lists of raw records
        """
        extracted = {
            'workouts': [],
            'recovery': [],
            'sleep': []
        }
        
        # Extract workouts (pure conversion, no transformation)
        if 'workouts' in raw_data:
            extracted['workouts'] = self.extract_workouts(raw_data['workouts'])
            self.logger.info(f"Extracted {len(extracted['workouts'])} raw workout records")
        
        # Extract recovery (pure conversion, no transformation)
        if 'recovery' in raw_data:
            extracted['recovery'] = self.extract_recovery(raw_data['recovery'])
            self.logger.info(f"Extracted {len(extracted['recovery'])} raw recovery records")
        
        # Extract sleep (pure conversion, no transformation)
        if 'sleep' in raw_data:
            extracted['sleep'] = self.extract_sleep(raw_data['sleep'])
            self.logger.info(f"Extracted {len(extracted['sleep'])} raw sleep records")
        
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
            try:
                workout_record = self._extract_single_workout(workout_data)
                if workout_record:
                    workouts.append(workout_record)
            except Exception as e:
                self.logger.warning(f"Failed to extract workout: {e}")
                continue
        
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
        
        # Extract duration
        duration_seconds = self.safe_get(workout_data, 'duration_seconds', 0, int)
        duration_minutes = duration_seconds // 60 if duration_seconds else 0
        
        # Extract score data
        score_data = self.safe_get(workout_data, 'score', {}, dict)
        strain_score = self.safe_get(score_data, 'strain', None, (int, float))
        kilojoules = self.safe_get(score_data, 'kilojoule', None, (int, float))
        
        # Convert kilojoules to calories (1 kJ = 0.239 calories)
        calories = int(kilojoules * 0.239) if kilojoules else None
        
        # Create workout record
        workout = WorkoutRecord(
            timestamp=start_time,
            source=DataSource.WHOOP,
            sport=SportType(sport_info['sport_type']),
            duration_minutes=duration_minutes,
            strain_score=strain_score,
            calories=calories
        )
        
        return workout
    
    def extract_recovery(self, raw_data: Dict[str, Any]) -> List[RecoveryRecord]:
        """Extract recovery records from raw Whoop recovery data.
        
        Args:
            raw_data: Raw recovery API response
            
        Returns:
            List of RecoveryRecord instances
        """
        recovery_records = []
        raw_recovery = raw_data.get('records', [])  # Whoop API uses 'records' not 'data'
        
        for recovery_data in raw_recovery:
            try:
                recovery_record = self._extract_single_recovery(recovery_data)
                if recovery_record:
                    recovery_records.append(recovery_record)
            except Exception as e:
                self.logger.warning(f"Failed to extract recovery: {e}")
                continue
        
        self.log_extraction_stats('recovery', len(recovery_records), len(raw_recovery))
        return recovery_records
    
    def _extract_single_recovery(self, recovery_data: Dict[str, Any]) -> RecoveryRecord:
        """Extract a single recovery record.
        
        Args:
            recovery_data: Raw recovery data from API
            
        Returns:
            RecoveryRecord instance or None if extraction fails
        """
        # Parse date from cycle_id (format: YYYY-MM-DD)
        cycle_id = self.safe_get(recovery_data, 'cycle_id', '', str)
        if not cycle_id:
            self.logger.warning("Missing cycle_id in recovery data")
            return None
        
        try:
            record_date = datetime.strptime(cycle_id, '%Y-%m-%d').date()
        except ValueError:
            self.logger.warning(f"Invalid cycle_id format: {cycle_id}")
            return None
        
        # Extract score data
        score_data = self.safe_get(recovery_data, 'score', {}, dict)
        recovery_score = self.safe_get(score_data, 'recovery_score', None, int)
        hrv_rmssd = self.safe_get(score_data, 'hrv_rmssd_milli', None, (int, float))
        resting_hr = self.safe_get(score_data, 'resting_heart_rate', None, int)
        
        # Convert HRV from milliseconds to standard units if needed
        if hrv_rmssd:
            hrv_rmssd = hrv_rmssd / 1000.0 if hrv_rmssd > 100 else hrv_rmssd
        
        # Determine recovery level using configuration
        recovery_level = None
        if recovery_score:
            level_str = self.config.get_recovery_level(recovery_score)
            recovery_level = RecoveryLevel(level_str)
        
        # Create recovery record
        recovery = RecoveryRecord(
            date=record_date,
            source=DataSource.WHOOP,
            recovery_score=recovery_score,
            recovery_level=recovery_level,
            hrv_rmssd=hrv_rmssd,
            resting_hr=resting_hr,
            raw_data=recovery_data
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
            try:
                sleep_record = self._extract_single_sleep(sleep_data)
                if sleep_record:
                    sleep_records.append(sleep_record)
            except Exception as e:
                self.logger.warning(f"Failed to extract sleep: {e}")
                continue
        
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
        
        record_date = start_time.date()
        
        # Extract score data
        score_data = self.safe_get(sleep_data, 'score', {}, dict)
        sleep_score = self.safe_get(score_data, 'sleep_performance_percentage', None, (int, float))
        
        # Extract duration data (convert from milliseconds to minutes)
        total_sleep_ms = self.safe_get(sleep_data, 'total_sleep_time_milli', None, int)
        total_sleep_minutes = total_sleep_ms // 60000 if total_sleep_ms else None
        
        time_in_bed_ms = self.safe_get(sleep_data, 'time_in_bed_milli', None, int)
        time_in_bed_minutes = time_in_bed_ms // 60000 if time_in_bed_ms else None
        
        # Calculate sleep efficiency
        sleep_efficiency = None
        if total_sleep_minutes and time_in_bed_minutes and time_in_bed_minutes > 0:
            sleep_efficiency = (total_sleep_minutes / time_in_bed_minutes) * 100
        
        # Extract sleep stages (convert from milliseconds to minutes)
        light_sleep_ms = self.safe_get(sleep_data, 'light_sleep_time_milli', None, int)
        light_sleep_minutes = light_sleep_ms // 60000 if light_sleep_ms else None
        
        deep_sleep_ms = self.safe_get(sleep_data, 'slow_wave_sleep_time_milli', None, int)
        deep_sleep_minutes = deep_sleep_ms // 60000 if deep_sleep_ms else None
        
        rem_sleep_ms = self.safe_get(sleep_data, 'rem_sleep_time_milli', None, int)
        rem_sleep_minutes = rem_sleep_ms // 60000 if rem_sleep_ms else None
        
        wake_time_ms = self.safe_get(sleep_data, 'wake_time_milli', None, int)
        awake_minutes = wake_time_ms // 60000 if wake_time_ms else None
        
        # Parse bedtime and wake time
        bedtime = self.parse_timestamp(sleep_data.get('start'))
        wake_time = self.parse_timestamp(sleep_data.get('end'))
        
        # Create sleep record
        sleep_record = SleepRecord(
            date=record_date,
            source=DataSource.WHOOP,
            total_sleep_minutes=total_sleep_minutes,
            time_in_bed_minutes=time_in_bed_minutes,
            sleep_efficiency=sleep_efficiency,
            light_sleep_minutes=light_sleep_minutes,
            deep_sleep_minutes=deep_sleep_minutes,
            rem_sleep_minutes=rem_sleep_minutes,
            awake_minutes=awake_minutes,
            sleep_score=int(sleep_score) if sleep_score else None,
            bedtime=bedtime,
            wake_time=wake_time,
            raw_data=sleep_data
        )
        
        return sleep_record
