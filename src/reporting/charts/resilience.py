"""Resilience chart generator module."""

# Python 3.12 has built-in type annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.app_config import AppConfig
from src.utils.date_utils import DateUtils

from .base import ChartGenerator


class ResilienceChartGenerator(ChartGenerator):
    """
    Generates a resilience chart image from a DataFrame containing resilience data.
    Output is saved as a PNG in data/charts/.
    """

    def __init__(self):
        """
        Initialize resilience chart generator with config values.
        """
        super().__init__()

        # Get resilience bands from analyzer_config
        # Use lowercase keys for internal logic but uppercase for display
        self.resilience_bands = {}
        for level, score in AppConfig.ANALYSIS_RESILIENCE_LEVEL_SCORES.items():
            # Only include the main levels, skip legacy mappings
            if level in ["exceptional", "strong", "solid", "adequate", "limited"]:
                self.resilience_bands[level.upper()] = score

    def generate(self, df: pd.DataFrame, filename: str = "resilience_chart.png") -> str:
        """
        Generate a line chart for resilience scores.

        Args:
            df: DataFrame with columns ['date', 'resilience_score'] (date as string, resilience_score as numeric)
            filename: Output filename for the chart image
        Returns:
            Path to the saved chart image
        """
        # Defensive: check required columns
        if not {"date", "resilience_score"}.issubset(df.columns):
            raise ValueError(
                "DataFrame must contain 'date' and 'resilience_score' columns"
            )

        # Plot setup - using compact chart height
        fig, ax = self._setup_chart_figure(
            figsize=(10, AppConfig.REPORTING_STYLING["chart_height_compact"])
        )

        # Adjust margins to match recovery chart
        plt.subplots_adjust(right=0.82, left=0.12)  # Match recovery chart margins

        day_labels = DateUtils.get_day_of_week_labels(df["date"].tolist())

        # Set up x-axis values
        x_numeric = np.arange(len(df["date"]))

        # Plot the line in a medium gray
        ax.plot(
            x_numeric,
            df["resilience_score"],
            color=AppConfig.REPORTING_COLORS["text"],
            marker="o",
            markersize=AppConfig.REPORTING_STYLING["default_marker_size"],
            linewidth=AppConfig.REPORTING_STYLING["default_line_width"],
            zorder=3,
        )

        # Add horizontal band lines and labels
        for label, score in self.resilience_bands.items():
            # Blue line for 'STRONG', others in dark gray
            color = (
                AppConfig.REPORTING_COLORS["resilience_strong"]
                if label == "STRONG"
                else AppConfig.REPORTING_COLORS["grid"]
            )
            # Solid line for the baseline (LIMITED = 0), dashed for others
            linestyle = "-" if score == 0 else "--"
            # Line thickness and opacity
            linewidth = 1.2 if label == "STRONG" else 0.8
            alpha = (
                1.0
                if label == "STRONG"
                else AppConfig.REPORTING_STYLING["grid_opacity"]
            )

            ax.axhline(
                score,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=alpha,
                zorder=1,
            )
            ax.text(
                -0.75,
                score,
                label,
                va="center",
                ha="right",
                fontsize=AppConfig.REPORTING_STYLING["resilience_band_font_size"],
                color=color,
                fontweight="bold",
            )

        # Set up axes
        self._style_axes(
            ax=ax,
            x_labels=day_labels,
            x_ticks=x_numeric,
            y_lim=(0, 100),
            x_label="",
            tick_label_color=AppConfig.REPORTING_COLORS["text"],
            axis_label_color=AppConfig.REPORTING_COLORS["text"],
            font_size=AppConfig.REPORTING_STYLING["default_font_size"],
            tick_font_size=AppConfig.REPORTING_STYLING["tick_font_size"],
            grid_axis="x",
            grid_color=AppConfig.REPORTING_COLORS["resilience_x_grid"],
            grid_line_width=AppConfig.REPORTING_STYLING["grid_line_width"],
            grid_opacity=1.0,  # Grid always visible for resilience chart
            spines_to_hide=["top", "right", "left"],  # Hide left Y-axis for main plot
            spines_to_color={"bottom": AppConfig.REPORTING_COLORS["chart_border"]},
        )

        # Create a twin axis on the right for score values
        ax2 = ax.twinx()
        self._style_axes(
            ax=ax2,
            y_lim=(0, 100),
            y_label="Score",
            y_ticks=[0, 20, 40, 60, 80],
            tick_label_color=AppConfig.REPORTING_COLORS["text"],
            axis_label_color=AppConfig.REPORTING_COLORS["text"],
            font_size=AppConfig.REPORTING_STYLING["default_font_size"],
            tick_font_size=AppConfig.REPORTING_STYLING["tick_font_size"],
            spines_to_hide=["top", "bottom", "left"],
            spines_to_color={"right": AppConfig.REPORTING_COLORS["grid"]},
            secondary_ax=ax2,
        )
        # Hide main y-axis completely
        ax.yaxis.set_visible(False)

        # Save the chart with the same settings as recovery chart
        return self._save_chart(fig, filename)
