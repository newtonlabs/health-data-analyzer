"""Module for generating formatted health and fitness reports."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from src.analysis.analyzer_config import AnalyzerConfig
from src.analysis.metrics_aggregator import MetricsAggregator

from .chart_generator import ChartGenerator
from .macro_ratio_chart_generator import MacroRatioChartGenerator
from .nutrition_chart_generator import NutritionChartGenerator
from .recovery_chart_generator import RecoveryChartGenerator
from .reporting_config import ReportingConfig
from .resilience_chart_generator import ResilienceChartGenerator


class ReportGenerator:
    def __init__(self, analyzer: MetricsAggregator):
        """Initialize ReportGenerator.

        Args:
            analyzer: MetricsAggregator instance to use for metrics generation
        """
        self.analyzer = analyzer

    def _df_to_markdown(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to markdown table format.

        Ensures consistent formatting of numeric values before conversion.
        Replaces all NaN values with a dash (-).
        """
        # Create a copy to avoid modifying the original DataFrame
        formatted_df = df.copy()

        # Define columns that should be displayed as integers
        integer_columns = ["CALORIES", "STEPS"]

        # First, replace all NaN values with a dash
        formatted_df = formatted_df.fillna("-")

        # For each column, ensure consistent string formatting
        for col in formatted_df.columns:
            # Skip non-numeric columns, special columns, and columns that are already dashes
            if formatted_df[col].dtype.kind not in "ifc" or col in [
                "recovery",
                "RECOVERY",
            ]:
                continue

            # Convert to numeric and apply consistent formatting
            formatted_df[col] = pd.to_numeric(formatted_df[col], errors="ignore")
            if formatted_df[col].dtype.kind in "ifc":
                # Use vectorized operations for better performance
                is_integer_col = col in integer_columns
                if is_integer_col:
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"{int(x)}" if pd.notnull(x) and x != "-" else "-"
                    )
                else:
                    # Format with one decimal place
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: (
                            f"{float(x):.1f}" if pd.notnull(x) and x != "-" else "-"
                        )
                    )

        # Convert to markdown with pandas to_markdown
        # floatfmt parameter ensures consistent decimal places for all numeric values
        # Set column alignment - right-align numeric columns including WEIGHT
        colalign = ["left"] * len(formatted_df.columns)
        for i, col in enumerate(formatted_df.columns):
            if col in ["CALORIES", "PROTEIN", "CARBS", "FAT", "STEPS", "WEIGHT"]:
                colalign[i] = "right"

        md_table = formatted_df.to_markdown(
            index=False, numalign="right", floatfmt=".1f", colalign=colalign
        )

        # Return the markdown table directly - styling is applied in html_templates.py
        return md_table

    def _merge_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge date and day columns into a single column.

        Args:
            df: DataFrame with 'date' and 'day' columns

        Returns:
            DataFrame with merged 'date' column in format 'MM-DD (day)'
        """
        if "date" in df.columns and "day" in df.columns:
            df = df.copy()
            df["date"] = df.apply(lambda row: f"{row['date']} ({row['day']})", axis=1)
            df = df.drop(columns=["day"])
            # Rename date column to uppercase
            df = df.rename(columns={"date": "DATE"})
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
        if score <= ReportingConfig.THRESHOLDS["recovery_low"]:
            return "recovery-low"
        elif score < ReportingConfig.THRESHOLDS["recovery_high"]:
            return "recovery-medium"
        else:
            return "recovery-high"

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
        if score is None or score == "-" or pd.isna(score):
            return "-"
        if isinstance(score, str) and "<span class=" in score:
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
        formatted = formatted.rename(
            columns={
                "calories": "CALORIES",
                "protein": "PROTEIN",
                "carbs": "CARBS",
                "fat": "FAT",
                "steps": "STEPS",
                "activity": "ACTIVITY",
                "weight": "WEIGHT",
            }
        )
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
        formatted["recovery"] = formatted["recovery"].apply(
            lambda x: self._format_recovery_score(x) if pd.notnull(x) else "-"
        )
        # Keep the special formatting when renaming to uppercase
        formatted = formatted.rename(
            columns={
                "sleep_need": "SLEEP NEED",
                "sleep_actual": "SLEEP ACTUAL",
                "resilience_level": "RES",
                "recovery": "RECOVERY",
                "hrv": "HRV",
                "hr": "HR",
            }
        )
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
        formatted = formatted.rename(
            columns={"sport": "SPORT", "duration": "DURATION", "strain": "STRAIN"}
        )
        return self._merge_date_columns(formatted)

    def _generate_chart_markdown(
        self,
        chart_generator_class,
        df: pd.DataFrame,
        filename: str,
        chart_type_name: str,
        **kwargs,
    ) -> Optional[str]:
        """Generic helper to generate a chart and return its markdown string."""
        try:
            chart_gen = chart_generator_class(**kwargs)
            chart_path = chart_gen.generate(df, filename=filename)
            if chart_path:
                # Extract relative path from charts_dir to ensure correct markdown path
                # Instantiate a ChartGenerator to get the default charts_dir
                base_chart_gen = ChartGenerator()
                relative_chart_path = os.path.relpath(
                    chart_path, base_chart_gen.charts_dir
                )
                return f"![{chart_type_name} Chart](charts/{relative_chart_path})\n"
            return None
        except Exception as e:
            self.logger.error(f"Error generating {chart_type_name} chart: {e}")
            return None

    def _generate_recovery_chart(
        self, recovery_df: pd.DataFrame, filename: str = "recovery_chart.png"
    ) -> Optional[str]:
        """Generate a recovery chart image and return markdown for embedding.

        Args:
            recovery_df: DataFrame containing recovery data
            filename: Output filename for the chart

        Returns:
            Markdown string for embedding the chart, or None if generation fails
        """
        # Include sleep data columns if they exist
        columns_to_include = ["date", "recovery"]
        if "sleep_need" in recovery_df.columns:
            columns_to_include.append("sleep_need")
        if "sleep_actual" in recovery_df.columns:
            columns_to_include.append("sleep_actual")

        chart_df = recovery_df[columns_to_include].dropna(subset=["recovery"])

        return self._generate_chart_markdown(
            chart_generator_class=RecoveryChartGenerator,
            df=chart_df,
            filename=filename,
            chart_type_name="Recovery",
        )

    def _generate_resilience_chart(
        self, recovery_df: pd.DataFrame, filename: str = "resilience_chart.png"
    ) -> Optional[str]:
        """Generate a resilience chart image and return markdown for embedding.

        Args:
            recovery_df: DataFrame containing recovery and resilience data
            filename: Output filename for the chart

        Returns:
            Markdown string for embedding the chart, or None if generation fails
        """
        # Create a copy of the dataframe for the chart
        chart_df = recovery_df[["date", "resilience_level"]].copy()

        # Calculate midpoints between thresholds for better visual positioning
        level_to_score = {}

        # Get the thresholds from analyzer_config
        thresholds = AnalyzerConfig.RESILIENCE_LEVEL_SCORES

        # Calculate midpoints for main levels
        level_to_score["exceptional"] = (
            thresholds["exceptional"] + 100
        ) / 2  # Between exceptional and max
        level_to_score["strong"] = (
            thresholds["strong"] + thresholds["exceptional"]
        ) / 2  # Between strong and exceptional
        level_to_score["solid"] = (
            thresholds["solid"] + thresholds["strong"]
        ) / 2  # Between solid and strong
        level_to_score["adequate"] = (
            thresholds["adequate"] + thresholds["solid"]
        ) / 2  # Between adequate and solid
        level_to_score["limited"] = (
            thresholds["limited"] + thresholds["adequate"]
        ) / 2  # Between limited and adequate

        # Add mappings for legacy levels
        level_to_score["weak"] = (
            thresholds["adequate"] + thresholds["limited"]
        ) / 2  # Between limited and adequate
        level_to_score["compromised"] = (
            thresholds["adequate"] + thresholds["limited"]
        ) / 2  # Same as weak
        level_to_score["low"] = thresholds["limited"] + 10  # Just above limited

        # Add resilience_score based on the level
        chart_df["resilience_score"] = chart_df["resilience_level"].apply(
            lambda x: (
                level_to_score.get(x.lower(), level_to_score["solid"])
                if pd.notnull(x)
                else level_to_score["solid"]
            )
        )

        return self._generate_chart_markdown(
            chart_generator_class=ResilienceChartGenerator,
            df=chart_df,
            filename=filename,
            chart_type_name="Resilience",
        )

    def _generate_nutrition_chart(
        self, macros_df: pd.DataFrame, filename: str = "nutrition_chart.png"
    ) -> Optional[str]:
        """Generate a nutrition chart image and return markdown for embedding.

        Args:
            macros_df: DataFrame containing nutrition data
            filename: Output filename for the chart

        Returns:
            Markdown string for embedding the chart, or None if generation fails
        """
        # If activity column doesn't exist, create it based on training type
        if "activity" not in macros_df.columns:
            if "training" in macros_df.columns:
                macros_df["activity"] = macros_df["training"].apply(
                    lambda x: (
                        "Strength"
                        if x in AnalyzerConfig.STRENGTH_ACTIVITIES
                        else "Rest"
                    )
                )
            else:
                # Default to Rest if no training info
                macros_df["activity"] = "Rest"

        # Check if we have macronutrient data for a stacked chart
        has_macro_data = {"protein", "carbs", "fat"}.issubset(macros_df.columns)

        if has_macro_data:
            # Use the stacked chart with macronutrient breakdown
            # Include weight data if available
            if "weight" in macros_df.columns:
                chart_df = macros_df[
                    ["date", "protein", "carbs", "fat", "activity", "weight"]
                ].copy()
            else:
                chart_df = macros_df[
                    ["date", "protein", "carbs", "fat", "activity"]
                ].copy()

            # Skip days with no data
            chart_df = chart_df[
                (chart_df["protein"] > 0)
                | (chart_df["carbs"] > 0)
                | (chart_df["fat"] > 0)
            ]

            stacked_filename = "stacked_" + filename
            return self._generate_chart_markdown(
                chart_generator_class=NutritionChartGenerator,
                df=chart_df,
                filename=stacked_filename,
                chart_type_name="Nutrition",
                target_strength=ReportingConfig.CALORIC_TARGETS["strength"],
                target_rest=ReportingConfig.CALORIC_TARGETS["rest"],
            )
        else:
            # Use the simple chart with just calories
            if "calories" not in macros_df.columns:
                return None

            chart_df = macros_df[["date", "calories", "activity"]].copy()

            return self._generate_chart_markdown(
                chart_generator_class=NutritionChartGenerator,
                df=chart_df,
                filename=filename,
                chart_type_name="Nutrition",
                target_strength=ReportingConfig.CALORIC_TARGETS["strength"],
                target_rest=ReportingConfig.CALORIC_TARGETS["rest"],
            )

    def generate_weekly_status(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> str:
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
        logger = getattr(self.analyzer, "logger", None)

        # ----------------------------------------------------------------------
        # 1. DATA COLLECTION AND PREPARATION
        # ----------------------------------------------------------------------

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
        active_days = macros_df[macros_df["calories"] > 0]
        total_calories = active_days["calories"].sum() if len(active_days) > 0 else 0
        avg_protein = active_days["protein"].mean() if len(active_days) > 0 else 0

        # Count strength days using the STRENGTH_ACTIVITIES list from AnalyzerConfig
        strength_days = len(
            training_df[training_df["sport"].isin(AnalyzerConfig.STRENGTH_ACTIVITIES)]
        )

        # Calculate macronutrient ratios
        macro_ratios = None
        if len(active_days) > 0:
            # Calculate calorie contributions
            protein_cals = (
                active_days["protein"].sum() * 4
            )  # 4 calories per gram of protein
            carbs_cals = active_days["carbs"].sum() * 4  # 4 calories per gram of carbs
            fat_cals = active_days["fat"].sum() * 9  # 9 calories per gram of fat
            total_calories = active_days["calories"].sum()

            if total_calories > 0:
                macro_ratios = {
                    "protein_pct": protein_cals / total_calories * 100,
                    "carbs_pct": carbs_cals / total_calories * 100,
                    "fat_pct": fat_cals / total_calories * 100,
                }

        # Get report date range for title
        report_start = (
            training_df["date"].iloc[0] if len(training_df) > 0 else "No data"
        )
        report_end = training_df["date"].iloc[-1] if len(training_df) > 0 else "No data"

        # ----------------------------------------------------------------------
        # 2. DATA FORMATTING AND VISUALIZATION
        # ----------------------------------------------------------------------

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

        # ----------------------------------------------------------------------
        # 3. MARKDOWN ASSEMBLY USING TEMPLATE
        # ----------------------------------------------------------------------

        # Generate macro ratio HTML if available
        macro_html = ""
        if macro_ratios:
            macro_chart_gen = MacroRatioChartGenerator()
            macro_html = macro_chart_gen.generate_html(
                macro_ratios["protein_pct"],
                macro_ratios["carbs_pct"],
                macro_ratios["fat_pct"],
            )

        # Format the report using a template
        report_template = f"""\
## Summary

**Key Metrics**:

- Weekly Total Calories: {total_calories:,.0f} kcal
- Average Protein: {avg_protein:.1f}g
- Strength Training Days: {strength_days}

## Weekly Macronutrients and Activity

{nutrition_chart if nutrition_chart else ''}

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
