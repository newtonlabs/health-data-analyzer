"""Processor for Whoop data.

This module provides functionality to process and analyze data from the Whoop API.
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple, List

from src.app_config import AppConfig
from src.utils.date_utils import DateUtils, DateFormat
from src.utils.logging_utils import HealthLogger


class WhoopProcessor:
    """Processor for Whoop data."""
    
    def __init__(self):
        """Initialize WhoopProcessor."""
        self.logger = HealthLogger(__name__)

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Extract and clean workout and recovery data from Whoop API response.

        Processes two types of data:
        1. Workouts: Exercise sessions with sport, duration, and strain
        2. Recovery: Daily recovery metrics including HRV and resting HR

        Args:
            raw_data: Raw Whoop API response containing workouts and recovery

        Returns:
            Dictionary with two DataFrames:
            - workouts: Exercise data with sport, duration, strain
            - recovery: Daily recovery metrics with HRV and HR
        """
        # Create empty DataFrames with correct columns
        workouts_df = pd.DataFrame(
            columns=["date", "sport_id", "sport", "duration", "strain"]
        )
        recovery_df = pd.DataFrame(
            columns=["date", "recovery_score", "hrv_rmssd", "resting_hr"]
        )

        # Return empty DataFrames if no data
        if not raw_data:
            self.logger.logger.debug("Invalid Whoop data structure")
            return {"workouts": workouts_df, "recovery": recovery_df}

        workout_data = []
        recovery_data = []
        
        # Process workouts
        if "workouts" in raw_data and "records" in raw_data["workouts"]:
            for workout in raw_data["workouts"]["records"]:
                transformed = self._transform_workout(workout)
                if transformed:
                    workout_data.append(transformed)
                    
        # Process recovery
        if "recovery" in raw_data and "records" in raw_data["recovery"]:
            self.logger.logger.debug(f"Processing {len(raw_data['recovery']['records'])} recovery records")
            for i, recovery in enumerate(raw_data["recovery"]["records"]):
                transformed = self._transform_recovery(recovery)
                if transformed:
                    self.logger.logger.debug(f"Recovery {i+1}: date type = {type(transformed['date'])}")
                    recovery_data.append(transformed)
                    
        # Add sleep data to recovery records
        if "sleep" in raw_data and "records" in raw_data["sleep"] and recovery_data:
            sleep_by_date = {}
            for sleep in raw_data["sleep"]["records"]:
                # Convert to local time and normalize date
                created = datetime.fromisoformat(
                    sleep["created_at"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                sleep_date = DateUtils.normalize_recovery_date(created)
                
                # Store sleep data by date
                # Calculate total sleep need in hours
                sleep_needed = sleep.get("score", {}).get("sleep_needed", {})
                total_need_milli = 0
                if sleep_needed:
                    total_need_milli = (
                        sleep_needed.get("baseline_milli", 0)
                        + sleep_needed.get("need_from_sleep_debt_milli", 0)
                        + sleep_needed.get("need_from_recent_strain_milli", 0)
                        - sleep_needed.get("need_from_recent_nap_milli", 0)
                    )
                    
                # Get actual sleep time in hours
                stage_summary = sleep.get("score", {}).get("stage_summary", {})
                total_sleep_milli = stage_summary.get(
                    "total_in_bed_time_milli", 0
                ) - stage_summary.get("total_awake_time_milli", 0)
                
                sleep_by_date[sleep_date.strftime("%Y-%m-%d")] = {
                    "sleep_need": total_need_milli
                    / (3600 * 1000),  # Convert milliseconds to hours
                    "sleep_actual": total_sleep_milli
                    / (3600 * 1000),  # Convert milliseconds to hours
                }
                
            # Add sleep data to recovery records
            for recovery in recovery_data:
                date_key = recovery["date"].strftime("%Y-%m-%d")
                if date_key in sleep_by_date:
                    recovery["sleep_need"] = sleep_by_date[date_key]["sleep_need"]
                    recovery["sleep_actual"] = sleep_by_date[date_key]["sleep_actual"]
                    
        # Create DataFrames if we have data
        if workout_data:
            workouts_df = pd.DataFrame(workout_data)
            # Debug logging
            self.logger.logger.debug(f"Workouts data before conversion: {workouts_df['date'].dtype if 'date' in workouts_df.columns else 'No date column'}")
            # Ensure date column is datetime for compatibility with metrics_aggregator
            if "date" in workouts_df.columns and not pd.api.types.is_datetime64_any_dtype(workouts_df["date"]):
                workouts_df["date"] = pd.to_datetime(workouts_df["date"])
                self.logger.logger.debug(f"Workouts data after conversion: {workouts_df['date'].dtype}")
            
        if recovery_data:
            recovery_df = pd.DataFrame(recovery_data)
            # Debug logging
            self.logger.logger.debug(f"Recovery data before conversion: {recovery_df['date'].dtype if 'date' in recovery_df.columns else 'No date column'}")
            # Ensure date column is datetime for compatibility with metrics_aggregator
            if "date" in recovery_df.columns and not pd.api.types.is_datetime64_any_dtype(recovery_df["date"]):
                recovery_df["date"] = pd.to_datetime(recovery_df["date"])
                self.logger.logger.debug(f"Recovery data after conversion: {recovery_df['date'].dtype}")
            
        return {"workouts": workouts_df, "recovery": recovery_df}
    
    def _transform_workout(self, workout: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform raw workout data.
        
        Args:
            workout: Raw workout data
            
        Returns:
            Transformed workout data
        """
        try:
            # Extract sport ID and get name
            sport_id = workout.get("sport_id", 0)
            sport_name = AppConfig.get_whoop_sport_name(sport_id)
            
            # Skip if no sport name or missing required data
            if not sport_name or "score" not in workout:
                return None
                
            # Get start time in local timezone
            start_time_str = workout.get("start")
            if not start_time_str:
                return None
                
            # Parse start time
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            
            # Convert to local time
            start_local = start_time.replace(tzinfo=None)
            
            # Calculate duration in minutes
            # First check for duration_seconds directly
            duration_seconds = workout.get("duration_seconds", 0)
            self.logger.logger.debug(f"Workout duration_seconds direct: {duration_seconds}")
            
            # If not found, try to calculate from start and end times
            if not duration_seconds and "start" in workout and "end" in workout:
                start_time = datetime.fromisoformat(workout["start"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(workout["end"].replace("Z", "+00:00"))
                duration_seconds = (end_time - start_time).total_seconds()
                self.logger.logger.debug(f"Workout duration_seconds calculated from start/end: {duration_seconds}")
            
            # Convert to minutes
            duration_minutes = round(duration_seconds / 60, 1) if duration_seconds else 0
            self.logger.logger.debug(f"Workout duration_minutes: {duration_minutes}")
            
            # Get strain score
            strain = workout.get("score", {}).get("strain", 0)
            
            # Keep date as a datetime object for compatibility with metrics_aggregator
            date = start_local
            
            # Log the final workout data being returned
            self.logger.logger.debug(f"Returning workout data: sport={sport_name}, duration={duration_minutes}, strain={strain}")
            
            return {
                "date": date,  # Keep as datetime object
                "sport_id": sport_id,
                "sport": sport_name,
                "duration": duration_minutes,
                "strain": strain,
            }
        except Exception as e:
            self.logger.logger.debug(f"Error processing workout: {e}")
            return None
        
    def _transform_recovery(self, recovery: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform raw recovery data.
        
        Args:
            recovery: Raw recovery data
            
        Returns:
            Transformed recovery data
        """
        try:
            # Debug logging
            self.logger.logger.debug(f"Recovery data: {recovery.keys()}")
            
            # Skip if missing required data
            if "score" not in recovery:
                self.logger.logger.debug("Recovery missing 'score' field")
                return None
                
            # Get creation time
            created_at = recovery.get("created_at")
            if not created_at:
                self.logger.logger.debug("Recovery missing creation time")
                return None
                
            # Parse the UTC creation time
            created_utc = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            
            # Use local timezone if available, otherwise assume UTC
            timezone_offset = recovery.get("timezone_offset")
            if timezone_offset:
                # Parse the timezone offset into hours and minutes
                offset_sign = -1 if timezone_offset.startswith("-") else 1
                offset_hours = int(timezone_offset[1:3])
                offset_minutes = int(timezone_offset[4:6])
                offset_seconds = offset_sign * (offset_hours * 3600 + offset_minutes * 60)
                
                # Apply the offset to convert to local time
                created_local = (created_utc + timedelta(seconds=offset_seconds)).replace(
                    tzinfo=None
                )
            else:
                # If no timezone offset is provided, assume UTC and convert to local time
                self.logger.logger.debug("No timezone offset provided, assuming UTC")
                created_local = created_utc.replace(tzinfo=None)
            
            # Normalize the date to account for recovery scores that come in after midnight
            # Keep as datetime object for compatibility with metrics_aggregator
            recovery_date = created_local
            
            # Extract recovery metrics - handle different API response structures
            if isinstance(recovery.get("score"), dict):
                # Handle nested score structure
                score_dict = recovery.get("score", {})
                recovery_score = score_dict.get("recovery_score", 0)
                hrv_rmssd = score_dict.get("hrv_rmssd_milli", 0)
                resting_hr = score_dict.get("resting_heart_rate", 0)
            else:
                # Handle flat structure
                recovery_score = recovery.get("score", 0)
                hrv_rmssd = recovery.get("hrv", 0)
                resting_hr = recovery.get("resting_hr", 0)
            
            self.logger.logger.debug(f"Transformed recovery: date={recovery_date}, score={recovery_score}")
            
            return {
                "date": recovery_date,  # Keep as datetime object
                "recovery_score": recovery_score,
                "hrv_rmssd": hrv_rmssd,
                "resting_hr": resting_hr,
                # Sleep data will be added later
                "sleep_need": 0,
                "sleep_actual": 0,
            }
        except Exception as e:
            self.logger.logger.debug(f"Error processing recovery: {e}")
            return None
        
    def save_processed_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Save processed Whoop data to CSV files.
        
        Args:
            data: Dictionary of DataFrames with processed data
            
        Returns:
            Dictionary of paths to the saved files
        """
        from src.utils.file_utils import save_dataframe_to_file
        
        result = {}
        
        # Save workout data
        if "workouts" in data and not data["workouts"].empty:
            workout_path = save_dataframe_to_file(
                data["workouts"],
                name="whoop-workouts-data",
                subdir="processing"
            )
            result["workouts"] = workout_path
        
        # Save recovery data
        if "recovery" in data and not data["recovery"].empty:
            recovery_path = save_dataframe_to_file(
                data["recovery"],
                name="whoop-recovery-data",
                subdir="processing"
            )
            result["recovery"] = recovery_path
        
        return result
