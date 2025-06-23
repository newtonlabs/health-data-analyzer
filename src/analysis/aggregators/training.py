"""Training aggregator module for metrics aggregation."""

from datetime import datetime
from typing import Dict, Any, List

import pandas as pd

from src.app_config import AppConfig
from src.utils.date_utils import DateUtils
from src.utils.file_utils import save_dataframe_to_file

from .base import BaseAggregator


class TrainingAggregator(BaseAggregator):
    """Aggregator for training metrics.
    
    Processes workout data to generate training metrics and summaries
    for reporting and visualization.
    """
    
    def get_training_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get training metrics for date range.
        
        Steps:
        1. Create base DataFrame for dates
        2. Get workout data for date range
        3. Format workout data into lookup
        4. Create training metrics with all workouts
        5. Filter out excluded sports and rest days
        
        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with columns:
            - date: Date of the workout (MM-DD)
            - day: Three letter day name
            - sport: Sport name (excluding Rest and excluded sports)
            - duration: Duration in HH:MM format
            - strain: Workout strain score (0-21)
        """
        # Step 1: Create base DataFrame for dates
        date_df = DateUtils.create_date_range_df(start_date, end_date)
        
        # Step 2: Get workout data
        workout_df = self._get_filtered_workout_data(start_date, end_date)
        if workout_df.empty:
            return date_df
            
        # Step 3: Format workout data
        workout_by_date = self._format_workout_data(workout_df)
        
        # Step 4: Create training metrics with all workouts
        # Start with an empty list to collect all workout rows
        all_workouts = []
        
        # For each date, add all workouts
        for _, row in date_df.iterrows():
            date = row["date"]
            day = row["day"]
            
            if date in workout_by_date and workout_by_date[date]["workouts"]:
                # Add each workout for this date
                for workout in workout_by_date[date]["workouts"]:
                    if (
                        workout["sport"] not in AppConfig.ANALYSIS_EXCLUDED_SPORTS
                        and workout["sport"] != "Rest"
                    ):
                        all_workouts.append(
                            {
                                "date": date,
                                "day": day,
                                "sport": workout["sport"],
                                "duration": workout["duration"],
                                "strain": workout["strain"],
                            }
                        )
                        
        # Create DataFrame from all workouts
        if all_workouts:
            df = pd.DataFrame(all_workouts)
        else:
            df = pd.DataFrame(columns=["date", "day", "sport", "duration", "strain"])
            
        # Save the final DataFrame to a file
        save_dataframe_to_file(df, "training-metrics", subdir="aggregations")
        
        return df
        
    def _get_filtered_workout_data(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get workout data filtered to date range.
        
        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with filtered workout data
        """
        if (
            self.processor.whoop_data is None
            or "workouts" not in self.processor.whoop_data
        ):
            return pd.DataFrame()
            
        return self.processor.whoop_data["workouts"][
            (self.processor.whoop_data["workouts"]["date"].dt.date >= start_date.date())
            & (self.processor.whoop_data["workouts"]["date"].dt.date <= end_date.date())
        ]
        
    def _format_workout_data(self, workout_df: pd.DataFrame) -> dict:
        """Format workout data into lookup by date.
        
        Args:
            workout_df: DataFrame with workout data
            
        Returns:
            Dictionary mapping dates to workout data
        """
        workout_df["date"] = workout_df["date"].dt.strftime("%m-%d")
        
        # Group workouts by date
        workout_by_date = {}
        
        # Debug logging for workout DataFrame
        self.logger.logger.debug(f"_format_workout_data - columns: {workout_df.columns}")
        self.logger.logger.debug(f"_format_workout_data - sample data: {workout_df.head(1).to_dict('records')}")
        
        # First pass: collect all workouts by date
        all_workouts_by_date = {}
        for _, row in workout_df.iterrows():
            date = row["date"]
            sport = row["sport"]
            strain = row["strain"]
            
            # Check if duration is in the row
            if "duration" in row:
                duration = row["duration"]
                self.logger.logger.debug(f"_format_workout_data - workout on {date}: sport={sport}, duration={duration}, type={type(duration)}")
            else:
                duration = 0
                self.logger.logger.debug(f"_format_workout_data - workout on {date}: sport={sport}, duration missing, using default 0")
                
            # Check if sport is in excluded list
            if sport in AppConfig.ANALYSIS_EXCLUDED_SPORTS:
                sport = "Rest"
                
            if date not in all_workouts_by_date:
                all_workouts_by_date[date] = []
                
            all_workouts_by_date[date].append(
                {"sport": sport, "duration": duration, "strain": strain}
            )
            
        # Store all workouts for each date
        for date, workouts in all_workouts_by_date.items():
            # Sort workouts by strain (descending)
            sorted_workouts = sorted(workouts, key=lambda x: x["strain"], reverse=True)
            
            # Determine primary workout based on new rules
            primary_workout = {"sport": "Rest", "duration": 0, "strain": 0}
            
            # Check if there are any workouts for this date
            if sorted_workouts:
                # First priority: Check for strength activities
                strength_workouts = [
                    w
                    for w in sorted_workouts
                    if w["sport"] in AppConfig.ANALYSIS_STRENGTH_ACTIVITIES
                ]
                if strength_workouts:
                    # Use the highest strain strength workout
                    primary_workout = strength_workouts[0]
                else:
                    # Second priority: Check for non-excluded sports
                    cardio_workouts = [
                        w
                        for w in sorted_workouts
                        if w["sport"] not in AppConfig.ANALYSIS_EXCLUDED_SPORTS
                    ]
                    if cardio_workouts:
                        # Use the highest strain cardio workout but label it as "Cardio"
                        primary_workout = cardio_workouts[0].copy()
                        primary_workout["sport"] = "Cardio"
                    # If no valid workouts, keep as 'Rest' (already set as default)
                    
            # Store all workouts for this date
            workout_by_date[date] = {
                "workouts": sorted_workouts,
                "primary": primary_workout,
            }
            
        return workout_by_date
