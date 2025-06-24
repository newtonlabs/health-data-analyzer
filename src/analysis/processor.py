"""Module for orchestrating health data processing.

This module serves as a lightweight orchestrator that delegates the actual
processing work to specialized processor classes for each data source.
"""

import os
from datetime import datetime
from typing import Any

import pandas as pd

from src.analysis.processors.hevy import HevyProcessor
from src.analysis.processors.oura import OuraProcessor
from src.analysis.processors.whoop import WhoopProcessor
from src.analysis.processors.withings import WithingsProcessor
from src.sources.nutrition_data import NutritionData
from src.utils.logging_utils import HealthLogger
from src.utils.progress_indicators import ProgressIndicator


class Processor:
    """Orchestrator for health data processing.

    This class is responsible for:
    1. Delegating raw data processing to specialized processor classes
    2. Managing processed data in memory
    3. Coordinating data flow between processors and consumers
    """

    def __init__(self, output_dir: str = "data"):
        """Initialize Processor.

        Args:
            output_dir: Directory for storing output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up logger
        self.logger = HealthLogger(__name__)

        # Initialize specialized processors
        self.oura_processor = OuraProcessor()
        self.whoop_processor = WhoopProcessor()
        self.withings_processor = WithingsProcessor()
        self.hevy_processor = HevyProcessor()

        # Initialize nutrition data source
        self.nutrition = NutritionData(output_dir)

        # Hold processed data in memory
        self.oura_data = None
        self.whoop_data = None
        self.withings_data = None
        self.hevy_data = None

    def process_raw_data(
        self,
        oura_raw: dict[str, Any],
        whoop_raw: dict[str, Any],
        withings_raw: dict[str, Any] = None,
        hevy_raw: dict[str, Any] = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> None:
        """Process raw data from all sources.

        Args:
            oura_raw: Raw data from Oura API
            whoop_raw: Raw data from Whoop API
            withings_raw: Raw data from Withings API (optional)
            hevy_raw: Raw data from Hevy API (optional)
            start_date: Start date for filtering data
            end_date: End date for filtering data
        """
        # Process Oura data
        if oura_raw:
            self.logger.logger.debug("Processing Oura data")
            self.oura_data = self.process_oura_data(oura_raw, start_date, end_date)

        # Process Whoop data
        if whoop_raw:
            self.logger.logger.debug("Processing Whoop data")
            self.whoop_data = self.process_whoop_data(whoop_raw)

        # Process Withings data
        if withings_raw:
            self.logger.logger.debug("Processing Withings data")
            self.withings_data = self.process_withings_data(
                withings_raw, start_date, end_date
            )

        # Process Hevy data
        if hevy_raw:
            self.logger.logger.debug("Processing Hevy data")
            self.hevy_data = self.process_hevy_data(hevy_raw, end_date)

        # Process nutrition data from CSV
        self.logger.logger.debug("Processing nutrition data")
        self.process_nutrition_data(start_date, end_date)

    def process_oura_data(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> dict[str, pd.DataFrame]:
        """Process data from Oura API.

        Args:
            raw_data: Raw data from Oura API
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            Dictionary of DataFrames with processed data
        """
        # Delegate processing to the specialized OuraProcessor
        processed_data = self.oura_processor.process_data(
            raw_data, start_date, end_date
        )

        # Save the processed data to files
        self.oura_processor.save_processed_data(processed_data)

        return processed_data

    def process_whoop_data(self, raw_data: dict[str, Any]) -> dict[str, pd.DataFrame]:
        """Process data from Whoop API.

        Args:
            raw_data: Raw data from Whoop API

        Returns:
            Dictionary of DataFrames with processed data
        """
        # Delegate processing to the specialized WhoopProcessor
        processed_data = self.whoop_processor.process_data(raw_data)

        # Save the processed data to files
        self.whoop_processor.save_processed_data(processed_data)

        return processed_data

    def process_withings_data(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> dict[str, pd.DataFrame]:
        """Process data from Withings API.

        Args:
            raw_data: Raw data from Withings API
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            Dictionary of DataFrames with processed data
        """
        # Delegate processing to the specialized WithingsProcessor
        processed_data = self.withings_processor.process_data(
            raw_data, start_date, end_date
        )

        # Save the processed data to files
        self.withings_processor.save_processed_data(processed_data)

        return processed_data

    def process_hevy_data(
        self, raw_data: dict[str, Any], date: datetime
    ) -> dict[str, pd.DataFrame]:
        """Process data from Hevy API.

        Args:
            raw_data: Raw data from Hevy API
            date: Date to use for saving the files

        Returns:
            Dictionary of DataFrames with processed data
        """
        # Delegate processing to the specialized HevyProcessor
        workout_df, exercise_df = self.hevy_processor.process_workouts(raw_data)

        result = {}

        # Save the processed data if not empty
        if not workout_df.empty and not exercise_df.empty:
            workout_path, exercise_path = self.hevy_processor.save_processed_data(
                workout_df, exercise_df, date
            )
            self.logger.logger.info(f"Saved Hevy workout data to {workout_path}")
            self.logger.logger.info(f"Saved Hevy exercise data to {exercise_path}")

            # Store the processed data in the result dictionary
            result["workouts"] = workout_df
            result["exercises"] = exercise_df
        else:
            self.logger.logger.warning(
                "No Hevy workout data to process - DataFrames are empty"
            )

        return result

    def process_nutrition_data(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Process nutrition data from CSV file.

        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with processed nutrition data
        """
        # Show progress indicator
        ProgressIndicator.step_start("Fetching nutrition data from file")

        # Load nutrition data from CSV
        self.logger.logger.debug("Loading nutrition data from CSV")
        nutrition_df = self.nutrition.load_data(start_date, end_date)

        # Save the processed data if not empty
        if not nutrition_df.empty:
            file_path = self.nutrition.save_processed_data(nutrition_df, end_date)
            self.logger.logger.info(f"Saved processed nutrition data to {file_path}")

        # Mark nutrition data fetching as complete
        ProgressIndicator.step_complete()

        return nutrition_df
