import os
from typing import (  # Keep these for now as they might be used in helper methods later
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.date_utils import DateUtils

from .chart_generator import ChartGenerator
from .reporting_config import ReportingConfig


class NutritionChartGenerator(ChartGenerator):
    """Generates chart visualization for calorie intake with targets based on activity type."""

    def __init__(
        self,
        charts_dir: Optional[str] = None,
        target_strength: int = ReportingConfig.CALORIC_TARGETS["strength"],
        target_rest: int = ReportingConfig.CALORIC_TARGETS["rest"],
    ):
        """
        Initialize nutrition chart generator with output directory and calorie targets.

        Args:
            charts_dir: Directory to save chart images
            target_strength: Target calories for strength training days
            target_rest: Target calories for rest days
        """
        super().__init__(charts_dir)
        self.target_strength = target_strength
        self.target_rest = target_rest

    def generate(self, df: pd.DataFrame, filename: str = "nutrition_chart.png") -> str:
        """
        Generate a stacked bar chart for macronutrient breakdown with targets based on activity type.

        Args:
            df: DataFrame with columns ['date', 'protein', 'carbs', 'fat', 'activity']
                (date as string, macros in grams, activity as 'Rest' or 'Strength')
            filename: Output filename for the chart image
        Returns:
            Path to the saved chart image
        """
        # Defensive: check required columns
        required_columns = {"date", "protein", "carbs", "fat", "activity"}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        # Constants
        x_numeric = np.arange(len(df["date"]))
        width = 0.6

        # Calculate calories from macros
        protein_cals = df["protein"] * 4  # 4 calories per gram
        carbs_cals = df["carbs"] * 4  # 4 calories per gram
        fat_cals = df["fat"] * 9  # 9 calories per gram
        total_cals = protein_cals + carbs_cals + fat_cals

        # Colors - matching the macro report color scheme
        protein_color = ReportingConfig.COLORS[
            "protein"
        ]  # Dark red (for protein, most important macro)
        carbs_color = ReportingConfig.COLORS["carbs"]  # Black (for carbs)
        fat_color = ReportingConfig.COLORS["fat"]  # Gray (for fat)

        # Bar colors - bright blue for strength days, gray for rest days
        strength_day_color = ReportingConfig.COLORS[
            "sleep_need"
        ]  # Bright blue for strength days

        # Plot setup - taller chart for better spacing
        fig, ax = self._setup_chart_figure(
            figsize=(10, ReportingConfig.STYLING["chart_height"])
        )

        # Create stacked bars with different colors based on activity type
        bars_protein = []
        bars_carbs = []
        bars_fat = []

        for i, (x_pos, prot, carb, f, act) in enumerate(
            zip(x_numeric, protein_cals, carbs_cals, fat_cals, df["activity"])
        ):
            # Skip if no calories
            if prot + carb + f == 0:
                continue

            # Create protein bar (bottom) - no border, higher zorder to be in front of grid
            p_bar = ax.bar(
                x_pos,
                prot,
                width,
                label="Protein" if i == 0 else "",
                color=protein_color,
                alpha=ReportingConfig.STYLING["macro_bar_alpha"],
                zorder=3,
            )
            bars_protein.append(p_bar)

            # Create carbs bar (middle) - no border, higher zorder to be in front of grid
            c_bar = ax.bar(
                x_pos,
                carb,
                width,
                bottom=prot,
                label="Carbs" if i == 0 else "",
                color=carbs_color,
                alpha=ReportingConfig.STYLING["macro_bar_alpha"],
                zorder=3,
            )
            bars_carbs.append(c_bar)

            # Create fat bar (top) - no border, higher zorder to be in front of grid
            f_bar = ax.bar(
                x_pos,
                f,
                width,
                bottom=prot + carb,
                label="Fat" if i == 0 else "",
                color=fat_color,
                alpha=ReportingConfig.STYLING["macro_bar_alpha"],
                zorder=3,
            )
            bars_fat.append(f_bar)

        # Add calorie labels at the bottom of each bar (much higher up to avoid clipping)
        for i, cal in enumerate(total_cals):
            if cal > 0:  # Only add labels for non-zero values
                ax.annotate(
                    f"{cal:.0f}",
                    xy=(x_numeric[i], 120),  # Position even higher above the x-axis
                    xytext=(0, 0),  # No offset
                    textcoords="offset points",
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=ReportingConfig.STYLING["default_font_size"],
                    fontweight="bold",
                    zorder=10,
                )  # Ensure it's on top

        # Draw target lines with colors matching macronutrients
        strength_line_handles = []
        rest_line_handles = []

        for i, act in enumerate(df["activity"]):
            y = self.target_strength if act == "Strength" else self.target_rest
            line_style = "-" if act == "Strength" else "--"
            # Use bright blue for both strength and rest targets
            line_color = strength_day_color  # Same bright blue for both

            # Calculate start and end points for the target line
            x_start = x_numeric[i] - width * 0.7
            x_end = x_numeric[i] + width * 0.7

            # Draw the horizontal line
            line = ax.hlines(
                y,
                x_start,
                x_end,
                color=line_color,
                linewidth=ReportingConfig.STYLING["default_line_width"],
                linestyle=line_style,
                zorder=4,
            )

            # Add markers at each end of the line
            ax.plot(
                [x_start, x_end],
                [y, y],
                "o",
                color=line_color,
                markersize=ReportingConfig.STYLING["default_marker_size"],
                zorder=5,
            )

            # Store handles for legend
            if act == "Strength" and not strength_line_handles:
                strength_line_handles.append(line)
            elif act == "Rest" and not rest_line_handles:
                rest_line_handles.append(line)

        # Axis config and styling
        max_cal = max(
            total_cals.max() if not total_cals.empty else 0, self.target_strength
        )
        day_labels = DateUtils.get_day_of_week_labels(df["date"].tolist())

        self._style_axes(
            ax=ax,
            x_labels=day_labels,
            x_ticks=x_numeric,
            y_lim=(0, max_cal + 300),
            y_label="Calories Consumed",
            x_label="",
            tick_label_color=ReportingConfig.COLORS["text"],
            axis_label_color=ReportingConfig.COLORS["text"],
            font_size=ReportingConfig.STYLING["default_font_size"],
            tick_font_size=ReportingConfig.STYLING["tick_font_size"],
            grid_line_width=ReportingConfig.STYLING["grid_line_width"],
            grid_opacity=ReportingConfig.STYLING["grid_opacity"],
            spines_to_hide=["top", "right"],
            spines_to_color={
                "left": ReportingConfig.COLORS["grid"],
                "bottom": ReportingConfig.COLORS["grid"],
            },
        )

        # Create legend for macros
        macro_legend = [
            plt.Rectangle(
                (0, 0),
                1,
                1,
                color=protein_color,
                alpha=ReportingConfig.STYLING["macro_bar_alpha"],
                label="Protein",
            ),
            plt.Rectangle(
                (0, 0),
                1,
                1,
                color=carbs_color,
                alpha=ReportingConfig.STYLING["macro_bar_alpha"],
                label="Carbs",
            ),
            plt.Rectangle(
                (0, 0),
                1,
                1,
                color=fat_color,
                alpha=ReportingConfig.STYLING["macro_bar_alpha"],
                label="Fat",
            ),
        ]

        # Create legend for activity targets
        target_legend = [
            plt.Line2D(
                [0],
                [0],
                color=strength_day_color,
                lw=ReportingConfig.STYLING["default_line_width"],
                linestyle="-",
                marker="o",
                markersize=ReportingConfig.STYLING["default_marker_size"],
                label=f"Strength Target ({self.target_strength} cal)",
            ),
            plt.Line2D(
                [0],
                [0],
                color=strength_day_color,
                lw=ReportingConfig.STYLING["default_line_width"],
                linestyle="--",
                marker="o",
                markersize=ReportingConfig.STYLING["default_marker_size"],
                label=f"Rest Target ({self.target_rest} cal)",
            ),
        ]

        # Initialize combined line legends with target legends
        combined_line_legends = list(target_legend)

        # Add weight data if available and create its legend
        if "weight" in df.columns and not df["weight"].isna().all():
            # Create secondary y-axis for weight
            ax2 = ax.twinx()

            # Filter out NaN values for weight
            weight_data = df[["date", "weight"]].copy()
            weight_data = weight_data.dropna(subset=["weight"])

            if not weight_data.empty:
                # Get indices for the weight data points
                weight_indices = []
                weight_values = []
                for i, date in enumerate(df["date"]):
                    matching_rows = weight_data[weight_data["date"] == date]
                    if not matching_rows.empty:
                        weight_indices.append(i)
                        weight_values.append(matching_rows["weight"].values[0])

                if weight_indices and weight_values:
                    # Define colors for weight line and trend line
                    weight_color = ReportingConfig.COLORS[
                        "grid"
                    ]  # very light grey for weight line
                    trend_color = ReportingConfig.COLORS[
                        "sleep_need"
                    ]  # bright blue for trend line

                    # Plot weight line with markers - use more transparency
                    ax2.plot(
                        np.array(weight_indices),
                        weight_values,
                        "o-",
                        color=weight_color,
                        linewidth=ReportingConfig.STYLING["weight_line_width"],
                        markersize=ReportingConfig.STYLING["default_marker_size"],
                        alpha=ReportingConfig.STYLING["weight_line_alpha"],
                        label="Weight",
                        zorder=6,
                    )

                    # Removed numerical labels to make the chart cleaner

                    # Configure secondary y-axis
                    min_weight = min(weight_values) - 5 if weight_values else 150
                    max_weight = max(weight_values) + 5 if weight_values else 200
                    ax2.set_ylim(min_weight, max_weight)

                    # Use text color from constants for consistent styling
                    text_color = ReportingConfig.COLORS[
                        "text"
                    ]  # Gray for text elements

                    # Style the y-axis label and ticks with text color - use title case
                    ax2.set_ylabel(
                        "Weight (lbs)",
                        color=text_color,
                        fontsize=ReportingConfig.STYLING["default_font_size"],
                    )
                    ax2.tick_params(axis="y", colors=text_color, labelsize=8)

                    # Configure spines/borders for secondary axis - consistent with recovery chart
                    ax2.spines["top"].set_visible(False)
                    ax2.spines["left"].set_visible(False)
                    ax2.spines["right"].set_visible(True)
                    ax2.spines["bottom"].set_visible(False)
                    ax2.spines["right"].set_color(ReportingConfig.COLORS["grid"])

                    # Add a dotted trend line using numpy's polyfit
                    if (
                        len(weight_indices) > 1
                    ):  # Need at least 2 points for a trend line
                        z = np.polyfit(weight_indices, weight_values, 1)
                        p = np.poly1d(z)
                        trend_x = np.array([min(weight_indices), max(weight_indices)])
                        trend_y = p(trend_x)
                        ax2.plot(
                            trend_x,
                            trend_y,
                            "--",
                            color=trend_color,
                            linewidth=ReportingConfig.STYLING["default_line_width"],
                            alpha=ReportingConfig.STYLING["weight_trend_alpha"],
                            zorder=5,
                        )

                    # Add weight trend line to legend - use title case
                    weight_legend = [
                        plt.Line2D(
                            [0],
                            [0],
                            color=trend_color,
                            lw=ReportingConfig.STYLING["weight_line_width"],
                            linestyle="--",
                            marker="None",
                            markersize=0,
                            label="Weight Trend",
                        )
                    ]

                    combined_line_legends.extend(weight_legend)

        # Create and place macro legend (left)
        macro_leg = ax.legend(
            handles=macro_legend,
            loc="lower left",
            bbox_to_anchor=(0.0, ReportingConfig.STYLING["legend_vertical_offset"]),
            ncol=ReportingConfig.STYLING["legend_columns"],
            frameon=False,
            fontsize=ReportingConfig.STYLING["legend_font_size"],
        )

        # Create and place combined line legend (right)
        line_leg = ax.legend(
            handles=combined_line_legends,
            loc="lower right",
            bbox_to_anchor=(1.0, ReportingConfig.STYLING["legend_vertical_offset"]),
            ncol=len(combined_line_legends),
            frameon=False,
            fontsize=ReportingConfig.STYLING["legend_font_size"],
        )

        # Add legends as artists to the figure
        ax.add_artist(macro_leg)
        ax.add_artist(line_leg)

        # Style the legend text
        for text in macro_leg.get_texts():
            text.set_color(ReportingConfig.COLORS["text"])
        for text in line_leg.get_texts():
            text.set_color(ReportingConfig.COLORS["text"])

        return self._save_chart(fig, filename, extra_artists=(macro_leg, line_leg))
