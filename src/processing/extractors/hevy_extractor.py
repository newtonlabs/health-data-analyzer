"""Hevy data extractor for processing workout data from Hevy API."""

from datetime import datetime
from typing import Any, Dict, List

from src.models.data_records import WorkoutRecord, ExerciseRecord
from src.models.enums import DataSource, SportType


class HevyExtractor:
    """Extractor for processing Hevy workout data."""
    
    def extract_workouts(
        self, 
        raw_data: Dict[str, Any], 
        end_date: datetime
    ) -> List[WorkoutRecord]:
        """Extract workout records from Hevy API response.
        
        This is pure extraction - converts raw API data to basic WorkoutRecord models
        without any transformation, cleaning, or persistence.
        
        Args:
            raw_data: Raw response from Hevy API containing workout data
            end_date: End date for filtering workouts (Hevy doesn't support date filtering in API)
            
        Returns:
            List of raw WorkoutRecord objects
        """
        if not raw_data or "workouts" not in raw_data:
            print("No workout data found in Hevy response")
            return []
        
        workout_records = []
        
        # Direct conversion from raw API data to WorkoutRecord objects
        for workout in raw_data["workouts"]:
            try:
                # Parse workout date
                start_time = workout.get("start_time", "")
                if start_time:
                    # Parse ISO format timestamp
                    workout_date = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    continue  # Skip if no start time
                
                # Filter by end date if provided
                if end_date and workout_date.date() > end_date.date():
                    continue
                
                # Calculate duration in minutes
                duration_minutes = 0
                if workout.get("start_time") and workout.get("end_time"):
                    start = datetime.fromisoformat(workout["start_time"].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(workout["end_time"].replace('Z', '+00:00'))
                    duration_minutes = int((end - start).total_seconds() / 60)
                
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
                
                # Create WorkoutRecord
                record = WorkoutRecord(
                    timestamp=workout_date,
                    date=None,  # Will be calculated in transformer
                    source=DataSource.HEVY,
                    sport=SportType.STRENGTH_TRAINING,  # Hevy is primarily strength training
                    duration_minutes=duration_minutes,
                    set_count=set_count,
                    volume_kg=total_volume
                )
                workout_records.append(record)
                
            except Exception as e:
                print(f"Error creating WorkoutRecord from Hevy data: {e}")
                continue
        
        print(f"Extracted {len(workout_records)} raw workout records from Hevy")
        return workout_records
    
    def extract_exercises(
        self, 
        raw_data: Dict[str, Any], 
        end_date: datetime
    ) -> List[ExerciseRecord]:
        """Extract detailed exercise records from Hevy API response.
        
        This extracts individual sets and reps for each exercise.
        
        Args:
            raw_data: Raw response from Hevy API containing workout data
            end_date: End date for filtering workouts
            
        Returns:
            List of raw ExerciseRecord objects
        """
        if not raw_data or "workouts" not in raw_data:
            print("No workout data found in Hevy response")
            return []
        
        exercise_records = []
        
        # Extract detailed exercise data
        for workout in raw_data["workouts"]:
            try:
                # Parse workout date
                start_time = workout.get("start_time", "")
                if start_time:
                    workout_date = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    continue
                
                # Filter by end date if provided
                if end_date and workout_date.date() > end_date.date():
                    continue
                
                workout_id = workout.get("id", "")
                
                # Extract each exercise and its sets
                for exercise in workout.get("exercises", []):
                    exercise_name = exercise.get("title", "Unknown Exercise")
                    
                    for set_index, set_data in enumerate(exercise.get("sets", [])):
                        # Create ExerciseRecord for each set
                        record = ExerciseRecord(
                            timestamp=workout_date,
                            date=None,  # Will be calculated in transformer
                            source=DataSource.HEVY,
                            workout_id=workout_id,
                            exercise_name=exercise_name,
                            set_number=set_index + 1,
                            set_type=set_data.get("type", "normal"),
                            weight_kg=set_data.get("weight_kg"),
                            reps=set_data.get("reps")
                        )
                        exercise_records.append(record)
                        
            except Exception as e:
                print(f"Error creating ExerciseRecord from Hevy data: {e}")
                continue
        
        print(f"Extracted {len(exercise_records)} raw exercise records from Hevy")
        return exercise_records
