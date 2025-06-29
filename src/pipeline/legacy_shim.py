"""Memory-based legacy shim to bridge new pipeline aggregated data to legacy reporting system.

This adapter allows the legacy reporting system to consume in-memory data from
the new pipeline without any CSV file I/O.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

import pandas as pd

from src.utils.logging_utils import HealthLogger


class MemoryBasedLegacyShim:
    """Memory-based shim that works with in-memory aggregated data.
    
    This class provides the same interface as the legacy Aggregator class
    but uses in-memory aggregated data from the new pipeline, avoiding CSV I/O.
    """
    
    def __init__(self, aggregated_data: dict):
        """Initialize the memory-based shim.
        
        Args:
            aggregated_data: Dictionary containing aggregated data from pipeline
                           Expected keys: 'macros', 'recovery', 'training'
        """
        self.aggregated_data = aggregated_data
        self.logger = HealthLogger(__name__)
    
    def _convert_to_dataframe(self, data_key: str, expected_columns: list) -> pd.DataFrame:
        """Convert aggregated data to DataFrame with expected columns.
        
        Args:
            data_key: Key in aggregated_data (e.g., 'macros', 'recovery', 'training')
            expected_columns: List of expected column names
            
        Returns:
            DataFrame with the data
        """
        if data_key not in self.aggregated_data:
            self.logger.warning(f"No {data_key} data found in aggregated data")
            return pd.DataFrame(columns=expected_columns)
        
        data_list = self.aggregated_data[data_key]
        if not data_list:
            self.logger.warning(f"Empty {data_key} data list")
            return pd.DataFrame(columns=expected_columns)
        
        # Convert list of objects to DataFrame
        df = pd.DataFrame([item.__dict__ if hasattr(item, '__dict__') else item for item in data_list])
        
        # Ensure all expected columns exist
        for col in expected_columns:
            if col not in df.columns:
                if col in ['calories', 'protein', 'carbs', 'fat', 'alcohol', 'steps']:
                    df[col] = 0
                elif col == 'strain':
                    df[col] = 0
                else:
                    df[col] = None
        
        # Convert date column to datetime if it's string
        if 'date' in df.columns and df['date'].dtype == 'object':
            df['date'] = pd.to_datetime(df['date'])
        
        return df[expected_columns]
    
    def _filter_last_7_days(self, df: pd.DataFrame, end_date: datetime) -> pd.DataFrame:
        """Filter DataFrame to last 7 days excluding today.
        
        Args:
            df: DataFrame with 'date' column
            end_date: End date for filtering (today)
            
        Returns:
            Filtered DataFrame with last 7 days of data
        """
        if df.empty or 'date' not in df.columns:
            return df
        
        # Calculate date range (last 7 days, not including today)
        start_date = end_date - timedelta(days=7)
        
        # Filter data
        filtered_df = df[
            (df['date'] >= start_date) & 
            (df['date'] < end_date)
        ].copy()
        
        self.logger.info(f"Filtered data: {len(filtered_df)} records from {start_date.date()} to {end_date.date()}")
        return filtered_df
    
    def weekly_macros_and_activity(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get weekly macros and activity metrics (legacy interface).
        
        Returns DataFrame matching legacy MacrosActivityAggregator format:
        - date: MM-DD string format
        - day: 3-letter day name
        - All numeric columns as expected
        """
        expected_columns = ['date', 'day', 'calories', 'protein', 'carbs', 'fat', 'alcohol', 'sport_type', 'steps', 'weight']
        df = self._convert_to_dataframe('macros_activity', expected_columns)
        df = self._filter_last_7_days(df, end_date)
        
        if not df.empty:
            # Convert to exact legacy format
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%m-%d')  # MM-DD format
            df['day'] = pd.to_datetime(df['date'], format='%m-%d').dt.strftime('%a')  # 3-letter day
            
            # Convert sport_type to activity column (legacy format expects string)
            if 'sport_type' in df.columns:
                df['activity'] = df['sport_type'].apply(self._format_sport_name)
                # Replace empty/None values with 'Rest'
                df['activity'] = df['activity'].fillna('Rest')
                df.loc[df['activity'] == '', 'activity'] = 'Rest'
            else:
                df['activity'] = 'Rest'  # Default to Rest if no sport_type column
            
            # Convert weight from kg to lb (legacy format expects pounds)
            if 'weight' in df.columns:
                df['weight'] = df['weight'] * 2.20462  # kg to lb conversion
        
        return df
    
    def recovery_metrics(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get recovery metrics (legacy interface).
        
        Returns DataFrame matching legacy RecoveryAggregator format:
        - date: MM-DD string format
        - day: 3-letter day name
        - All numeric and string columns as expected
        """
        expected_columns = ['date', 'day', 'recovery', 'resilience_level', 'hrv', 'hr', 'sleep_need', 'sleep_actual']
        df = self._convert_to_dataframe('recovery_metrics', expected_columns)
        df = self._filter_last_7_days(df, end_date)
        
        if not df.empty:
            # Convert to exact legacy format
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%m-%d')  # MM-DD format
            df['day'] = pd.to_datetime(df['date'], format='%m-%d').dt.strftime('%a')  # 3-letter day
            # Convert sleep times from minutes to hours (legacy format expects hours)
            if 'sleep_need' in df.columns:
                df['sleep_need'] = df['sleep_need'] / 60  # minutes to hours
            if 'sleep_actual' in df.columns:
                df['sleep_actual'] = df['sleep_actual'] / 60  # minutes to hours
        
        return df
    
    def training_metrics(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get training metrics (legacy interface).
        
        Returns DataFrame matching legacy TrainingAggregator format:
        - date: MM-DD string format
        - day: 3-letter day name
        - sport: formatted sport name string
        - duration: HH:MM string format
        - strain: numeric workout strain/count
        """
        expected_columns = ['date', 'day', 'sport', 'duration', 'strain']
        conversion_columns = expected_columns + ['workout_count']
        df = self._convert_to_dataframe('training_metrics', conversion_columns)
        df = self._filter_last_7_days(df, end_date)
        
        if not df.empty:
            # Map workout_count to strain first
            if 'workout_count' in df.columns:
                df['strain'] = df['workout_count'].fillna(0).astype(int)
                # Filter out days with no workouts
                df = df[df['workout_count'] > 0]
            else:
                df['strain'] = 0
            
            # Convert to exact legacy format
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%m-%d')  # MM-DD format
            df['day'] = pd.to_datetime(df['date'], format='%m-%d').dt.strftime('%a')  # 3-letter day
            
            # Format sport names
            if 'sport' in df.columns:
                df['sport'] = df['sport'].apply(self._format_sport_name)
            
            # Format duration
            if 'duration' in df.columns:
                df['duration'] = df['duration'].apply(self._format_duration)
            
            # Select only legacy columns
            df = df[expected_columns]
        
        return df
    
    def _format_sport_name(self, sport) -> str:
        """Convert sport enum to formatted string.
        
        Args:
            sport: SportType enum or string
            
        Returns:
            Formatted sport name (replace underscores with spaces, title case)
        """
        if sport is None:
            return ''
        
        # Handle SportType enum objects
        if hasattr(sport, 'value'):
            sport_str = sport.value
        elif hasattr(sport, 'name'):
            sport_str = sport.name
        else:
            sport_str = str(sport)
        
        # Handle enum format like "SportType.STRENGTH_TRAINING" or "<SportType.WALKING: 'walking'>"
        if '.' in sport_str:
            sport_str = sport_str.split('.')[-1]
        
        # Clean up any remaining brackets or quotes
        sport_str = sport_str.replace('>', '').replace("'", '').strip()
        
        # Replace underscores with spaces and title case
        return sport_str.replace('_', ' ').title()
    
    def _format_duration(self, duration_minutes) -> str:
        """Convert duration from minutes to HH:MM format.
        
        Args:
            duration_minutes: Duration in minutes (int or float)
            
        Returns:
            Duration in HH:MM format
        """
        if duration_minutes is None or pd.isna(duration_minutes):
            return '00:00'
        
        try:
            minutes = int(duration_minutes)
            hours = minutes // 60
            mins = minutes % 60
            return f'{hours:02d}:{mins:02d}'
        except (ValueError, TypeError):
            return '00:00'
