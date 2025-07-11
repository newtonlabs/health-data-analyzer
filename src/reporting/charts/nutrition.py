# Python 3.12 has built-in type annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.app_config import AppConfig
from src.utils.date_utils import DateUtils
from src.utils.logging_utils import HealthLogger

from .base import ChartGenerator


class NutritionChartGenerator(ChartGenerator):
    """Generates chart visualization for calorie intake with targets based on activity type."""

    def __init__(self):
        """
        Initialize nutrition chart generator with config values.
        """
        super().__init__()
        self.target_strength = AppConfig.REPORTING_CALORIC_TARGETS["strength"]
        self.target_rest = AppConfig.REPORTING_CALORIC_TARGETS["rest"]
        self.logger = HealthLogger(__name__)

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

        # Calculate calories from macros using factors from AppConfig
        protein_cals = df["protein"] * AppConfig.REPORTING_CALORIE_FACTORS["protein"]
        carbs_cals = df["carbs"] * AppConfig.REPORTING_CALORIE_FACTORS["carbs"]
        fat_cals = df["fat"] * AppConfig.REPORTING_CALORIE_FACTORS["fat"]

        # Debug: Log column names to verify alcohol is present
        self.logger.logger.debug(f"DataFrame columns: {df.columns.tolist()}")

        # Calculate alcohol calories
        if "alcohol" in df.columns:
            self.logger.logger.debug(f"Alcohol values in df: {df['alcohol'].tolist()}")
            alcohol_cals = (
                df["alcohol"] * AppConfig.REPORTING_CALORIE_FACTORS["alcohol"]
            )
            self.logger.logger.debug(f"Alcohol calories: {alcohol_cals.tolist()}")
        else:
            self.logger.logger.debug("'alcohol' column not found in DataFrame")
            alcohol_cals = pd.Series([0] * len(df))

        total_cals = protein_cals + carbs_cals + fat_cals + alcohol_cals

        # Colors - matching the macro report color scheme
        protein_color = AppConfig.REPORTING_COLORS[
            "protein"
        ]  # Dark red (for protein, most important macro)
        carbs_color = AppConfig.REPORTING_COLORS["carbs"]  # Black (for carbs)
        fat_color = AppConfig.REPORTING_COLORS["fat"]  # Gray (for fat)
        alcohol_color = AppConfig.REPORTING_COLORS[
            "alcohol"
        ]  # Dark orange (for alcohol)

        # Make alcohol more visible by reducing alpha transparency
        alcohol_alpha = 0.9  # Higher alpha (less transparent) for alcohol

        # Bar colors - bright blue for strength days, gray for rest days
        strength_day_color = AppConfig.REPORTING_COLORS[
            "sleep_need"
        ]  # Bright blue for strength days

        # Plot setup - taller and wider chart for better spacing and legend room
        fig, ax = self._setup_chart_figure(
            figsize=(11, AppConfig.REPORTING_STYLING["chart_height"])
        )

        # Create stacked bars with different colors based on activity type
        bars_protein = []
        bars_carbs = []
        bars_fat = []
        bars_alcohol = []

        for i, (x_pos, prot, carb, f, alc, act) in enumerate(
            zip(
                x_numeric,
                protein_cals,
                carbs_cals,
                fat_cals,
                alcohol_cals,
                df["activity"],
            )
        ):
            # Skip if no calories
            if prot + carb + f + alc == 0:
                continue

            # Create protein bar (bottom) - no border, higher zorder to be in front of grid
            p_bar = ax.bar(
                x_pos,
                prot,
                width,
                label="Protein" if i == 0 else "",
                color=protein_color,
                alpha=AppConfig.REPORTING_STYLING["macro_bar_alpha"],
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
                alpha=AppConfig.REPORTING_STYLING["macro_bar_alpha"],
                zorder=3,
            )
            bars_carbs.append(c_bar)

            # Create fat bar (middle-top) - no border, higher zorder to be in front of grid
            f_bar = ax.bar(
                x_pos,
                f,
                width,
                bottom=prot + carb,
                label="Fat" if i == 0 else "",
                color=fat_color,
                alpha=AppConfig.REPORTING_STYLING["macro_bar_alpha"],
                zorder=3,
            )
            bars_fat.append(f_bar)

            # Create alcohol bar (top) - no border, higher zorder to be in front of grid
            self.logger.logger.debug(
                f"For index {i}, date {df['date'].iloc[i]}, alcohol calories: {alc}"
            )
            if alc > 0:  # Only add alcohol bar if there's alcohol consumption
                self.logger.logger.debug(
                    f"Adding alcohol bar for index {i}, date {df['date'].iloc[i]}"
                )
                a_bar = ax.bar(
                    x_pos,
                    alc,
                    width,
                    bottom=prot + carb + f,
                    label="Alcohol" if i == 0 else "",
                    color=alcohol_color,
                    alpha=alcohol_alpha,  # Use higher alpha for better visibility
                    zorder=4,  # Higher zorder to ensure it's on top
                )
                bars_alcohol.append(a_bar)
            else:
                self.logger.logger.debug(
                    f"No alcohol bar added for index {i}, date {df['date'].iloc[i]} (alc={alc})"
                )

        # Add calorie labels at the bottom of each bar (much higher up to avoid clipping)
        for i, cal in enumerate(total_cals):
            if cal > 0:  # Only add labels for non-zero values
                # Use actual calories from the data if available, otherwise use calculated calories
                if "calories" in df.columns:
                    display_cal = df["calories"].iloc[i]
                else:
                    display_cal = cal

                ax.annotate(
                    f"{display_cal:.0f}",
                    xy=(x_numeric[i], 120),  # Position even higher above the x-axis
                    xytext=(0, 0),  # No offset
                    textcoords="offset points",
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=AppConfig.REPORTING_STYLING["default_font_size"],
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
                linewidth=AppConfig.REPORTING_STYLING["default_line_width"],
                linestyle=line_style,
                zorder=4,
            )

            # Add markers at each end of the line
            ax.plot(
                [x_start, x_end],
                [y, y],
                "o",
                color=line_color,
                markersize=AppConfig.REPORTING_STYLING["default_marker_size"],
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
        
        # Debug: Log the date values being passed to get_day_of_week_labels
        date_values = df["date"].tolist()
        self.logger.debug(f"Date values being passed to get_day_of_week_labels: {date_values}")
        
        # Get day labels
        day_labels = DateUtils.get_day_of_week_labels(date_values)
        
        # Debug: Log the returned day labels
        self.logger.debug(f"Day labels returned: {day_labels}")

        self._style_axes(
            ax=ax,
            x_labels=day_labels,
            x_ticks=x_numeric,
            y_lim=(0, max_cal + 300),
            y_label="Calories Consumed",
            x_label="",
            tick_label_color=AppConfig.REPORTING_COLORS["text"],
            axis_label_color=AppConfig.REPORTING_COLORS["text"],
            font_size=AppConfig.REPORTING_STYLING["default_font_size"],
            tick_font_size=AppConfig.REPORTING_STYLING["tick_font_size"],
            grid_line_width=AppConfig.REPORTING_STYLING["grid_line_width"],
            grid_opacity=AppConfig.REPORTING_STYLING["grid_opacity"],
            spines_to_hide=["top", "right"],
            spines_to_color={
                "left": AppConfig.REPORTING_COLORS["grid"],
                "bottom": AppConfig.REPORTING_COLORS["grid"],
            },
        )

        # Create legend for macros
        macro_legend = [
            plt.Rectangle(
                (0, 0),
                1,
                1,
                color=protein_color,
                alpha=AppConfig.REPORTING_STYLING["macro_bar_alpha"],
                label="Protein",
            ),
            plt.Rectangle(
                (0, 0),
                1,
                1,
                color=carbs_color,
                alpha=AppConfig.REPORTING_STYLING["macro_bar_alpha"],
                label="Carbs",
            ),
            plt.Rectangle(
                (0, 0),
                1,
                1,
                color=fat_color,
                alpha=AppConfig.REPORTING_STYLING["macro_bar_alpha"],
                label="Fat",
            ),
            plt.Rectangle(
                (0, 0),
                1,
                1,
                color=alcohol_color,
                alpha=AppConfig.REPORTING_STYLING["macro_bar_alpha"],
                label="Alcohol",
            ),
        ]

        # Create legend for activity targets
        target_legend = [
            plt.Line2D(
                [0],
                [0],
                color=strength_day_color,
                lw=AppConfig.REPORTING_STYLING["default_line_width"],
                linestyle="-",
                marker="o",
                markersize=AppConfig.REPORTING_STYLING["default_marker_size"],
                label=f"Strength Target ({self.target_strength} cal)",
            ),
            plt.Line2D(
                [0],
                [0],
                color=strength_day_color,
                lw=AppConfig.REPORTING_STYLING["default_line_width"],
                linestyle="--",
                marker="o",
                markersize=AppConfig.REPORTING_STYLING["default_marker_size"],
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
                    weight_color = AppConfig.REPORTING_COLORS[
                        "sleep_actual"
                    ]  # Dark red for weight line
                    trend_color = AppConfig.REPORTING_COLORS[
                        "sleep_need"
                    ]  # Blue for trend line

                    # Plot weight line with markers - use more transparency
                    ax2.plot(
                        np.array(weight_indices),
                        weight_values,
                        "o-",
                        color=weight_color,
                        linewidth=AppConfig.REPORTING_STYLING["weight_line_width"],
                        markersize=AppConfig.REPORTING_STYLING["default_marker_size"],
                        alpha=AppConfig.REPORTING_STYLING["weight_line_alpha"],
                        label="Weight",
                        zorder=6,
                    )

                    # Removed numerical labels to make the chart cleaner

                    # Configure secondary y-axis
                    min_weight = min(weight_values) - 5 if weight_values else 150
                    max_weight = max(weight_values) + 5 if weight_values else 200
                    ax2.set_ylim(min_weight, max_weight)

                    # Use text color from constants for consistent styling
                    text_color = AppConfig.REPORTING_COLORS[
                        "text"
                    ]  # Gray for text elements

                    # Style the y-axis label and ticks with text color - use title case
                    ax2.set_ylabel(
                        "Weight (lbs)",
                        color=text_color,
                        fontsize=AppConfig.REPORTING_STYLING["default_font_size"],
                    )
                    ax2.tick_params(axis="y", colors=text_color, labelsize=8)

                    # Configure spines/borders for secondary axis - consistent with recovery chart
                    ax2.spines["top"].set_visible(False)
                    ax2.spines["left"].set_visible(False)
                    ax2.spines["right"].set_visible(True)
                    ax2.spines["bottom"].set_visible(False)
                    ax2.spines["right"].set_color(AppConfig.REPORTING_COLORS["grid"])

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
                            linewidth=AppConfig.REPORTING_STYLING["default_line_width"],
                            alpha=AppConfig.REPORTING_STYLING["weight_trend_alpha"],
                            zorder=5,
                        )

                    # Add weight trend line to legend - use title case
                    weight_legend = [
                        plt.Line2D(
                            [0],
                            [0],
                            color=trend_color,
                            lw=AppConfig.REPORTING_STYLING["weight_line_width"],
                            linestyle="--",
                            marker="None",
                            markersize=0,
                            label="Weight Trend",
                        )
                    ]

                    combined_line_legends.extend(weight_legend)

        # Create and place macro legend (left) - using 2 columns for better spacing
        macro_leg = ax.legend(
            handles=macro_legend,
            loc="lower left",
            bbox_to_anchor=(0.0, AppConfig.REPORTING_STYLING["legend_vertical_offset"]),
            ncol=2,  # Fixed 2 columns for macro legend regardless of config
            frameon=False,
            fontsize=AppConfig.REPORTING_STYLING["legend_font_size"],
        )

        # Create and place combined line legend (right)
        # Calculate number of columns based on number of items, but cap at 2 for better spacing
        n_cols = min(len(combined_line_legends), 2)
        line_leg = ax.legend(
            handles=combined_line_legends,
            loc="lower right",
            bbox_to_anchor=(1.0, AppConfig.REPORTING_STYLING["legend_vertical_offset"]),
            ncol=n_cols,
            frameon=False,
            fontsize=AppConfig.REPORTING_STYLING["legend_font_size"],
        )

        # Add legends as artists to the figure
        ax.add_artist(macro_leg)
        ax.add_artist(line_leg)

        # Style the legend text
        for text in macro_leg.get_texts():
            text.set_color(AppConfig.REPORTING_COLORS["text"])
        for text in line_leg.get_texts():
            text.set_color(AppConfig.REPORTING_COLORS["text"])

        return self._save_chart(fig, filename, extra_artists=(macro_leg, line_leg))
