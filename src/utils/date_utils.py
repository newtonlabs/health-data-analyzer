"""Utility functions for date operations."""
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import List, Optional


class DateFormat:
    """Standard date formats."""
    STANDARD = '%Y-%m-%d'  # Used by base.py for file naming
    DISPLAY = '%m-%d (%a)'  # Used by date_utils.py for display
    ISO = '%Y-%m-%dT%H:%M:%SZ'  # Used by whoop_client.py for API


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
        report_end = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        
        # Report starts REPORT_WINDOW_DAYS before report_end
        report_start = report_end - timedelta(days=DateConfig.REPORT_WINDOW_DAYS-1)
        
        # Fetch until end of tomorrow to get any late data
        fetch_end = (report_end + timedelta(days=1)).replace(
            hour=DateConfig.FETCH_END_HOUR,
            minute=DateConfig.FETCH_END_MINUTE,
            second=DateConfig.FETCH_END_SECOND
        )
        
        # Start fetching well before the report window
        fetch_start = (fetch_end - timedelta(days=DateConfig.FETCH_WINDOW_DAYS)).replace(
            hour=0, minute=0, second=0
        )
        
        return report_start, report_end, fetch_start, fetch_end
    
    @staticmethod
    def get_report_path(end_date: datetime, extension: str = '.md') -> str:
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
    def get_day_of_week_labels(date_strings: List[str]) -> List[str]:
        """Convert date strings to day of week labels.
        
        Args:
            date_strings: List of date strings in format 'YYYY-MM-DD'
            
        Returns:
            List of day of week labels (e.g., 'Mon', 'Tue', etc.)
        """
        day_labels = []
        for date_str in date_strings:
            try:
                # Parse the date string and get the day of week
                # Handle different date formats
                if '-' in date_str:
                    # YYYY-MM-DD format
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                elif '/' in date_str:
                    # MM/DD/YYYY format
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                else:
                    # Try to parse as MM-DD format
                    date_obj = datetime.strptime(f"2025-{date_str}", '%Y-%m-%d')
                    
                # Get abbreviated day name (Mon, Tue, etc.)
                day_name = date_obj.strftime('%a')
                day_labels.append(day_name)
            except ValueError:
                # If date parsing fails, use the original string
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
