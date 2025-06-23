"""Processor for Hevy workout data.

This module provides functionality to process and analyze workout data from the Hevy API.
It creates two dataframes:
1. A summary of workouts with total tonnage per workout
2. A detailed breakdown of exercises per workout with tonnage per exercise
"""

from datetime import datetime
from typing import Any

import pandas as pd

from src.utils.logging_utils import HealthLogger


class HevyProcessor:
    """Processor for Hevy workout data."""

    def __init__(self):
        """Initialize the HevyProcessor with a logger."""
        self.logger = HealthLogger(__name__)

    def process_workouts(
        self, workouts_data: dict[str, Any]
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Process Hevy workout data into two dataframes.

        Args:
            workouts_data: Raw workout data from the Hevy API

        Returns:
            Tuple containing:
                - workout_df: DataFrame with workout summaries and total tonnage
                - exercise_df: DataFrame with exercise details per workout
        """
        # Add logging at debug level
        self.logger.debug(f"Workouts data type: {type(workouts_data)}")
        if isinstance(workouts_data, dict):
            self.logger.debug(f"Workouts data keys: {workouts_data.keys()}")

        # Extract workouts from the data
        # Handle nested structure where workouts_data['workouts'] is another dict with a 'workouts' key
        if isinstance(workouts_data, dict):
            if "workouts" in workouts_data:
                # Check if workouts is a dict with another 'workouts' key (nested structure)
                if (
                    isinstance(workouts_data["workouts"], dict)
                    and "workouts" in workouts_data["workouts"]
                ):
                    workouts = workouts_data["workouts"]["workouts"]
                    self.logger.debug(
                        f"Using nested workouts: {type(workouts)}, length: {len(workouts)}"
                    )
                # Otherwise, check if workouts is a list
                elif isinstance(workouts_data["workouts"], list):
                    workouts = workouts_data["workouts"]
                    self.logger.debug(
                        f"Using direct workouts list: {type(workouts)}, length: {len(workouts)}"
                    )
                # Otherwise, it might be something else
                else:
                    workouts = []
                    self.logger.debug(
                        f"Unexpected workouts type: {type(workouts_data['workouts'])}"
                    )
            else:
                workouts = []
                self.logger.debug("No 'workouts' key in data")
        else:
            workouts = []
            self.logger.debug("Workouts data is not a dict, using empty list")

        if not workouts:
            self.logger.debug("No workouts found, returning empty DataFrames")
            return pd.DataFrame(), pd.DataFrame()

        # Process workouts into two dataframes
        workout_records = []
        exercise_records = []

        for i, workout in enumerate(workouts):
            # Add logging for each workout
            self.logger.debug(
                f"Processing workout {i+1}/{len(workouts)} - type: {type(workout)}"
            )

            # Handle case where workout might be a string instead of a dictionary
            if not isinstance(workout, dict):
                self.logger.debug(
                    f"Skipping workout with missing required fields: {workout}"
                )
                continue

            # Calculate workout metrics
            workout_id = workout.get("id")
            workout_title = workout.get("title")
            workout_description = workout.get("description", "")
            start_time = workout.get("start_time")
            end_time = workout.get("end_time")

            # Convert timestamps to datetime objects
            start_datetime = (
                datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if start_time
                else None
            )
            end_datetime = (
                datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                if end_time
                else None
            )

            # Calculate workout duration in minutes
            duration_minutes = None
            if start_datetime and end_datetime:
                duration_seconds = (end_datetime - start_datetime).total_seconds()
                duration_minutes = duration_seconds / 60

            exercises = workout.get("exercises", [])
            total_exercises = len(exercises)

            # Calculate total tonnage for the workout
            workout_tonnage = 0
            exercise_tonnages = {}

            for exercise in exercises:
                exercise_title = exercise.get("title")
                exercise_notes = exercise.get("notes", "")
                sets = exercise.get("sets", [])

                # Calculate tonnage for this exercise
                exercise_tonnage = 0
                num_sets = len(sets)

                for workout_set in sets:
                    weight_kg = workout_set.get("weight_kg")
                    reps = workout_set.get("reps")

                    # Calculate tonnage for this set (weight in lbs * reps)
                    if weight_kg is not None and reps is not None:
                        # Convert kg to lbs (1 kg ≈ 2.20462 lbs)
                        weight_lbs = weight_kg * 2.20462
                        set_tonnage = weight_lbs * reps
                        exercise_tonnage += set_tonnage

                # Add to total workout tonnage
                workout_tonnage += exercise_tonnage

                # Store exercise tonnage
                exercise_tonnages[exercise_title] = {
                    "tonnage": exercise_tonnage,
                    "num_sets": num_sets,
                    "notes": exercise_notes,
                }

                # Format the date as MM-DD to match other DataFrames
                workout_date_str = (
                    start_datetime.strftime("%m-%d") if start_datetime else ""
                )

                # Add day of week for better readability
                workout_day_str = (
                    start_datetime.strftime("%a") if start_datetime else ""
                )

                # Add record to exercise_records
                exercise_records.append(
                    {
                        "workout_id": workout_id,
                        "workout_title": workout_title,
                        "workout_description": workout_description,
                        "workout_date": (
                            start_datetime.date() if start_datetime else None
                        ),  # Full date object
                        "date": workout_date_str,  # MM-DD format for consistency
                        "day": workout_day_str,  # Day of week for readability
                        "exercise_name": exercise_title,
                        "exercise_notes": exercise_notes,
                        "tonnage": round(exercise_tonnage, 2),
                        "number_of_sets": num_sets,
                    }
                )

            # Format the date as MM-DD to match other DataFrames
            workout_date_str = (
                start_datetime.strftime("%m-%d") if start_datetime else ""
            )

            # Add day of week for better readability
            workout_day_str = start_datetime.strftime("%a") if start_datetime else ""

            # Add record to workout_records
            workout_records.append(
                {
                    "workout_id": workout_id,
                    "title": workout_title,
                    "description": workout_description,
                    "date": start_datetime.date() if start_datetime else None,
                    "workout_date": workout_date_str,  # Added for consistency with other processors
                    "day": workout_day_str,  # Added for consistency with other processors
                    "start_time": start_datetime,
                    "end_time": end_datetime,
                    "duration_minutes": (
                        round(duration_minutes, 2) if duration_minutes else None
                    ),
                    "num_exercises": total_exercises,
                    "total_tonnage": round(workout_tonnage, 2),
                }
            )

        # Create dataframes
        workout_df = pd.DataFrame(workout_records)
        exercise_df = pd.DataFrame(exercise_records)

        return workout_df, exercise_df

    def save_processed_data(
        self, workout_df: pd.DataFrame, exercise_df: pd.DataFrame, date: datetime
    ) -> tuple[str, str]:
        """Save processed Hevy data to CSV files.

        Args:
            workout_df: DataFrame with workout summaries
            exercise_df: DataFrame with exercise details
            date: Date to use in filenames

        Returns:
            Tuple of paths to the saved files (workout_file_path, exercise_file_path)
        """
        from src.utils.file_utils import save_dataframe_to_file

        # Date is passed directly to save_dataframe_to_file function

        # Save workout summary dataframe
        workout_file_path = save_dataframe_to_file(
            workout_df, name="hevy-workouts", subdir="processing", date=date
        )

        # Save exercise details dataframe
        exercise_file_path = save_dataframe_to_file(
            exercise_df, name="hevy-exercises", subdir="processing", date=date
        )

        return workout_file_path, exercise_file_path
