"""Utility functions for date operations."""

from datetime import datetime, timedelta, timezone
from enum import Enum, auto
import logging
from typing import Optional, Union

import pandas as pd
import pytz

# Set up module logger
logger = logging.getLogger(__name__)


class DateFormat:
    """Standard date formats."""

    STANDARD = "%Y-%m-%d"  # Used by base.py for file naming
    DISPLAY = "%m-%d (%a)"  # Used by date_utils.py for display
    ISO = "%Y-%m-%dT%H:%M:%SZ"  # Used by whoop_client.py for API


class DateStatus(Enum):
    """Status of a date relative to today."""

    PAST = auto()
    TODAY = auto()
    FUTURE = auto()


class DateConfig:
    """Configuration for date handling."""

    # Recovery scores before this hour are counted for previous day
    RECOVERY_CUTOFF_HOUR = 4

    # Window sizes in days
    FETCH_WINDOW_DAYS = 15  # How many days of data to fetch (report window + buffer)
    REPORT_WINDOW_DAYS = 7  # How many days to show in report

    # Time configurations
    FETCH_END_HOUR = 23  # Hour to end data fetch (23 = 11 PM)
    FETCH_END_MINUTE = 59  # Minute to end data fetch
    FETCH_END_SECOND = 59  # Second to end data fetch
    
    # Default timezone for the application
    DEFAULT_TIMEZONE = "America/New_York"  # Eastern Time


class DateUtils:
    """Utility functions for date operations."""

    @staticmethod
    def get_date_ranges() -> tuple[datetime, datetime, datetime, datetime]:
        """Get all date ranges for the report.

        The report always ends at midnight yesterday, since we need complete
        data for the last day in the report. From there we calculate:
        - report_start: REPORT_WINDOW_DAYS before report_end
        - fetch_start: FETCH_WINDOW_DAYS before fetch_end
        - fetch_end: Day after report_end at 23:59:59

        Returns:
            Tuple of (report_start, report_end, fetch_start, fetch_end)
        """
        # Report always ends at midnight yesterday
        now = datetime.now()
        report_end = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=1
        )

        # Report starts REPORT_WINDOW_DAYS before report_end
        report_start = report_end - timedelta(days=DateConfig.REPORT_WINDOW_DAYS - 1)

        # Fetch until end of tomorrow to get any late data
        fetch_end = (report_end + timedelta(days=1)).replace(
            hour=DateConfig.FETCH_END_HOUR,
            minute=DateConfig.FETCH_END_MINUTE,
            second=DateConfig.FETCH_END_SECOND,
        )

        # Start fetching well before the report window
        fetch_start = (
            fetch_end - timedelta(days=DateConfig.FETCH_WINDOW_DAYS)
        ).replace(hour=0, minute=0, second=0)

        return report_start, report_end, fetch_start, fetch_end

    @staticmethod
    def get_report_path(end_date: datetime, extension: str = ".md") -> str:
        """Get path to report file.

        Args:
            end_date: End date for report
            extension: File extension (default: .md)

        Returns:
            Path to report file
        """
        return f"data/{end_date.strftime('%Y-%m-%d')}-weekly-status{extension}"

    @staticmethod
    def format_date(dt: datetime, fmt: str = DateFormat.STANDARD) -> str:
        """Format datetime using standard format."""
        return dt.strftime(fmt)

    @staticmethod
    def create_date_range_df(start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Create base DataFrame with date range.

        Args:
            start_date: Start date of the range.
            end_date: End date of the range.

        Returns:
            pd.DataFrame: DataFrame with 'date' (MM-DD) and 'day' (Mon, Tue, etc.) columns.
        """
        df = pd.DataFrame(
            {"date": pd.date_range(start=start_date, end=end_date, freq="D")}
        )
        df["day"] = df["date"].dt.strftime("%a")
        df["date"] = df["date"].dt.strftime("%m-%d")
        return df

    @staticmethod
    def get_day_of_week_labels(date_strings: list[str]) -> list[str]:
        """Convert date strings to day of week labels.

        Args:
            date_strings: List of date strings in format 'MM-DD' or other formats

        Returns:
            List of day of week labels in format 'MM-DD (Day)'
        """
        day_labels = []
        for date_str in date_strings:
            try:
                # Parse the date string and get the day of week
                # Handle different date formats
                if "-" in date_str and len(date_str) > 5:
                    # YYYY-MM-DD format
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    # Format as MM-DD
                    mm_dd = date_obj.strftime("%m-%d")
                elif "/" in date_str:
                    # MM/DD/YYYY format
                    date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                    # Format as MM-DD
                    mm_dd = date_obj.strftime("%m-%d")
                else:
                    # Try to parse as MM-DD format
                    mm_dd = date_str
                    # Add current year for day of week calculation
                    date_obj = datetime.strptime(f"2025-{date_str}", "%Y-%m-%d")
                
                # Get abbreviated day name (Mon, Tue, etc.)
                day_name = date_obj.strftime("%a")
                
                # Create the combined format: MM-DD (Day)
                formatted_label = f"{mm_dd} ({day_name})"
                
                # Add debug logging
                logger.debug(f"Converting '{date_str}' to '{formatted_label}'")
                
                day_labels.append(formatted_label)
            except ValueError as e:
                # If date parsing fails, use the original string
                logger.warning(f"Error parsing date '{date_str}': {e}")
                day_labels.append(date_str)
        return day_labels

    @staticmethod
    def normalize_recovery_date(created: datetime) -> datetime:
        """Normalize recovery date to 4 AM.

        If the recovery score was recorded before 4 AM, it's counted for the previous day.
        All recovery times are normalized to 4 AM for consistent date handling.

        Args:
            created: When the recovery score was recorded

        Returns:
            Normalized date at 4 AM
        """
        if created.hour < DateConfig.RECOVERY_CUTOFF_HOUR:
            created = created - timedelta(days=1)
        return created.replace(hour=DateConfig.RECOVERY_CUTOFF_HOUR, minute=0, second=0)

    @staticmethod
    def get_date_status(date: datetime) -> DateStatus:
        """Get status of a date relative to today.

        Args:
            date: Date to check

        Returns:
            DateStatus: PAST, TODAY, or FUTURE
        """
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        if date < today:
            return DateStatus.PAST
        elif date > today:
            return DateStatus.FUTURE
        else:
            return DateStatus.TODAY
            
    @staticmethod
    def convert_utc_to_local(utc_datetime: datetime, timezone_str: str = DateConfig.DEFAULT_TIMEZONE) -> datetime:
        """Convert UTC datetime to local time.
        
        Args:
            utc_datetime: Datetime in UTC (can be timezone-aware or naive)
            timezone_str: Timezone identifier (default: from DateConfig)
            
        Returns:
            Naive datetime object in local time
        """
        # Ensure the datetime is timezone-aware with UTC
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
        
        # Convert to the target timezone
        local_tz = pytz.timezone(timezone_str)
        local_datetime = utc_datetime.astimezone(local_tz)
        
        # Return naive datetime for compatibility with existing code
        return local_datetime.replace(tzinfo=None)

    @staticmethod
    def parse_iso_timestamp(timestamp_str: str, to_local: bool = True, 
                           timezone_str: str = DateConfig.DEFAULT_TIMEZONE) -> datetime:
        """Parse ISO format timestamp and optionally convert to local time.
        
        Args:
            timestamp_str: ISO format timestamp string (with or without timezone info)
            to_local: Whether to convert to local time (default: True)
            timezone_str: Timezone identifier (default: from DateConfig)
            
        Returns:
            Naive datetime object (in UTC or local time)
        """
        # Handle 'Z' suffix for UTC
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str.replace('Z', '+00:00')
        
        # Parse the timestamp
        dt = datetime.fromisoformat(timestamp_str)
        
        # If no timezone info in string, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to local time if requested
        if to_local:
            return DateUtils.convert_utc_to_local(dt, timezone_str)
        
        # Otherwise return naive UTC datetime
        return dt.replace(tzinfo=None)
        
    @staticmethod
    def parse_timestamp(timestamp: Union[str, int, float], to_local: bool = True,
                       timezone_str: str = DateConfig.DEFAULT_TIMEZONE) -> Optional[datetime]:
        """Parse different timestamp formats and convert to datetime.
        
        Handles:
        - ISO format strings (with or without timezone)
        - Unix timestamps (seconds since epoch)
        
        Args:
            timestamp: Timestamp as string, int, or float
            to_local: Whether to convert to local time
            timezone_str: Timezone identifier
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            # Handle ISO format timestamps (string)
            if isinstance(timestamp, str):
                return DateUtils.parse_iso_timestamp(timestamp, to_local, timezone_str)
            
            # Handle Unix timestamps (integer or float)
            elif isinstance(timestamp, (int, float)):
                dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                if to_local:
                    return DateUtils.convert_utc_to_local(dt_utc, timezone_str)
                return dt_utc.replace(tzinfo=None)
                
            return None
        except Exception:
            # Silent failure, return None
            return None
