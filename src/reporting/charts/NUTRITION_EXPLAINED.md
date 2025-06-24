# Nutrition Chart Generator: Step-by-Step Explanation

This document explains how the `NutritionChartGenerator` class works, breaking down the code step by step to understand how the nutrition visualization is created.

## 1. Class Setup and Initialization

```python
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
```

- The class inherits from a base `ChartGenerator` class
- It accepts parameters for:
  - `charts_dir`: Directory to save chart images
  - `target_strength`: Target calories for strength training days (default from config)
  - `target_rest`: Target calories for rest days (default from config)

## 2. Generate Method - Initial Setup

```python
def generate(self, df: pd.DataFrame, filename: str = "nutrition_chart.png") -> str:
    # Defensive: check required columns
    required_columns = {"date", "protein", "carbs", "fat", "activity"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"DataFrame must contain columns: {required_columns}")

    # Constants
    x_numeric = np.arange(len(df["date"]))
    width = 0.6
```

- Takes a DataFrame with nutrition data and an output filename
- Validates that the DataFrame has all required columns
- Creates numeric x-coordinates for plotting
- Sets the bar width to 0.6 units

## 3. Calorie Calculation

```python
# Calculate calories from macros
protein_cals = df["protein"] * 4  # 4 calories per gram
carbs_cals = df["carbs"] * 4  # 4 calories per gram
fat_cals = df["fat"] * 9  # 9 calories per gram
total_cals = protein_cals + carbs_cals + fat_cals
```

- Converts macronutrient grams to calories using standard conversion factors:
  - Protein: 4 calories per gram
  - Carbs: 4 calories per gram
  - Fat: 9 calories per gram
- Calculates total calories by summing all macronutrients

## 4. Color Setup

```python
# Colors - matching the macro report color scheme
protein_color = ReportingConfig.COLORS["protein"]  # Dark red
carbs_color = ReportingConfig.COLORS["carbs"]  # Black
fat_color = ReportingConfig.COLORS["fat"]  # Gray

# Bar colors - bright blue for strength days, gray for rest days
strength_day_color = ReportingConfig.COLORS["sleep_need"]  # Bright blue
```

- Gets colors from the configuration for consistent styling across reports
- Uses specific colors for each macronutrient and activity type

## 5. Chart Setup

```python
# Plot setup - taller chart for better spacing
fig, ax = self._setup_chart_figure(
    figsize=(10, ReportingConfig.STYLING["chart_height"])
)
```

- Creates a figure and axis with dimensions from the configuration
- Uses a helper method from the parent class

## 6. Creating Stacked Bars

```python
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

    # Create protein bar (bottom)
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

    # Create carbs bar (middle)
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

    # Create fat bar (top)
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
```

- Loops through each day's data to create stacked bars
- For each day:
  - Skips days with zero calories
  - Creates three stacked bars for protein, carbs, and fat
  - Sets the position of each bar (protein at bottom, carbs in middle, fat on top)
  - Applies consistent styling with semi-transparency
  - Only adds labels to the first bar of each type for the legend

## 7. Adding Calorie Labels

```python
# Add calorie labels at the bottom of each bar
for i, cal in enumerate(total_cals):
    if cal > 0:  # Only add labels for non-zero values
        # Use actual calories from the data if available, otherwise use calculated calories
        if 'calories' in df.columns:
            display_cal = df['calories'].iloc[i]
        else:
            display_cal = cal
            
        ax.annotate(
            f"{display_cal:.0f}",
            xy=(x_numeric[i], 120),  # Position above the x-axis
            xytext=(0, 0),  # No offset
            textcoords="offset points",
            ha="center",
            va="center",
            color="white",
            fontsize=ReportingConfig.STYLING["default_font_size"],
            fontweight="bold",
            zorder=10,
        )
```

- Adds text labels showing total calories above each bar
- Uses actual calories from data if available, otherwise uses calculated calories
- Formats the number without decimal places
- Positions the label high above each bar to avoid clipping
- Makes the text white and bold for visibility

## 8. Drawing Target Lines

```python
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
```

- Draws horizontal target lines for each day based on activity type
- Uses different styles for strength days (solid line) vs rest days (dashed line)
- Both use the same bright blue color for consistency
- Adds circle markers at the ends of each line
- Stores line handles for the legend

## 9. Axis Configuration and Styling

```python
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
```

- Calculates the maximum y-axis value based on data and target values
- Converts dates to day-of-week labels (e.g., "Mon", "Tue")
- Uses a helper method to apply consistent styling to the axes
- Sets up grid lines, labels, colors, and other visual elements

## 10. Creating Legends

```python
# Create legend for macros
macro_legend = [
    plt.Rectangle((0, 0), 1, 1, color=protein_color, alpha=ReportingConfig.STYLING["macro_bar_alpha"], label="Protein"),
    plt.Rectangle((0, 0), 1, 1, color=carbs_color, alpha=ReportingConfig.STYLING["macro_bar_alpha"], label="Carbs"),
    plt.Rectangle((0, 0), 1, 1, color=fat_color, alpha=ReportingConfig.STYLING["macro_bar_alpha"], label="Fat"),
]

# Create legend for activity targets
target_legend = [
    plt.Line2D([0], [0], color=strength_day_color, lw=ReportingConfig.STYLING["default_line_width"], 
               linestyle="-", marker="o", markersize=ReportingConfig.STYLING["default_marker_size"], 
               label=f"Strength Target ({self.target_strength} cal)"),
    plt.Line2D([0], [0], color=strength_day_color, lw=ReportingConfig.STYLING["default_line_width"], 
               linestyle="--", marker="o", markersize=ReportingConfig.STYLING["default_marker_size"], 
               label=f"Rest Target ({self.target_rest} cal)"),
]

# Initialize combined line legends with target legends
combined_line_legends = list(target_legend)
```

- Creates legend elements for macronutrients using colored rectangles
- Creates legend elements for target lines using Line2D objects
- Prepares a combined list for all line-based legend items

## 11. Optional Weight Data Visualization

```python
# Add weight data if available and create its legend
if "weight" in df.columns and not df["weight"].isna().all():
    # Create secondary y-axis for weight
    ax2 = ax.twinx()
    
    # Filter out NaN values for weight
    weight_data = df[["date", "weight"]].copy()
    weight_data = weight_data.dropna(subset=["weight"])
    
    if not weight_data.empty:
        # Plot weight data and trend line
        # ...
        # Add weight trend line to legend
        weight_legend = [
            plt.Line2D([0], [0], color=trend_color, lw=ReportingConfig.STYLING["weight_line_width"],
                       linestyle="--", marker="None", markersize=0, label="Weight Trend"),
        ]
        
        combined_line_legends.extend(weight_legend)
```

- Conditionally adds weight data visualization if present in the DataFrame
- Creates a secondary y-axis for weight values
- Plots weight points and a trend line
- Adds weight trend to the combined legend

## 12. Placing and Styling Legends

```python
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
```

- Places the macronutrient legend at the lower left
- Places the line-based legend (targets and weight trend) at the lower right
- Adds both legends to the figure
- Sets consistent text color for all legend items

## 13. Saving the Chart

```python
return self._save_chart(fig, filename, extra_artists=(macro_leg, line_leg))
```

- Saves the chart to the specified filename
- Includes the legends as extra artists to ensure they're properly included in the saved image
- Returns the path to the saved chart image

## Summary

The `NutritionChartGenerator` creates a sophisticated stacked bar chart that:

1. Shows daily calorie intake broken down by macronutrients (protein, carbs, fat)
2. Displays target calorie lines based on activity type (strength vs. rest days)
3. Optionally includes weight data with a trend line
4. Uses consistent styling and colors from the centralized configuration
5. Provides clear visual indicators through color-coding and legends
