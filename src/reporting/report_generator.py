"""Module for generating formatted health and fitness reports."""
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any, Optional, List

from src.analysis.metrics_aggregator import MetricsAggregator
from src.analysis.analyzer_config import AnalyzerConfig
from .chart_generator import RecoveryChartGenerator, MacroRatioChartGenerator, NutritionChartGenerator, WeightChartGenerator
from .resilience_chart_generator import ResilienceChartGenerator
from .reporting_config import ReportingConfig

class ReportGenerator:
    def __init__(self, analyzer: MetricsAggregator):
        """Initialize ReportGenerator.
        
        Args:
            analyzer: MetricsAggregator instance to use for metrics generation
        """
        self.analyzer = analyzer
    
    def _format_number(self, value, decimal_places=1, integer_columns=None):
        """Format a number with consistent decimal places.
        
        Args:
            value: The number to format
            decimal_places: Number of decimal places to display
            integer_columns: List of column names that should be displayed as integers
            
        Returns:
            Formatted string representation of the number
        """
        if pd.isna(value):
            return '-'
            
        # Check if this is a column that should be displayed as an integer
        if integer_columns and hasattr(value, 'name') and value.name in integer_columns:
            return f"{int(value)}"
            
        # Format with specified decimal places
        return f"{float(value):.{decimal_places}f}"
    
    def _df_to_markdown(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to markdown table format.
        
        Ensures consistent formatting of numeric values before conversion.
        Replaces all NaN values with a dash (-).
        """
        # Create a copy to avoid modifying the original DataFrame
        formatted_df = df.copy()
        
        # Define columns that should be displayed as integers
        integer_columns = ['CALORIES', 'STEPS']
        
        # First, replace all NaN values with a dash
        formatted_df = formatted_df.fillna('-')
        
        # For each column, ensure consistent string formatting
        for col in formatted_df.columns:
            # Skip non-numeric columns, special columns, and columns that are already dashes
            if formatted_df[col].dtype.kind not in 'ifc' or col in ['recovery', 'RECOVERY']:
                continue
            
            # Convert to numeric and apply consistent formatting
            formatted_df[col] = pd.to_numeric(formatted_df[col], errors='ignore')
            if formatted_df[col].dtype.kind in 'ifc':
                # Use vectorized operations for better performance
                is_integer_col = col in integer_columns
                if is_integer_col:
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"{int(x)}" if pd.notnull(x) and x != '-' else '-'
                    )
                else:
                    # Format with one decimal place
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"{float(x):.1f}" if pd.notnull(x) and x != '-' else '-'
                    )
        
        # Use pandas to_markdown with consistent formatting
        # floatfmt parameter ensures consistent decimal places for all numeric values
        return formatted_df.to_markdown(index=False, numalign='right', floatfmt='.1f')
        
    def _merge_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge date and day columns into a single column.
        
        Args:
            df: DataFrame with 'date' and 'day' columns
            
        Returns:
            DataFrame with merged 'date' column in format 'MM-DD (day)'
        """
        if 'date' in df.columns and 'day' in df.columns:
            df = df.copy()
            df['date'] = df.apply(lambda row: f"{row['date']} ({row['day']})", axis=1)
            df = df.drop(columns=['day'])
            # Rename date column to uppercase
            df = df.rename(columns={'date': 'DATE'})
        return df
    
    @staticmethod
    def _get_recovery_class(score: float) -> str:
        """Get recovery class based on score using thresholds from ReportingConfig.
        
        Args:
            score: Recovery score (0-100)
            
        Returns:
            Class name: 'recovery-low', 'recovery-medium', or 'recovery-high'
            based on thresholds defined in ReportingConfig
        """
        score = float(score)
        if score <= ReportingConfig.THRESHOLDS['recovery_low']:
            return 'recovery-low'
        elif score <= ReportingConfig.THRESHOLDS['recovery_medium'] + 31:  # 34 + 31 = 65
            return 'recovery-medium'
        else:
            return 'recovery-high'
    
    def _format_recovery_score(self, score: Any) -> str:
        """Format recovery score with color coding.
        
        Args:
            score: Recovery score (0-100) or '-' for missing data
            
        Returns:
            Markdown formatted score with HTML class
            - recovery-low (0-33)
            - recovery-medium (34-65)
            - recovery-high (66-100)
        """
        if score is None or score == '-' or pd.isna(score):
            return '-'
        if isinstance(score, str) and '<span class=' in score:
            return score
        score = float(score)
        return f'<span class="{self._get_recovery_class(score)}">{score:.0f}</span>'
        
    def _format_macros_table(self, macros_df: pd.DataFrame) -> pd.DataFrame:
        """Format macros data into a markdown-ready DataFrame.
        
        Args:
            macros_df: Raw macros DataFrame
            
        Returns:
            Formatted DataFrame ready for markdown conversion
        """
        # Simply pass through to _df_to_markdown which now handles all formatting
        formatted = macros_df.copy()
        formatted = formatted.rename(columns={
            'calories': 'CALORIES',
            'protein': 'PROTEIN',
            'carbs': 'CARBS',
            'fat': 'FAT',
            'steps': 'STEPS',
            'activity': 'ACTIVITY'
        })
        return self._merge_date_columns(formatted)
    
    def _format_recovery_table(self, recovery_df: pd.DataFrame) -> pd.DataFrame:
        """Format recovery data into a markdown-ready DataFrame.
        
        Args:
            recovery_df: Raw recovery DataFrame
            
        Returns:
            Formatted DataFrame ready for markdown conversion
        """
        formatted = recovery_df.copy()
        
        # Special formatting for recovery score only - other numeric columns handled by _df_to_markdown
        formatted['recovery'] = formatted['recovery'].apply(lambda x: self._format_recovery_score(x) if pd.notnull(x) else '-')
        # Keep the special formatting when renaming to uppercase
        formatted = formatted.rename(columns={
            'sleep_need': 'SLEEP NEED',
            'sleep_actual': 'SLEEP ACTUAL',
            'resilience_level': 'RES',
            'recovery': 'RECOVERY',
            'hrv': 'HRV',
            'hr': 'HR'
        })
        return self._merge_date_columns(formatted)
    
    def _format_training_table(self, training_df: pd.DataFrame) -> pd.DataFrame:
        """Format training data into a markdown-ready DataFrame.
        
        Args:
            training_df: Raw training DataFrame
            
        Returns:
            Formatted DataFrame ready for markdown conversion
        """
        if training_df.empty:
            return training_df
        formatted = training_df.copy()
        # Rename columns to uppercase
        formatted = formatted.rename(columns={
            'sport': 'SPORT',
            'duration': 'DURATION',
            'strain': 'STRAIN'
        })
        return self._merge_date_columns(formatted)
    
    def _generate_recovery_chart(self, recovery_df: pd.DataFrame, filename: str = "recovery_chart.png") -> Optional[str]:
        """Generate a recovery chart image and return markdown for embedding.
        
        Args:
            recovery_df: DataFrame containing recovery data
            filename: Output filename for the chart
            
        Returns:
            Markdown string for embedding the chart, or None if generation fails
        """
        try:
            chart_gen = RecoveryChartGenerator()
            
            # Include sleep data columns if they exist
            columns_to_include = ['date', 'recovery']
            if 'sleep_need' in recovery_df.columns:
                columns_to_include.append('sleep_need')
            if 'sleep_actual' in recovery_df.columns:
                columns_to_include.append('sleep_actual')
                
            chart_df = recovery_df[columns_to_include].dropna(subset=['recovery'])
            chart_path = chart_gen.generate(chart_df, filename=filename)
            return f"![Recovery Chart](charts/recovery_chart.png)\n" if chart_path else None
        except Exception as e:
            # Could log the error here
            print(f"Error generating recovery chart: {e}")
            return None
            
    def _generate_resilience_chart(self, recovery_df: pd.DataFrame, filename: str = "resilience_chart.png") -> Optional[str]:
        """Generate a resilience chart image and return markdown for embedding.
        
        Args:
            recovery_df: DataFrame containing recovery and resilience data
            filename: Output filename for the chart
            
        Returns:
            Markdown string for embedding the chart, or None if generation fails
        """
        try:
            chart_gen = ResilienceChartGenerator()
            
            # Create a copy of the dataframe for the chart
            chart_df = recovery_df[['date', 'resilience_level']].copy()
            
            # Calculate midpoints between thresholds for better visual positioning
            level_to_score = {}
            
            # Get the thresholds from analyzer_config
            thresholds = AnalyzerConfig.RESILIENCE_LEVEL_SCORES
            
            # Calculate midpoints for main levels
            level_to_score['exceptional'] = (thresholds['exceptional'] + 100) / 2  # Between exceptional and max
            level_to_score['strong'] = (thresholds['strong'] + thresholds['exceptional']) / 2  # Between strong and exceptional
            level_to_score['solid'] = (thresholds['solid'] + thresholds['strong']) / 2  # Between solid and strong
            level_to_score['adequate'] = (thresholds['adequate'] + thresholds['solid']) / 2  # Between adequate and solid
            level_to_score['limited'] = (thresholds['limited'] + thresholds['adequate']) / 2  # Between limited and adequate
            
            # Add mappings for legacy levels
            level_to_score['weak'] = (thresholds['adequate'] + thresholds['limited']) / 2  # Between limited and adequate
            level_to_score['compromised'] = (thresholds['adequate'] + thresholds['limited']) / 2  # Same as weak
            level_to_score['low'] = thresholds['limited'] + 10  # Just above limited
            
            # Add resilience_score based on the level
            chart_df['resilience_score'] = chart_df['resilience_level'].apply(
                lambda x: level_to_score.get(x.lower(), level_to_score['solid']) if pd.notnull(x) else level_to_score['solid']
            )
                
            chart_path = chart_gen.generate(chart_df, filename=filename)
            return f"![Resilience Chart](charts/{filename})\n" if chart_path else None
        except Exception as e:
            # Could log the error here
            print(f"Error generating resilience chart: {e}")
            return None
            
    def _generate_nutrition_chart(self, macros_df: pd.DataFrame, filename: str = "nutrition_chart.png") -> Optional[str]:
        """Generate a nutrition chart image and return markdown for embedding.
        
        Args:
            macros_df: DataFrame containing nutrition data
            filename: Output filename for the chart
            
        Returns:
            Markdown string for embedding the chart, or None if generation fails
        """
        try:
            # Create chart generator with configurable targets from config
            chart_gen = NutritionChartGenerator(
                target_strength=ReportingConfig.CALORIC_TARGETS['strength'],
                target_rest=ReportingConfig.CALORIC_TARGETS['rest']
            )
            
            # If activity column doesn't exist, create it based on training type
            if 'activity' not in macros_df.columns:
                if 'training' in macros_df.columns:
                    macros_df['activity'] = macros_df['training'].apply(
                        lambda x: 'Strength' if x in AnalyzerConfig.STRENGTH_ACTIVITIES else 'Rest'
                    )
                else:
                    # Default to Rest if no training info
                    macros_df['activity'] = 'Rest'
            
            # Check if we have macronutrient data for a stacked chart
            has_macro_data = {'protein', 'carbs', 'fat'}.issubset(macros_df.columns)
            
            if has_macro_data:
                # Use the stacked chart with macronutrient breakdown
                chart_df = macros_df[['date', 'protein', 'carbs', 'fat', 'activity']].copy()
                
                # Skip days with no data
                chart_df = chart_df[(chart_df['protein'] > 0) | (chart_df['carbs'] > 0) | (chart_df['fat'] > 0)]
                
                # Generate stacked chart
                stacked_filename = "stacked_" + filename
                chart_path = chart_gen.generate_stacked(chart_df, filename=stacked_filename)
                return f"![Nutrition Chart](charts/{stacked_filename})\n" if chart_path else None
            else:
                # Use the simple chart with just calories
                if 'calories' not in macros_df.columns:
                    return None
                    
                chart_df = macros_df[['date', 'calories', 'activity']].copy()
                
                # Generate simple chart
                chart_path = chart_gen.generate(chart_df, filename=filename)
                return f"![Nutrition Chart](charts/{filename})\n" if chart_path else None
        except Exception as e:
            # Could log the error here
            print(f"Error generating nutrition chart: {e}")
            return None
    
    def _generate_weight_chart(self, df: pd.DataFrame, filename: str = "weight_chart.png") -> Optional[str]:
        """Generate weight chart from DataFrame with weight data.
        
        Args:
            df: DataFrame with weight data
            filename: Output filename for the chart
            
        Returns:
            Markdown image tag for the chart, or None if chart generation failed
        """
        try:
            # Check if we have weight data
            if 'weight' not in df.columns or df['weight'].isna().all():
                return None
                
            # Create chart generator
            chart_gen = WeightChartGenerator()
            
            # Create a copy of the DataFrame with just date and weight
            chart_df = df[['date', 'weight']].copy()
            
            # Generate weight chart
            chart_path = chart_gen.generate(chart_df, filename=filename)
            return f"![Weight Chart](charts/{filename})\n" if chart_path else None
        except Exception as e:
            # Could log the error here
            print(f"Error generating weight chart: {e}")
            return None
    
    def generate_weekly_status(self, start_date: datetime = None, end_date: datetime = None) -> str:
        """Generate weekly status report in markdown format.
        
        Args:
            start_date: Start date for the report period (default: 7 days ago)
            end_date: End date for the report period (default: today)
            
        Returns:
            Markdown formatted report with sections for:
            - Summary
            - Weekly Macronutrients and Activity
            - Recovery Metrics
            - Training
        """
        logger = getattr(self.analyzer, 'logger', None)
        
        #----------------------------------------------------------------------
        # 1. DATA COLLECTION AND PREPARATION
        #----------------------------------------------------------------------
        
        # Set default date range if not provided
        if end_date is None:
            end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if start_date is None:
            start_date = end_date - timedelta(days=7)
            
        # Fetch all raw data from analyzer
        # Process macros and activity data
        macros_df = self.analyzer.weekly_macros_and_activity(start_date, end_date)

        
        # Process recovery metrics
        recovery_df = self.analyzer.recovery_metrics(start_date, end_date)

        
        # Process training metrics
        training_df = self.analyzer.training_metrics(start_date, end_date)

        
        # Calculate summary metrics
        active_days = macros_df[macros_df['calories'] > 0]
        total_calories = active_days['calories'].sum() if len(active_days) > 0 else 0
        avg_protein = active_days['protein'].mean() if len(active_days) > 0 else 0
        
        # Count strength days using the STRENGTH_ACTIVITIES list from AnalyzerConfig
        strength_days = len(training_df[training_df['sport'].isin(AnalyzerConfig.STRENGTH_ACTIVITIES)])
        
        # Calculate macronutrient ratios
        macro_ratios = None
        if len(active_days) > 0:
            # Calculate calorie contributions
            protein_cals = active_days['protein'].sum() * 4  # 4 calories per gram of protein
            carbs_cals = active_days['carbs'].sum() * 4     # 4 calories per gram of carbs
            fat_cals = active_days['fat'].sum() * 9        # 9 calories per gram of fat
            total_calories = active_days['calories'].sum()
            
            if total_calories > 0:
                macro_ratios = {
                    'protein_pct': protein_cals / total_calories * 100,
                    'carbs_pct': carbs_cals / total_calories * 100,
                    'fat_pct': fat_cals / total_calories * 100
                }
        
        # Get report date range for title
        report_start = training_df['date'].iloc[0] if len(training_df) > 0 else 'No data'
        report_end = training_df['date'].iloc[-1] if len(training_df) > 0 else 'No data'
        
        #----------------------------------------------------------------------
        # 2. DATA FORMATTING AND VISUALIZATION
        #----------------------------------------------------------------------
        
        # Format tables using helper methods
        formatted_macros = self._format_macros_table(macros_df)
        macros_table = self._df_to_markdown(formatted_macros)
        
        formatted_recovery = self._format_recovery_table(recovery_df)
        recovery_table = self._df_to_markdown(formatted_recovery)
        
        formatted_training = self._format_training_table(training_df)
        if not formatted_training.empty:
            training_table = self._df_to_markdown(formatted_training)
        else:
            training_table = "No training data available for this period."
        
        # Generate charts
        recovery_chart = self._generate_recovery_chart(recovery_df)
        resilience_chart = self._generate_resilience_chart(recovery_df)
        nutrition_chart = self._generate_nutrition_chart(macros_df)
        weight_chart = self._generate_weight_chart(macros_df)
        
        #----------------------------------------------------------------------
        # 3. MARKDOWN ASSEMBLY USING TEMPLATE
        #----------------------------------------------------------------------
        
        # Generate macro ratio HTML if available
        macro_html = ""
        if macro_ratios:
            macro_chart_gen = MacroRatioChartGenerator()
            macro_html = macro_chart_gen.generate_html(
                macro_ratios['protein_pct'],
                macro_ratios['carbs_pct'],
                macro_ratios['fat_pct']
            )
        
        # Format the report using a template
        report_template = f"""\
# Weekly Report for {report_start} to {report_end}

## Summary

**Key Metrics**:

- Weekly Total Calories: {total_calories:,.0f} kcal
- Average Protein: {avg_protein:.1f}g
- Strength Training Days: {strength_days}

## Weekly Macronutrients and Activity

{nutrition_chart if nutrition_chart else ''}

{weight_chart if weight_chart else ''}

{macros_table}

{macro_html}

## Recovery Metrics

{recovery_chart if recovery_chart else ''}
{resilience_chart if resilience_chart else ''}
{recovery_table}

## Training Log

{training_table}
"""
        
        return report_template
        
    # Helper methods for building report sections have been removed
    # as they are now replaced by the template-based approach
