"""Hevy data extractor for processing workout data from Hevy API."""

from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional

from .base_extractor import BaseExtractor
from src.models.raw_data import WorkoutRecord, ExerciseRecord
from src.models.enums import DataSource, SportType
from src.app_config import AppConfig
from src.utils.date_utils import DateUtils


class HevyExtractor(BaseExtractor):
    """Extractor for processing Hevy workout data."""
    
    def __init__(self):
        """Initialize the Hevy extractor."""
        super().__init__(DataSource.HEVY)
    
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract all data types from raw Hevy API response.
        
        This is pure extraction - converts raw API data to basic data models
        without any transformation, cleaning, or date filtering.
        
        Args:
            raw_data: Raw API response data from Hevy
            
        Returns:
            Dictionary with keys 'workout_records', 'exercise_records'
            and values as lists of structured records
        """
        extracted_data = {}
        
        # Extract workout data (pure conversion, no filtering)
        workout_records = self._extract_workouts(raw_data)
        if workout_records:
            extracted_data["workouts"] = workout_records
        
        # Extract exercise data (pure conversion, no filtering)
        exercise_records = self._extract_exercises(raw_data)
        if exercise_records:
            extracted_data["exercises"] = exercise_records
        
        self.logger.info(f"Extracted Hevy data with {len(extracted_data)} data types")
        return extracted_data
    
    def _extract_workouts(self, raw_data: Dict[str, Any]) -> List[WorkoutRecord]:
        """Extract workout records from Hevy API response.
        
        This is pure extraction - converts raw API data to basic WorkoutRecord models
        without any transformation, cleaning, or persistence.
        
        Args:
            raw_data: Raw response from Hevy API containing workout data
            end_date: End date for filtering data
            
        Returns:
            List of raw WorkoutRecord objects
        """
        # Handle nested structure: raw_data["workouts"] might contain {"workouts": [...]}
        workouts_data = raw_data.get("workouts", [])
        
        # If workouts_data is a dict with "workouts" key, extract the list
        if isinstance(workouts_data, dict) and "workouts" in workouts_data:
            workouts_list = workouts_data["workouts"]
        elif isinstance(workouts_data, list):
            workouts_list = workouts_data
        else:
            self.logger.info("No workout data found in Hevy response")
            return []
        
        workout_records = []
        
        # Direct conversion from raw API data to WorkoutRecord objects
        for workout in workouts_list:
            # Extract basic workout info
            workout_date = workout.get("start_time")
            if not workout_date:
                self.logger.info(f"No start_time found in Hevy workout data, skipping record")
                continue
            
            # Parse timestamp string to datetime object
            workout_timestamp = DateUtils.parse_iso_timestamp(workout_date)
            
            # Calculate duration in minutes
            start_time = workout.get("start_time")
            end_time = workout.get("end_time")
            duration_minutes = 0
            
            if start_time and end_time:
                start_dt = DateUtils.parse_iso_timestamp(start_time)
                end_dt = DateUtils.parse_iso_timestamp(end_time)
                duration_minutes = (end_dt - start_dt).total_seconds() / 60
            
            # Count sets and calculate volume
            set_count = 0
            total_volume = 0.0
            
            for exercise in workout.get("exercises", []):
                for set_data in exercise.get("sets", []):
                    set_count += 1
                    # Calculate volume (weight * reps)
                    weight = set_data.get("weight_kg", 0) or 0
                    reps = set_data.get("reps", 0) or 0
                    total_volume += weight * reps
            
            # Get sport type using config system (Hevy is strength training)
            sport_name = "Strength Training"
            sport_type = AppConfig.get_sport_type_from_name(sport_name)
            
            # Extract workout title from raw data
            workout_title = workout.get("title")
            
            # Create WorkoutRecord
            calculated_date = DateUtils.parse_timestamp(workout_timestamp, to_local=True)
            calculated_date = calculated_date.date() if calculated_date else None
            record = WorkoutRecord(
                timestamp=workout_timestamp,
                date=calculated_date,  # Calculate date in extractor
                source=DataSource.HEVY,
                sport_type=sport_type,
                sport_name=sport_name,
                title=workout_title,
                duration_minutes=duration_minutes,
                set_count=set_count,
                volume_kg=total_volume
            )
            workout_records.append(record)
        
        self.logger.info(f"Extracted {len(workout_records)} raw workout records from Hevy")
        return workout_records
    
    def _extract_exercises(self, raw_data: Dict[str, Any]) -> List[ExerciseRecord]:
        """Extract detailed exercise records from Hevy API response.
        
        This extracts individual sets and reps for each exercise.
        
        Args:
            raw_data: Raw response from Hevy API containing workout data
            end_date: End date for filtering data
            
        Returns:
            List of raw ExerciseRecord objects
        """
        # Handle nested structure: raw_data["workouts"] might contain {"workouts": [...]}
        workouts_data = raw_data.get("workouts", [])
        
        # If workouts_data is a dict with "workouts" key, extract the list
        if isinstance(workouts_data, dict) and "workouts" in workouts_data:
            workouts_list = workouts_data["workouts"]
        elif isinstance(workouts_data, list):
            workouts_list = workouts_data
        else:
            self.logger.info("No workout data found in Hevy response")
            return []
        
        exercise_records = []
        
        # Process each workout and extract exercises
        for workout in workouts_list:
            workout_date = workout.get("start_time")
            if not workout_date:
                continue
            
            # Parse timestamp string to datetime object
            workout_timestamp = DateUtils.parse_iso_timestamp(workout_date)
            
            # Process each exercise in the workout
            for exercise in workout.get("exercises", []):
                exercise_name = exercise.get("title", "Unknown Exercise")
                
                # Process each set in the exercise
                for set_index, set_data in enumerate(exercise.get("sets", []), 1):
                    # Extract set data
                    weight = set_data.get("weight_kg", 0) or 0
                    reps = set_data.get("reps", 0) or 0
                    set_type = set_data.get("type", "normal")
                    
                    # Create ExerciseRecord for each set
                    calculated_date = DateUtils.parse_timestamp(workout_timestamp, to_local=True)
                    calculated_date = calculated_date.date() if calculated_date else None
                    record = ExerciseRecord(
                        timestamp=workout_timestamp,
                        date=calculated_date,  # Calculate date in extractor
                        source=DataSource.HEVY,
                        workout_id=workout.get("id", ""),
                        exercise_name=exercise_name,
                        set_number=set_index,
                        set_type=set_type,
                        weight_kg=weight if weight > 0 else None,
                        reps=reps if reps > 0 else None
                    )
                    exercise_records.append(record)
        
        self.logger.info(f"Extracted {len(exercise_records)} raw exercise records from Hevy")
        return exercise_records
