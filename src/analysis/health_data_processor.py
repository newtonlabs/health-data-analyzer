"""Module for processing raw health data into clean DataFrames."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd

from src.data_sources.nutrition_data import NutritionData
from src.data_sources.whoop_constants import get_sport_name
from src.utils.date_utils import DateStatus, DateUtils
from src.utils.logging_utils import DEBUG_MODE, HealthLogger

from .analyzer_config import AnalyzerConfig


class HealthDataProcessor:
    """Process raw health data from various sources.

    This class handles:
    1. Raw data ingestion from APIs
    2. Data extraction and transformation
    3. Data cleaning and filtering

    The class focuses on converting raw API data into clean,
    structured DataFrames that can be used for metrics generation.
    """

    def __init__(self, output_dir: str = "data"):
        """Initialize HealthDataProcessor.

        Args:
            output_dir: Directory for storing output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up utilities
        self.logger = HealthLogger(__name__)

        # Initialize data sources
        self.nutrition = NutritionData(output_dir)

        # Hold processed data in memory
        self.oura_data = None
        self.whoop_data = None
        self.withings_data = None

    def process_raw_data(
        self,
        oura_raw: dict[str, Any],
        whoop_raw: dict[str, Any],
        withings_raw: dict[str, Any] = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> None:
        """Process raw data from all sources.

        Steps:
        1. Process Oura data
        2. Process Whoop data
        3. Process Withings data
        4. Load nutrition data

        Args:
            oura_raw: Raw Oura API data
            whoop_raw: Raw Whoop API data
            withings_raw: Raw Withings API data (optional)
            start_date: Start date for processing
            end_date: End date for processing
        """
        # Process each source
        if oura_raw:
            self.oura_data = self.process_oura_data(oura_raw, start_date, end_date)

            # Display the processed Oura data in debug mode
            if self.oura_data:
                if "activity" in self.oura_data:
                    self.logger.debug_dataframe(
                        self.oura_data["activity"], "Oura Activity Data"
                    )
                if "resilience" in self.oura_data:
                    self.logger.debug_dataframe(
                        self.oura_data["resilience"], "Oura Resilience Data"
                    )

        # Process Whoop data
        if whoop_raw:
            self.whoop_data = self.process_whoop_data(whoop_raw)

            # Display the processed Whoop data in debug mode
            if self.whoop_data:
                if "workouts" in self.whoop_data:
                    self.logger.debug_dataframe(
                        self.whoop_data["workouts"], "Whoop Workouts Data"
                    )
                if "recovery" in self.whoop_data:
                    self.logger.debug_dataframe(
                        self.whoop_data["recovery"], "Whoop Recovery Data"
                    )
                if "sleep" in self.whoop_data:
                    self.logger.debug_dataframe(
                        self.whoop_data["sleep"], "Whoop Sleep Data"
                    )

        # Process Withings data
        if withings_raw:
            # Always print the full Withings API response in debug mode
            if DEBUG_MODE:
                self.logger.debug(
                    "===== WITHINGS API RESPONSE =====\n"
                    + json.dumps(withings_raw, indent=2)
                    + "\n===== END WITHINGS API RESPONSE ====="
                )
            self.withings_data = self.process_withings_data(
                withings_raw, start_date, end_date
            )
            self.logger.debug(
                f"Processed Withings data: {self.withings_data['weight'].shape[0]} weight records"
            )
            # Display the processed weight data in debug mode
            if DEBUG_MODE and "weight" in self.withings_data:
                self.logger.debug_dataframe(
                    self.withings_data["weight"], "Withings Weight Data"
                )
            # Only print debug info when in DEBUG_MODE
            if DEBUG_MODE:
                self.logger.debug(
                    "===== Withings Weight DataFrame (direct print) ====="
                )
                self.logger.debug(self.withings_data["weight"])
                self.logger.debug(f"Shape: {self.withings_data['weight'].shape}")
                self.logger.debug(
                    f"Columns: {self.withings_data['weight'].columns.tolist()}"
                )
                self.logger.debug("==============================================")

    def process_oura_data(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> dict[str, pd.DataFrame]:
        """Process data from Oura API.

        Steps:
        1. Process activity data
        2. Process resilience data
        3. Return combined results

        Args:
            raw_data: Raw Oura API response containing activity and resilience data
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            Dictionary of DataFrames with processed data
        """
        result = {}

        # Process activity data
        if "activity" in raw_data:
            result["activity"] = self._process_oura_activity(
                raw_data["activity"], start_date, end_date
            )

        # Process resilience data
        if "resilience" in raw_data:
            result["resilience"] = self._process_oura_resilience(
                raw_data["resilience"], start_date, end_date
            )

        return result

    def _process_oura_activity(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Process activity data from Oura API.

        Args:
            raw_data: Raw Oura activity data
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with daily activity metrics
        """
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=["date", "steps"])

        # Return empty DataFrame if no data
        if not raw_data or "data" not in raw_data:
            self.logger.log_skipped_date(None, "Invalid Oura activity data structure")
            return df

        # Extract activity data and round steps
        activity_data = []

        for activity in raw_data.get("data", []):
            if "steps" in activity and "day" in activity:
                activity_data.append(
                    {"date": activity["day"], "steps": round(activity["steps"])}
                )

        # Create DataFrame if we have data
        if activity_data:
            df = pd.DataFrame(activity_data)

        return df

    def _process_oura_resilience(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Process resilience data from Oura API.

        Args:
            raw_data: Raw Oura resilience data
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with daily resilience metrics
        """
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=["date", "resilience_score", "resilience_level"])

        # Return empty DataFrame if no data
        if not raw_data or "data" not in raw_data:
            self.logger.log_skipped_date(None, "Invalid Oura resilience data structure")
            return df

        # Extract resilience data
        resilience_data = []
        for item in raw_data["data"]:
            # Extract date from the ID (format: YYYY-MM-DD)
            try:
                date_str = item.get("day")
                if not date_str:
                    continue

                # Convert to datetime for filtering
                day_date = datetime.strptime(date_str, "%Y-%m-%d")

                # Skip if outside date range
                if (
                    day_date.date() < start_date.date()
                    or day_date.date() > end_date.date()
                ):
                    continue

                # Extract resilience level and convert to score
                resilience_level = item.get("level")
                if resilience_level is None:
                    continue

                # Get score from AnalyzerConfig mapping or use default of 0
                resilience_score = AnalyzerConfig.RESILIENCE_LEVEL_SCORES.get(
                    resilience_level.lower(), 0
                )

                # Add to data list
                resilience_data.append(
                    {
                        "date": date_str,
                        "resilience_score": round(resilience_score, 1),
                        "resilience_level": resilience_level.lower(),
                    }
                )
            except Exception as e:
                self.logger.log_skipped_date(
                    None, f"Error processing resilience data: {str(e)}"
                )
                continue

        # Create DataFrame if we have data
        if resilience_data:
            df = pd.DataFrame(resilience_data)

        return df

    def process_whoop_data(self, raw_data: dict[str, Any]) -> dict[str, pd.DataFrame]:
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
            self.logger.log_skipped_date(None, "Invalid Whoop data structure")
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
            for recovery in raw_data["recovery"]["records"]:
                transformed = self._transform_recovery(recovery)
                if transformed:
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
            workouts_df = self._round_numeric_columns(workouts_df)
            workouts_df["sport"] = workouts_df["sport_id"].apply(get_sport_name)

        if recovery_data:
            recovery_df = pd.DataFrame(recovery_data)
            recovery_df = self._round_numeric_columns(recovery_df)

        return {"workouts": workouts_df, "recovery": recovery_df}

    def _transform_workout(self, workout: dict[str, Any]) -> dict[str, Any]:
        """Transform raw workout data.

        Args:
            workout: Raw workout data

        Returns:
            Transformed workout data
        """
        # Get timezone offset from the workout data
        timezone_offset = workout.get("timezone_offset", "+00:00")

        # Parse UTC timestamps first
        start_time_utc = datetime.fromisoformat(workout["start"].replace("Z", "+00:00"))
        end_time_utc = datetime.fromisoformat(workout["end"].replace("Z", "+00:00"))

        # Parse the timezone offset into hours and minutes
        offset_sign = -1 if timezone_offset.startswith("-") else 1
        offset_hours = int(timezone_offset[1:3])
        offset_minutes = int(timezone_offset[4:6])
        offset_seconds = offset_sign * (offset_hours * 3600 + offset_minutes * 60)

        # Apply the offset to convert to local time
        start_time = (start_time_utc + timedelta(seconds=offset_seconds)).replace(
            tzinfo=None
        )
        end_time = (end_time_utc + timedelta(seconds=offset_seconds)).replace(
            tzinfo=None
        )

        # Use start time as the workout date
        workout_date = start_time

        # Calculate duration in minutes
        duration_minutes = int((end_time - start_time).total_seconds() / 60)

        return {
            "date": workout_date,
            "id": workout.get("id"),
            "sport_id": workout.get("sport_id"),
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration_minutes,
            "strain": workout.get("score", {}).get("strain", 0),
            "avg_hr": workout.get("score", {}).get("average_heart_rate", 0),
            "max_hr": workout.get("score", {}).get("max_heart_rate", 0),
            "kilojoules": workout.get("score", {}).get("kilojoule", 0),
            "distance_meters": workout.get("score", {}).get("distance_meter", 0),
            "altitude_gain": workout.get("score", {}).get("altitude_gain", 0),
        }

    def _transform_recovery(self, recovery: dict[str, Any]) -> dict[str, Any]:
        """Transform raw recovery data.

        Args:
            recovery: Raw recovery data

        Returns:
            Transformed recovery data
        """
        # Get timezone offset from the recovery data
        timezone_offset = recovery.get("timezone_offset", "+00:00")

        # Parse UTC timestamp first
        created_utc = datetime.fromisoformat(
            recovery["created_at"].replace("Z", "+00:00")
        )

        # Parse the timezone offset into hours and minutes
        offset_sign = -1 if timezone_offset.startswith("-") else 1
        offset_hours = int(timezone_offset[1:3])
        offset_minutes = int(timezone_offset[4:6])
        offset_seconds = offset_sign * (offset_hours * 3600 + offset_minutes * 60)

        # Apply the offset to convert to local time
        created = (created_utc + timedelta(seconds=offset_seconds)).replace(tzinfo=None)

        # Normalize recovery date to 4 AM
        recovery_date = DateUtils.normalize_recovery_date(created)

        # Skip future dates
        if DateUtils.get_date_status(recovery_date) == DateStatus.FUTURE:
            self.logger.log_skipped_date(recovery_date, "Future date")
            return None

        # Extract recovery info from the score object
        recovery_info = recovery.get("score", {})

        # Recovery processing logs are completely disabled to reduce debug output clutter
        # The detailed recovery data will still be processed and included in the final report

        return {
            "date": recovery_date,
            "recovery_score": recovery_info.get("recovery_score"),
            "hrv_rmssd": recovery_info.get("hrv_rmssd_milli"),
            "resting_hr": recovery_info.get("resting_heart_rate"),
            "spo2": recovery_info.get("spo2_percentage"),
            "sleep_need": None,  # Will be populated later from sleep data
            "sleep_actual": None,  # Will be populated later from sleep data
        }

    def _round_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Round numeric columns to specified precision.

        Args:
            df: DataFrame to round

        Returns:
            DataFrame with rounded values
        """
        for col in df.select_dtypes(include=["float64"]).columns:
            if col in AnalyzerConfig.NUMERIC_PRECISION:
                df[col] = df[col].round(AnalyzerConfig.NUMERIC_PRECISION[col])
        return df

    def process_withings_data(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> dict[str, pd.DataFrame]:
        """Process data from Withings API.

        Steps:
        1. Process weight measurements
        2. Return results

        Args:
            raw_data: Raw Withings API response containing weight data
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            Dictionary of DataFrames with processed data
        """
        result = {}

        # Import and define timezone early to avoid NameError
        from datetime import timezone

        import pytz

        local_tz = pytz.timezone("America/New_York")

        weight_data = []
        if "weight" in raw_data:
            # Process each measurement group from the Withings API
            measuregrps = raw_data["weight"].get("measuregrps", [])
            self.logger.debug(
                f"Processing {len(measuregrps)} Withings measurement groups"
            )

            for group in measuregrps:
                timestamp = group.get("date")
                if not timestamp:
                    continue

                # Convert timestamp from UTC to local time
                dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                dt_local = dt_utc.astimezone(local_tz)

                # Skip if outside date range
                if start_date and dt_local.date() < start_date.date():
                    continue
                if end_date and dt_local.date() > end_date.date():
                    continue

                # Process weight measurements (type 1)
                for measure in group.get("measures", []):
                    if measure.get("type") == 1:
                        # Convert value using unit multiplier (e.g., -3 means ×10^-3)
                        value = measure.get("value", 0) * (10 ** measure.get("unit", 0))
                        weight_data.append(
                            {
                                "date": dt_local.date(),
                                "weight": value,
                                "timestamp": timestamp,
                            }
                        )

            # Create DataFrame with both date and timestamp
            df = pd.DataFrame(weight_data, columns=["date", "weight", "timestamp"])
            self.logger.debug("Withings weight data after extraction:")
            self.logger.debug(f"Shape: {df.shape}, Columns: {df.columns.tolist()}")

            if df.empty:
                return {"weight": pd.DataFrame(columns=["date", "day", "weight"])}

            # Sort by timestamp so the latest measurement per day is always kept
            df_sorted = df.sort_values("timestamp")
            df_latest = df_sorted.groupby("date", as_index=True).last()

            # Build full 7-day index (yesterday to 6 days prior) to ensure all days are included
            today = datetime.now(local_tz).date()
            yesterday = today - timedelta(days=1)
            week_start = yesterday - timedelta(days=6)
            full_index = [week_start + timedelta(days=i) for i in range(7)]

            # Reindex to include all days in the reporting window
            df_latest = df_latest.reindex(full_index)
            self.logger.debug(
                f"Reindexing to include all days in the reporting window: week_start={week_start}, yesterday={yesterday}"
            )
            self.logger.debug(
                f"Dates after grouping and reindexing: {df_latest.index.tolist()}"
            )

            # Format date as MM-DD to match other DataFrames
            df_latest["date"] = [
                d.strftime("%m-%d") if d is not None else "" for d in df_latest.index
            ]

            # Add day of week for better readability
            df_latest["day"] = [
                d.strftime("%a") if d is not None else "" for d in df_latest.index
            ]
            # Convert weight from kg to pounds and round to the configured precision
            KG_TO_LB = 2.20462
            weight_precision = AnalyzerConfig.NUMERIC_PRECISION.get("weight", 1)
            df_latest["weight"] = (df_latest["weight"] * KG_TO_LB).round(
                weight_precision
            )

            # Reorder columns for consistency with other DataFrames
            df_latest = df_latest[["date", "day", "weight"]]
            return {"weight": df_latest}
        else:
            # Return empty DataFrame with expected columns if no data
            return {"weight": pd.DataFrame(columns=["date", "day", "weight"])}
