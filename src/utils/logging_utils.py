"""Logging utilities for health data analyzer."""
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Global debug flag (default to False)
DEBUG_MODE = False

def set_debug_mode(enabled: bool = False) -> None:
    """Set the global debug mode flag.
    
    Args:
        enabled: Whether debug mode is enabled
    """
    global DEBUG_MODE
    DEBUG_MODE = enabled
    
    # Configure root logger based on debug mode
    root_logger = logging.getLogger()
    if DEBUG_MODE:
        # In debug mode, show all DEBUG logs
        root_logger.setLevel(logging.DEBUG)
    else:
        # In normal mode, only show WARNING and above
        root_logger.setLevel(logging.WARNING)

class HealthLogger:
    """Logger for health data operations."""
    def __init__(self, name: str):
        """Initialize logger.
        
        Args:
            name: Logger name, typically module name
        """
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up logger with standard configuration."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # Set logger level based on debug mode
            global DEBUG_MODE
            if DEBUG_MODE:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)
    
    def log_recovery_processing(self, created: datetime, recovery_date: datetime,
                              recovery_info: Optional[Dict[str, Any]] = None):
        """Log recovery data processing.
        
        Args:
            created: When recovery score was recorded
            recovery_date: Normalized recovery date
            recovery_info: Optional recovery data
        """
        msg = f"Processing recovery from {created} -> {recovery_date}"
        if recovery_info:
            msg += f": score={recovery_info.get('recovery_score')}, "
            msg += f"hrv={recovery_info.get('hrv_rmssd')}, "
            msg += f"hr={recovery_info.get('resting_hr')}"
        self.logger.debug(msg)
    
    def log_skipped_date(self, date: datetime, reason: str):
        """Log skipped recovery date.
        
        Args:
            date: Date that was skipped
            reason: Why it was skipped
        """
        self.logger.warning(f"Skipped recovery date {date}: {reason}")
    
    def log_api_request(self, endpoint: str, params: Dict[str, Any]):
        """Log API request.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
        """
        self.logger.info(f"API request to {endpoint} with params: {params}")
    
    def log_date_range(self, start: datetime, end: datetime, context: str):
        """Log date range for operation.
        
        Args:
            start: Start date
            end: End date
            context: Operation context (e.g., 'fetch', 'report')
        """
        self.logger.info(f"{context} date range: {start.date()} to {end.date()}")
    
    def log_data_counts(self, data_type: str, count: int):
        """Log number of data items processed.
        
        Args:
            data_type: Type of data (e.g., 'recovery', 'workout')
            count: Number of items
        """
        self.logger.debug(f"Found {count} {data_type} records")
        
    def debug(self, message: str):
        """Log debug message (only shown in debug mode).
        
        Args:
            message: Debug message
        """
        if not DEBUG_MODE:
            return
        self.logger.info(f"DEBUG: {message}")
        
    def debug_dataframe(self, df, name: str, max_rows: int = 10):
        """Print a DataFrame in a readable format when in debug mode.
        
        Args:
            df: Pandas DataFrame to print
            name: Name of the DataFrame for identification
            max_rows: Maximum number of rows to display
        """
        if not DEBUG_MODE:
            return
            
        if df is None:
            self.logger.debug(f"DataFrame '{name}' is None")
            return
            
        import pandas as pd
        if not isinstance(df, pd.DataFrame):
            self.logger.debug(f"Object '{name}' is not a DataFrame, it's a {type(df)}")
            return
            
        if df.empty:
            self.logger.debug(f"DataFrame '{name}' is empty (0 rows)")
            return
            
        # Set pandas display options for better formatting
        with pd.option_context('display.max_rows', max_rows, 
                               'display.max_columns', None,
                               'display.width', 1000,
                               'display.precision', 2):
            self.logger.debug(f"\n===== DataFrame: {name} =====\n" + 
                          f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n" +
                          f"Columns: {', '.join(df.columns)}\n\n" +
                          f"{df.head(max_rows)}\n" +
                          "====================================")
