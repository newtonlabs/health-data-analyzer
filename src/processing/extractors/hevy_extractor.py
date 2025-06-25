"""Hevy data extractor for processing workout data from Hevy API."""

from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.processing.extractors.base_extractor import BaseExtractor
from src.models.data_records import WorkoutRecord
from src.models.enums import DataSource
from src.analysis.processors.hevy import HevyProcessor


class HevyExtractor(BaseExtractor):
    """Extractor for processing Hevy workout data."""
    
    def __init__(self):
        """Initialize the Hevy extractor."""
        super().__init__(DataSource.HEVY)
        self.hevy_processor = HevyProcessor()
    
    def extract_workouts(
        self, 
        raw_data: Dict[str, Any], 
        end_date: datetime
    ) -> List[WorkoutRecord]:
        """Extract workout records from Hevy API response.
        
        Args:
            raw_data: Raw response from Hevy API containing workout data
            end_date: End date for filtering workouts (Hevy doesn't support date filtering in API)
            
        Returns:
            List of WorkoutRecord objects
        """
        if not raw_data or "workouts" not in raw_data:
            self.logger.warning("No workout data found in Hevy response")
            return []
        
        # Process the raw data using the existing HevyProcessor
        workout_df, exercise_df = self.hevy_processor.process_workouts(raw_data)
        
        if workout_df.empty:
            self.logger.warning("No workout data after processing")
            return []
        
        # Convert DataFrame to WorkoutRecord objects
        workout_records = []
        for _, row in workout_df.iterrows():
            try:
                # Extract workout date
                workout_date = row.get("date")
                if isinstance(workout_date, str):
                    workout_date = datetime.fromisoformat(workout_date.replace('Z', '+00:00'))
                elif not isinstance(workout_date, datetime):
                    continue  # Skip if date is not valid
                
                # Create WorkoutRecord
                record = WorkoutRecord(
                    date=workout_date.date(),
                    source="hevy",
                    workout_type=row.get("title", "Unknown"),
                    duration_minutes=row.get("duration_minutes", 0),
                    calories_burned=row.get("calories", 0),
                    sport_type=self._map_hevy_sport_type(row.get("title", "")),
                    metadata={
                        "workout_id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "description": row.get("description", ""),
                        "start_time": row.get("start_time", ""),
                        "end_time": row.get("end_time", ""),
                        "total_tonnage": row.get("total_tonnage", 0.0),
                        "exercise_count": row.get("exercise_count", 0),
                        "set_count": row.get("set_count", 0),
                        "created_at": row.get("created_at", ""),
                        "updated_at": row.get("updated_at", ""),
                    }
                )
                workout_records.append(record)
                
            except Exception as e:
                self.logger.error(f"Error creating WorkoutRecord from Hevy data: {e}")
                continue
        
        self.logger.info(f"Extracted {len(workout_records)} workout records from Hevy")
        return workout_records
    
    def extract_workout_and_exercise_data(
        self, 
        raw_data: Dict[str, Any], 
        end_date: datetime
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extract both workout and exercise DataFrames from Hevy API response.
        
        Args:
            raw_data: Raw response from Hevy API containing workout data
            end_date: End date for filtering workouts
            
        Returns:
            Tuple containing (workout_df, exercise_df)
        """
        if not raw_data or "workouts" not in raw_data:
            self.logger.warning("No workout data found in Hevy response")
            return pd.DataFrame(), pd.DataFrame()
        
        # Process the raw data using the existing HevyProcessor
        workout_df, exercise_df = self.hevy_processor.process_workouts(raw_data)
        
        self.logger.info(f"Extracted {len(workout_df)} workouts and {len(exercise_df)} exercises from Hevy")
        return workout_df, exercise_df
    
    def extract_all_data(
        self, 
        raw_data: Dict[str, Any], 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Extract all available data from Hevy API response.
        
        Args:
            raw_data: Raw response from Hevy API
            end_date: End date for filtering data
            
        Returns:
            Dictionary containing all extracted data
        """
        extracted_data = {}
        
        # Extract workout records
        workout_records = self.extract_workouts(raw_data, end_date)
        if workout_records:
            extracted_data["workout_records"] = workout_records
        
        # Extract workout and exercise DataFrames
        workout_df, exercise_df = self.extract_workout_and_exercise_data(raw_data, end_date)
        if not workout_df.empty:
            extracted_data["workout_df"] = workout_df
        if not exercise_df.empty:
            extracted_data["exercise_df"] = exercise_df
        
        self.logger.info(f"Extracted Hevy data with {len(extracted_data)} data types")
        return extracted_data
    
    def _map_hevy_sport_type(self, workout_title: str) -> str:
        """Map Hevy workout title to sport type.
        
        Args:
            workout_title: Title of the workout from Hevy
            
        Returns:
            Mapped sport type string
        """
        # Simple mapping based on common workout titles
        title_lower = workout_title.lower()
        
        if any(keyword in title_lower for keyword in ["push", "pull", "leg", "chest", "back", "arm", "shoulder"]):
            return "strength_training"
        elif any(keyword in title_lower for keyword in ["cardio", "run", "bike", "treadmill"]):
            return "cardio"
        elif any(keyword in title_lower for keyword in ["yoga", "stretch", "flexibility"]):
            return "flexibility"
        else:
            return "strength_training"  # Default for most Hevy workouts
    
    def extract_data(self, raw_data: Dict[str, Any]) -> Dict[str, List]:
        """Extract all data types from raw Hevy API response.
        
        This is the main entry point for Hevy data extraction, implementing
        the BaseExtractor interface.
        
        Args:
            raw_data: Raw API response data from Hevy
            
        Returns:
            Dictionary with keys like 'workout_records', 'processed_data', etc.
            and values as lists of structured records or processed DataFrames
        """
        self.logger.info("Starting Hevy data extraction")
        
        # Use a reasonable end date if not provided in raw_data
        # Hevy API doesn't support date filtering, so we use current time
        from datetime import datetime
        end_date = datetime.now()
        
        # Leverage the existing extract_all_data method
        extracted_data = self.extract_all_data(raw_data, end_date)
        
        # Save extracted data to CSV files
        saved_files = self.save_extracted_data_to_csv(extracted_data)
        if saved_files:
            self.logger.info(f" Hevy data exported to: {list(saved_files.values())}")
        
        return extracted_data
