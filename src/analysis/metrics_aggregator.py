"""Module for generating health and fitness metrics."""
from datetime import datetime
from typing import Dict, Any

import pandas as pd

from src.utils.logging_utils import HealthLogger
from .analyzer_config import AnalyzerConfig
from .health_data_processor import HealthDataProcessor


class MetricsAggregator:
    """Generate health and fitness metrics from processed data.
    
    This class handles:
    1. Combining data from multiple sources
    2. Generating daily and weekly metrics
    3. Creating summary statistics
    4. Preparing data for reporting
    
    The class focuses on transforming clean data into meaningful metrics
    that can be used for analysis and reporting.
    """
    
    def __init__(self, processor: HealthDataProcessor):
        """Initialize MetricsAggregator.
        
        Args:
            processor: HealthDataProcessor instance to use for data
        """
        self.processor = processor
        self.logger = HealthLogger(__name__)
    
    def _get_filtered_recovery_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get recovery data filtered to date range."""
        if self.processor.whoop_data is None or 'recovery' not in self.processor.whoop_data:
            return pd.DataFrame()
        df = self.processor.whoop_data['recovery'][
            (self.processor.whoop_data['recovery']['date'].dt.date >= start_date.date()) & 
            (self.processor.whoop_data['recovery']['date'].dt.date <= end_date.date())
        ].copy()
        return df
    
    def _format_recovery_data(self, recovery_df: pd.DataFrame) -> dict:
        """Format recovery data into lookup by date."""
        recovery_df['date'] = recovery_df['date'].dt.strftime('%m-%d')
        
        recovery_by_date = {}
        for _, row in recovery_df.iterrows():
            recovery_by_date[row['date']] = {
                'recovery': row['recovery_score'],
                'hrv': row['hrv_rmssd'],
                'hr': row['resting_hr'],
                'sleep_need': row['sleep_need'],
                'sleep_actual': row['sleep_actual']
            }
        return recovery_by_date
    
    def _update_recovery_metrics(self, df: pd.DataFrame, recovery_by_date: dict) -> pd.DataFrame:
        """Update DataFrame with recovery metrics."""
        # Set default values
        df['recovery'] = '-'
        df['hrv'] = '-'
        df['hr'] = '-'
        df['sleep_need'] = '-'
        df['sleep_actual'] = '-'
        
        # Update with actual values
        for date in df['date']:
            if date in recovery_by_date:
                df.loc[df['date'] == date, 'recovery'] = recovery_by_date[date]['recovery']
                df.loc[df['date'] == date, 'hrv'] = recovery_by_date[date]['hrv']
                df.loc[df['date'] == date, 'hr'] = recovery_by_date[date]['hr']
                df.loc[df['date'] == date, 'sleep_need'] = recovery_by_date[date]['sleep_need']
                df.loc[df['date'] == date, 'sleep_actual'] = recovery_by_date[date]['sleep_actual']
        
        # Format numeric values
        for col in ['recovery', 'hrv', 'hr']:
            df[col] = df[col].apply(lambda x: round(float(x), 1) if not pd.isna(x) and x != '-' else None)
            
        # Format sleep values to 1 decimal place
        for col in ['sleep_need', 'sleep_actual']:
            df[col] = df[col].apply(lambda x: round(float(x), 1) if not pd.isna(x) and x != '-' else None)
        
        return df
    
    def _get_filtered_workout_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get workout data filtered to date range."""
        if self.processor.whoop_data is None or 'workouts' not in self.processor.whoop_data:
            return pd.DataFrame()
            
        return self.processor.whoop_data['workouts'][
            (self.processor.whoop_data['workouts']['date'].dt.date >= start_date.date()) & 
            (self.processor.whoop_data['workouts']['date'].dt.date <= end_date.date())
        ].copy()
    
    def _format_workout_data(self, workout_df: pd.DataFrame) -> dict:
        """Format workout data into lookup by date."""
        workout_df['date'] = workout_df['date'].dt.strftime('%m-%d')
        
        # Group workouts by date
        workout_by_date = {}
        
        # First pass: collect all workouts by date
        all_workouts_by_date = {}
        for _, row in workout_df.iterrows():
            date = row['date']
            sport = row['sport']
            strain = row['strain']
            duration = row['duration']
            
            # Check if sport is in excluded list
            if sport in AnalyzerConfig.EXCLUDED_SPORTS:
                sport = 'Rest'
            
            if date not in all_workouts_by_date:
                all_workouts_by_date[date] = []
                
            all_workouts_by_date[date].append({
                'sport': sport,
                'duration': duration,
                'strain': strain
            })
        
        # Store all workouts for each date
        for date, workouts in all_workouts_by_date.items():
            # Sort workouts by strain (descending)
            sorted_workouts = sorted(workouts, key=lambda x: x['strain'], reverse=True)
            
            # Determine primary workout based on new rules
            primary_workout = {'sport': 'Rest', 'duration': 0, 'strain': 0}
            
            # Check if there are any workouts for this date
            if sorted_workouts:
                # First priority: Check for strength activities
                strength_workouts = [w for w in sorted_workouts if w['sport'] in AnalyzerConfig.STRENGTH_ACTIVITIES]
                if strength_workouts:
                    # Use the highest strain strength workout
                    primary_workout = strength_workouts[0]
                else:
                    # Second priority: Check for non-excluded sports
                    cardio_workouts = [w for w in sorted_workouts if w['sport'] not in AnalyzerConfig.EXCLUDED_SPORTS]
                    if cardio_workouts:
                        # Use the highest strain cardio workout but label it as "Cardio"
                        primary_workout = cardio_workouts[0].copy()
                        primary_workout['sport'] = 'Cardio'
                    # If no valid workouts, keep as 'Rest' (already set as default)
            
            # Store all workouts for this date
            workout_by_date[date] = {
                'workouts': sorted_workouts,
                'primary': primary_workout
            }
        return workout_by_date
    

    
    def _create_date_range_df(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Create base DataFrame with date range."""
        df = pd.DataFrame({'date': pd.date_range(start=start_date, end=end_date, freq='D')})
        df['day'] = df['date'].dt.strftime('%a')
        df['date'] = df['date'].dt.strftime('%m-%d')
        return df
    
    def _get_filtered_resilience_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get resilience data filtered to date range."""
        if self.processor.oura_data is None or 'resilience' not in self.processor.oura_data:
            return pd.DataFrame()
        
        # Convert date strings to datetime objects for proper comparison
        resilience_df = self.processor.oura_data['resilience'].copy()
        if not resilience_df.empty and 'date' in resilience_df.columns:
            resilience_df['date_obj'] = pd.to_datetime(resilience_df['date'])
            filtered_df = resilience_df[
                (resilience_df['date_obj'].dt.date >= start_date.date()) & 
                (resilience_df['date_obj'].dt.date <= end_date.date())
            ].copy()
            filtered_df.drop('date_obj', axis=1, inplace=True)
            return filtered_df
        
        return pd.DataFrame()
    
    def _format_resilience_data(self, resilience_df: pd.DataFrame) -> dict:
        """Format resilience data into lookup by date."""
        resilience_by_date = {}
        for _, row in resilience_df.iterrows():
            date_key = row['date']
            # Convert YYYY-MM-DD to MM-DD format
            if len(date_key) == 10:  # YYYY-MM-DD format
                date_key = date_key[5:]  # Extract MM-DD part
            resilience_by_date[date_key] = {
                'resilience_score': row['resilience_score'],
                'resilience_level': row['resilience_level']
            }
        return resilience_by_date
        
    def recovery_metrics(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get recovery metrics for date range.
        
        Steps:
        1. Create base DataFrame with date range
        2. Get recovery data for date range
        3. Get resilience data from Oura
        4. Format recovery and resilience data into lookups
        5. Update base DataFrame with metrics
        6. (Weight data removed - now only in macros dataframe)
        
        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with columns:
            - date: Date of the metrics (MM-DD)
            - day: Three letter day name
            - recovery: Recovery score (0-100)
            - resilience_level: Resilience level from Oura (text)
            - hrv: Heart rate variability in ms
            - hr: Resting heart rate in bpm
            - sleep_need: Hours of sleep needed
            - sleep_actual: Actual hours of sleep
        """
        # Step 1: Create base DataFrame
        df = self._create_date_range_df(start_date, end_date)
        
        # Step 2: Get recovery data
        recovery_df = self._get_filtered_recovery_data(start_date, end_date)
        
        # Step 3: Get resilience data
        resilience_df = self._get_filtered_resilience_data(start_date, end_date)
        
        # Step 4: Format data into lookups
        recovery_by_date = {}
        if not recovery_df.empty:
            recovery_by_date = self._format_recovery_data(recovery_df)
            
        resilience_by_date = {}
        if not resilience_df.empty:
            resilience_by_date = self._format_resilience_data(resilience_df)
        
        # Step 5: Update metrics
        df = self._update_recovery_metrics(df, recovery_by_date)
        
        # Add resilience level data if available (only include level, not score)
        if resilience_by_date:
            df['resilience_level'] = df['date'].map(lambda x: resilience_by_date.get(x, {}).get('resilience_level'))
        
        # Step 6: Weight data removed - now only in macros dataframe
        # df = self._add_weight_data(df, start_date, end_date)
            
        # Log the final DataFrame in debug mode
        from src.utils.logging_utils import DEBUG_MODE
        if DEBUG_MODE and hasattr(self, 'logger') and hasattr(self.logger, 'debug_dataframe'):
            self.logger.debug_dataframe(df, "Post-Aggregation Recovery Metrics")
        
        return df
    
    def training_metrics(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
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
        date_df = self._create_date_range_df(start_date, end_date)
        
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
            date = row['date']
            day = row['day']
            
            if date in workout_by_date and workout_by_date[date]['workouts']:
                # Add each workout for this date
                for workout in workout_by_date[date]['workouts']:
                    if workout['sport'] not in AnalyzerConfig.EXCLUDED_SPORTS and workout['sport'] != 'Rest':
                        all_workouts.append({
                            'date': date,
                            'day': day,
                            'sport': workout['sport'],
                            'duration': workout['duration'],
                            'strain': workout['strain']
                        })
        
        # Create DataFrame from all workouts
        if all_workouts:
            df = pd.DataFrame(all_workouts)
        else:
            df = pd.DataFrame(columns=['date', 'day', 'sport', 'duration', 'strain'])
            
        # Log the final DataFrame in debug mode
        from src.utils.logging_utils import DEBUG_MODE
        if DEBUG_MODE and hasattr(self, 'logger') and hasattr(self.logger, 'debug_dataframe'):
            self.logger.debug_dataframe(df, "Post-Aggregation Training Metrics")
            
        return df
    
    def _get_filtered_nutrition_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get nutrition data filtered to date range."""
        df = self.processor.nutrition.load_data()
        
        # Filter to date range
        df = df[
            (df['date'] >= start_date) & 
            (df['date'] <= end_date)
        ]
        
        # Fill missing values
        df = df.fillna({
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        })
        
        # Round numeric values
        for col in ['calories', 'protein', 'carbs', 'fat']:
            df[col] = df[col].round(1)
            
        return df
    
    def _add_steps_data(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Add steps data to DataFrame."""
        if self.processor.oura_data is None:
            df['steps'] = 0
            return df
            
        # Handle the new Oura data structure
        if isinstance(self.processor.oura_data, dict) and 'activity' in self.processor.oura_data:
            oura_df = self.processor.oura_data['activity'].copy()
            
            # Check if we have data
            if oura_df.empty:
                df['steps'] = 0
                return df
                
            # Convert dates for comparison
            oura_df['date'] = pd.to_datetime(oura_df['date'])
            
            # Filter to date range
            oura_df = oura_df[
                (oura_df['date'] >= start_date) & 
                (oura_df['date'] <= end_date)
            ]
            
            # Create steps lookup by date
            steps_by_date = {}
            for _, row in oura_df.iterrows():
                date_key = row['date'].strftime('%m-%d')
                steps_by_date[date_key] = row['steps']
            
            # Add steps to DataFrame
            df['steps'] = df['date'].map(steps_by_date).fillna(0).astype(int)
        else:
            # Fallback for old data structure or empty data
            df['steps'] = 0
        
        return df
    
    def _add_activity_data(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Add activity data to DataFrame."""
        # Default to Rest if no workout data available
        df['activity'] = 'Rest'
        
        # Early return if no workout data
        if self.processor.whoop_data is None or 'workouts' not in self.processor.whoop_data:
            return df
            
        # Filter to date range
        workout_df = self.processor.whoop_data['workouts'][
            (self.processor.whoop_data['workouts']['date'].dt.date >= start_date.date()) & 
            (self.processor.whoop_data['workouts']['date'].dt.date <= end_date.date())
        ]
        
        # Debug logging setup
        from src.utils.logging_utils import DEBUG_MODE
        
        # Track best workout for each date
        best_workouts = {}
        
        # Process each workout
        for _, row in workout_df.iterrows():
            date_key = row['date'].strftime('%m-%d')
            sport = row['sport']
            strain = row['strain']
            
            # Categorize the sport
            if sport in AnalyzerConfig.EXCLUDED_SPORTS:
                activity_type = 'Rest'
                priority = 0  # Lowest priority
            elif sport in AnalyzerConfig.STRENGTH_ACTIVITIES:
                activity_type = 'Strength'
                priority = 2  # Highest priority
            else:
                activity_type = 'Cardio'
                priority = 1  # Medium priority
            
            # Check if we should update the best workout for this date
            current = best_workouts.get(date_key, {'priority': -1, 'strain': -1})
            
            # Update if: higher priority or same priority but higher strain
            if priority > current['priority'] or (priority == current['priority'] and strain > current['strain']):
                best_workouts[date_key] = {
                    'sport': activity_type,
                    'strain': strain,
                    'priority': priority
                }
        
        # Update DataFrame with best activities
        for date_key, workout in best_workouts.items():
            df.loc[df['date'] == date_key, 'activity'] = workout['sport']
        
        return df
        
    def _add_weight_data(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Add weight data to DataFrame.
        
        Args:
            df: DataFrame to add weight data to
            start_date: Start date for filtering data
            end_date: End date for filtering data
            
        Returns:
            DataFrame with weight data added
        """
        # Default to no weight data
        df['weight'] = None
        
        # Early return if no Withings data available
        if self.processor.withings_data is None or 'weight' not in self.processor.withings_data:
            return df
            
        # Get weight data
        weight_df = self.processor.withings_data['weight']
        
        # Create weight lookup by date
        weight_by_date = {}
        for _, row in weight_df.iterrows():
            if 'date' in row and 'weight' in row:
                weight_by_date[row['date']] = row['weight']
        
        # Update DataFrame with weight data
        for date in df['date']:
            if date in weight_by_date:
                df.loc[df['date'] == date, 'weight'] = weight_by_date[date]
        
        # Format weight values using the configured precision
        from .analyzer_config import AnalyzerConfig
        weight_precision = AnalyzerConfig.NUMERIC_PRECISION.get('weight', 1)
        df['weight'] = df['weight'].apply(
            lambda x: round(float(x), weight_precision) if not pd.isna(x) and x != '-' else None
        )
        
        return df
    
    def weekly_macros_and_activity(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
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
            - activity: Sport name or 'Rest'
            - steps: Daily step count
            - weight: Weight in pounds (if available)
        """
        # Step 1: Create base DataFrame with date range
        df = self._create_date_range_df(start_date, end_date)
        
        # Step 2: Get nutrition data
        nutrition_df = self._get_filtered_nutrition_data(start_date, end_date)
        
        # Create lookup by date string (MM-DD)
        nutrition_by_date = {}
        for _, row in nutrition_df.iterrows():
            date_key = row['date'].strftime('%m-%d')
            nutrition_by_date[date_key] = {
                'calories': row['calories'],
                'protein': row['protein'],
                'carbs': row['carbs'],
                'fat': row['fat']
            }
        
        # Set default values
        df['calories'] = 0
        df['protein'] = 0
        df['carbs'] = 0
        df['fat'] = 0
        
        # Update with actual values
        for date in df['date']:
            if date in nutrition_by_date:
                df.loc[df['date'] == date, 'calories'] = nutrition_by_date[date]['calories']
                df.loc[df['date'] == date, 'protein'] = nutrition_by_date[date]['protein']
                df.loc[df['date'] == date, 'carbs'] = nutrition_by_date[date]['carbs']
                df.loc[df['date'] == date, 'fat'] = nutrition_by_date[date]['fat']
        
        # Step 3: Add steps data
        df = self._add_steps_data(df, start_date, end_date)
        
        # Step 4: Add activity data
        df = self._add_activity_data(df, start_date, end_date)
        
        # Step 5: Add weight data
        df = self._add_weight_data(df, start_date, end_date)
        
        # Step 6: Format output
        columns = ['date', 'day', 'calories', 'protein', 'carbs', 'fat', 'activity', 'steps']
        if 'weight' in df.columns:
            columns.append('weight')
        df = df[columns]
        
        # Log the final DataFrame in debug mode
        from src.utils.logging_utils import DEBUG_MODE
        if DEBUG_MODE and hasattr(self, 'logger') and hasattr(self.logger, 'debug_dataframe'):
            self.logger.debug_dataframe(df, "Post-Aggregation Macros and Activity")
        
        return df
