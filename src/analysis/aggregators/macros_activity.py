"""Macros and activity aggregator module for metrics aggregation."""

from datetime import datetime
from typing import Dict, Any

import pandas as pd

from src.app_config import AppConfig
from src.utils.date_utils import DateUtils
from src.utils.file_utils import save_dataframe_to_file

from .base import BaseAggregator


class MacrosActivityAggregator(BaseAggregator):
    """Aggregator for macros and activity metrics.
    
    Combines nutrition, activity, steps, and weight data into a single DataFrame
    for weekly reporting and visualization.
    """
    
    def weekly_macros_and_activity(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get weekly macros and activity metrics.
        
        Steps:
        1. Create base DataFrame with date range
        2. Get nutrition data
        3. Add steps data
        4. Add activity data
        5. Add weight data
        6. Format output
        
        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with columns:
            - date: Date of the summary (MM-DD)
            - day: Three letter day name
            - calories: Total calories consumed
            - protein: Protein in grams
            - carbs: Carbohydrates in grams
            - fat: Fat in grams
            - alcohol: Alcohol in grams
            - activity: Sport name or 'Rest'
            - steps: Daily step count
            - weight: Weight in pounds (if available)
        """
        # Step 1: Create base DataFrame with date range
        df = DateUtils.create_date_range_df(start_date, end_date)
        
        # Step 2: Get nutrition data
        nutrition_df = self._get_filtered_nutrition_data(start_date, end_date)
        
        # Create lookup by date string (MM-DD)
        nutrition_by_date = {}
        for _, row in nutrition_df.iterrows():
            date_key = row["date"].strftime("%m-%d")
            nutrition_by_date[date_key] = {
                "calories": row["calories"],
                "protein": row["protein"],
                "carbs": row["carbs"],
                "fat": row["fat"],
                "alcohol": row["alcohol"] if "alcohol" in row else 0,
            }
            
        # Set default values
        df["calories"] = 0
        df["protein"] = 0
        df["carbs"] = 0
        df["fat"] = 0
        df["alcohol"] = 0
        
        # Update with actual values
        for date in df["date"]:
            if date in nutrition_by_date:
                df.loc[df["date"] == date, "calories"] = nutrition_by_date[date]["calories"]
                df.loc[df["date"] == date, "protein"] = nutrition_by_date[date]["protein"]
                df.loc[df["date"] == date, "carbs"] = nutrition_by_date[date]["carbs"]
                df.loc[df["date"] == date, "fat"] = nutrition_by_date[date]["fat"]
                df.loc[df["date"] == date, "alcohol"] = nutrition_by_date[date]["alcohol"]
                
        # Step 3: Add steps data
        df = self._add_steps_data(df, start_date, end_date)
        
        # Step 4: Add activity data
        df = self._add_activity_data(df, start_date, end_date)
        
        # Step 5: Add weight data
        df = self._add_weight_data(df, start_date, end_date)
        
        # Step 6: Format output
        columns = [
            "date",
            "day",
            "calories",
            "protein",
            "carbs",
            "fat",
            "alcohol",
            "activity",
            "steps",
        ]
        if "weight" in df.columns:
            columns.append("weight")
        df = df[columns]
        
        # Save the final DataFrame to a file
        save_dataframe_to_file(df, "macros-and-activity", subdir="aggregations")
        
        return df
        
    def _get_filtered_nutrition_data(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get nutrition data filtered to date range.
        
        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with filtered nutrition data
        """
        df = self.processor.nutrition.load_data()
        
        # Filter to date range
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        
        # Fill missing values
        df = df.fillna({"calories": 0, "protein": 0, "carbs": 0, "fat": 0})
        
        # Round numeric values
        for col in ["calories", "protein", "carbs", "fat"]:
            df[col] = df[col].round(1)
            
        return df
        
    def _add_steps_data(
        self, df: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Add steps data to DataFrame.
        
        Args:
            df: DataFrame to add steps data to
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with steps data added
        """
        if self.processor.oura_data is None:
            df["steps"] = 0
            return df
            
        # Handle the new Oura data structure
        if (
            isinstance(self.processor.oura_data, dict)
            and "activity" in self.processor.oura_data
        ):
            oura_df = self.processor.oura_data["activity"].copy()
            
            # Check if we have data
            if oura_df.empty:
                df["steps"] = 0
                return df
                
            # Convert dates for comparison
            oura_df["date"] = pd.to_datetime(oura_df["date"])
            
            # Filter to date range
            oura_df = oura_df[
                (oura_df["date"] >= start_date) & (oura_df["date"] <= end_date)
            ]
            
            # Create steps lookup by date
            steps_by_date = {}
            for _, row in oura_df.iterrows():
                date_key = row["date"].strftime("%m-%d")
                steps_by_date[date_key] = row["steps"]
                
            # Add steps to DataFrame
            df["steps"] = df["date"].map(steps_by_date).fillna(0).astype(int)
        else:
            # Fallback for old data structure or empty data
            df["steps"] = 0
            
        return df
        
    def _add_activity_data(
        self, df: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Add activity data to DataFrame.
        
        Args:
            df: DataFrame to add activity data to
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with activity data added
        """
        # Default to Rest if no workout data available
        df["activity"] = "Rest"
        
        # Early return if no workout data
        if (
            self.processor.whoop_data is None
            or "workouts" not in self.processor.whoop_data
        ):
            return df
            
        # Filter to date range
        workout_df = self.processor.whoop_data["workouts"][
            (self.processor.whoop_data["workouts"]["date"].dt.date >= start_date.date())
            & (self.processor.whoop_data["workouts"]["date"].dt.date <= end_date.date())
        ]
        
        # Track best workout for each date
        best_workouts = {}
        
        # Debug logging for workout data
        self.logger.logger.debug(f"Workout DataFrame columns: {workout_df.columns}")
        if 'duration' in workout_df.columns:
            self.logger.logger.debug(f"Workout durations: {workout_df['duration'].tolist()}")
        else:
            self.logger.logger.debug("'duration' column not found in workout DataFrame")
        
        # Process each workout
        for _, row in workout_df.iterrows():
            date_key = row["date"].strftime("%m-%d")
            sport = row["sport"]
            strain = row["strain"]
            duration = row.get("duration", 0)
            self.logger.logger.debug(f"Processing workout: date={date_key}, sport={sport}, strain={strain}, duration={duration}")
            
            # Categorize the sport
            if sport in AppConfig.ANALYSIS_EXCLUDED_SPORTS:
                activity_type = "Rest"
                priority = 0  # Lowest priority
            elif sport in AppConfig.ANALYSIS_STRENGTH_ACTIVITIES:
                activity_type = "Strength"
                priority = 2  # Highest priority
            else:
                activity_type = "Cardio"
                priority = 1  # Medium priority
                
            # Check if we should update the best workout for this date
            current = best_workouts.get(date_key, {"priority": -1, "strain": -1})
            
            # Update if: higher priority or same priority but higher strain
            if priority > current["priority"] or (
                priority == current["priority"] and strain > current["strain"]
            ):
                best_workouts[date_key] = {
                    "sport": activity_type,
                    "strain": strain,
                    "priority": priority,
                }
                
        # Update DataFrame with best activities
        for date_key, workout in best_workouts.items():
            df.loc[df["date"] == date_key, "activity"] = workout["sport"]
            
        return df
        
    def _add_weight_data(
        self, df: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Add weight data to DataFrame.
        
        Args:
            df: DataFrame to add weight data to
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with weight data added
        """
        # Default to no weight data
        df["weight"] = None
        
        # Early return if no Withings data available
        if (
            self.processor.withings_data is None
            or "weight" not in self.processor.withings_data
        ):
            return df
            
        # Get weight data
        weight_df = self.processor.withings_data["weight"]
        
        # Create weight lookup by date
        weight_by_date = {}
        for _, row in weight_df.iterrows():
            if "date" in row and "weight" in row:
                weight_by_date[row["date"]] = row["weight"]
                
        # Update DataFrame with weight data
        for date in df["date"]:
            if date in weight_by_date:
                df.loc[df["date"] == date, "weight"] = weight_by_date[date]
                
        # Format weight values using the configured precision
        weight_precision = AppConfig.ANALYSIS_NUMERIC_PRECISION.get("weight", 1)
        df["weight"] = df["weight"].apply(
            lambda x: (
                round(float(x), weight_precision)
                if not pd.isna(x) and x != "-"
                else None
            )
        )
        
        return df
