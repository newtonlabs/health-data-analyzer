import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .reporting_config import ReportingConfig

class ChartGenerator:
    """Base class for chart generators."""
    
    def __init__(self, charts_dir: Optional[str] = None):
        """Initialize chart generator with output directory."""
        self.charts_dir = charts_dir or os.path.join("data", "charts")
        os.makedirs(self.charts_dir, exist_ok=True)
        
    def _get_day_of_week_labels(self, date_strings: List[str]) -> List[str]:
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

class RecoveryChartGenerator(ChartGenerator):
    """
    Generates a recovery chart image from a DataFrame containing recovery data.
    Output is saved as a PNG in data/charts/.
    """
    
    def __init__(self, charts_dir: Optional[str] = None):
        """
        Initialize recovery chart generator with output directory and color definitions.
        
        Args:
            charts_dir: Directory to save chart images
        """
        super().__init__(charts_dir)
        # Get colors and thresholds from config
        self.green_color = ReportingConfig.COLORS['recovery_high']
        self.yellow_color = ReportingConfig.COLORS['recovery_medium']
        self.red_color = ReportingConfig.COLORS['recovery_low']
        self.recovery_threshold_high = ReportingConfig.THRESHOLDS['recovery_high']
        self.recovery_threshold_medium = ReportingConfig.THRESHOLDS['recovery_medium']
        self.recovery_threshold_low = ReportingConfig.THRESHOLDS['recovery_low']
    def generate(self, df: pd.DataFrame, filename: str = "recovery_chart.png") -> str:
        """
        Generate a bar chart for recovery scores with sleep need vs. actual overlay.

        Args:
            df: DataFrame with columns ['date', 'recovery'] (date as string, recovery as numeric)
                 and optionally ['sleep_need', 'sleep_actual'] for the line chart overlay
            filename: Output filename for the chart image
        Returns:
            Path to the saved chart image
        """
        # Defensive: check required columns
        if not {'date', 'recovery'}.issubset(df.columns):
            raise ValueError("DataFrame must contain 'date' and 'recovery' columns")

        # Plot setup - slightly taller chart to accommodate bottom legend
        fig, ax1 = plt.subplots(figsize=(10, ReportingConfig.STYLING['chart_height']))
        fig.patch.set_facecolor('white')
        ax1.set_facecolor('white')
        
        # Create color-coded bars based on recovery score with three levels
        bar_colors = []
        for score in df['recovery']:
            if score >= self.recovery_threshold_high:
                bar_colors.append(self.green_color)  # High recovery
            elif score >= self.recovery_threshold_medium:
                bar_colors.append(self.yellow_color)  # Moderate recovery
            else:
                bar_colors.append(self.red_color)  # Low recovery
        
        # Create bars with consistent opacity
        x_numeric = np.arange(len(df['date']))
        bars = ax1.bar(x_numeric, df['recovery'], width=0.6, 
                       color=bar_colors, alpha=ReportingConfig.STYLING['bar_alpha'], zorder=3)
        
        # Add recovery score labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        color=ReportingConfig.COLORS['text'], fontsize=9)
        
        # Add legend at the bottom left with rectangle patches to match nutrition chart
        recovery_legend = [
            plt.Rectangle((0,0), 1, 1, color=self.green_color, alpha=ReportingConfig.STYLING['bar_alpha'], label=f"High Recovery (≥{self.recovery_threshold_high})"),
            plt.Rectangle((0,0), 1, 1, color=self.yellow_color, alpha=ReportingConfig.STYLING['bar_alpha'], label=f"Moderate Recovery ({self.recovery_threshold_medium}-{self.recovery_threshold_high-1})"),
            plt.Rectangle((0,0), 1, 1, color=self.red_color, alpha=ReportingConfig.STYLING['bar_alpha'], label=f"Low Recovery (≤{self.recovery_threshold_low})")
        ]
        
        # Add legend at the bottom left with 3 columns for recovery levels
        recovery_leg = ax1.legend(handles=recovery_legend, loc='lower left', 
                                 bbox_to_anchor=(0.0, -0.2), ncol=3, 
                                 frameon=False, fontsize=9)
        
        # Style the legend text
        for text in recovery_leg.get_texts():
            text.set_color(ReportingConfig.COLORS['text'])
        
        # Add sleep need vs. actual overlay if columns exist
        has_sleep_data = {'sleep_need', 'sleep_actual'}.issubset(df.columns) and \
                        not df['sleep_need'].isna().all() and not df['sleep_actual'].isna().all()
                        
        if has_sleep_data:
            # Create secondary axis for sleep hours
            ax2 = ax1.twinx()
            
            # No smoothing - plot direct lines with markers using same x_numeric as bars
            # Plot lines with updated styling and markers
            sleep_actual_line, = ax2.plot(x_numeric, df['sleep_actual'], 
                                        color=ReportingConfig.COLORS['sleep_actual'], linestyle='--', linewidth=ReportingConfig.STYLING['line_thickness'], 
                                        marker='o', markersize=4,
                                        label="Sleep Actual")
            
            # Use bright blue for sleep need line to match nutrition chart target lines
            sleep_need_line, = ax2.plot(x_numeric, df['sleep_need'], 
                                      color=ReportingConfig.COLORS['sleep_need'], linestyle='-', linewidth=ReportingConfig.STYLING['line_thickness'], 
                                      marker='s', markersize=4,
                                      label="Sleep Need")
            
            # Set up secondary axis for sleep hours
            max_sleep = max(df['sleep_need'].max(), df['sleep_actual'].max())
            ax2.set_ylim(0, max_sleep * 1.2)
            
            # Configure y-axis on the right for sleep hours
            ax2.spines['top'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            ax2.spines['right'].set_visible(True)
            ax2.spines['right'].set_color(ReportingConfig.COLORS['grid'])
            ax2.tick_params(axis='y', colors=ReportingConfig.COLORS['text'], labelsize=8)
            ax2.set_ylabel('Hours', color=ReportingConfig.COLORS['text'], fontsize=9)
            ax2.yaxis.set_visible(True)
            
            # Add legend at the bottom right, similar to nutrition chart
            sleep_legend = [
                plt.Line2D([0], [0], color="#1E88E5", lw=1.5, linestyle='-', marker='s', markersize=4,
                          label="Sleep Need"),
                plt.Line2D([0], [0], color="#7B1F1F", lw=1.5, linestyle='--', marker='o', markersize=4,
                          label="Sleep Actual")
            ]
            
            # Add legend at the bottom right
            sleep_leg = ax2.legend(handles=sleep_legend, loc='lower right', 
                                 bbox_to_anchor=(1.0, -0.2), ncol=2, 
                                 frameon=False, fontsize=9)
            
            # Style the legend text
            for text in sleep_leg.get_texts():
                text.set_color(ReportingConfig.COLORS['text'])
                
            # Make sure the sleep legend is added after the recovery legend
            ax2.add_artist(sleep_leg)
        
        # Set up primary axis styling
        ax1.set_ylim(0, 100)
        
        # Set x-ticks and convert date labels to day of week
        ax1.set_xticks(x_numeric)
        
        # Create day of week labels directly
        day_labels = []
        for date_str in df['date']:
            try:
                # Try different date formats
                if '-' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    # Try MM-DD format
                    current_year = datetime.now().year
                    date_obj = datetime.strptime(f"{current_year}-{date_str}", '%Y-%m-%d')
                # Get abbreviated day name
                day_labels.append(date_obj.strftime('%a'))
            except ValueError:
                day_labels.append(date_str)
        
        # Set x-tick labels to day of week
        ax1.set_xticklabels(day_labels)
        
        # Add light gray axis labels
        ax1.set_ylabel('Recovery', color=ReportingConfig.COLORS['text'], fontsize=9)
        ax1.set_xlabel('', color=ReportingConfig.COLORS['text'], fontsize=9)
        ax1.tick_params(axis='x', colors=ReportingConfig.COLORS['text'], labelsize=8)
        ax1.tick_params(axis='y', colors=ReportingConfig.COLORS['text'], labelsize=8)
        
        # Enhanced grid styling - both horizontal and vertical with increased visibility
        ax1.grid(True, linestyle=':', linewidth=0.7, alpha=ReportingConfig.STYLING['grid_opacity'], color=ReportingConfig.COLORS['grid'])
        
        # Configure spines/borders for primary axis - consistent light gray
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_visible(True)
        ax1.spines['bottom'].set_visible(True)
        ax1.spines['left'].set_color(ReportingConfig.COLORS['grid'])
        ax1.spines['bottom'].set_color(ReportingConfig.COLORS['grid'])
        
        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path

class NutritionChartGenerator(ChartGenerator):
    """Generates chart visualization for calorie intake with targets based on activity type."""
    
    def __init__(self, charts_dir: Optional[str] = None, target_strength: int = ReportingConfig.CALORIC_TARGETS['strength'], target_rest: int = ReportingConfig.CALORIC_TARGETS['rest']):
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
    

        
    def generate_stacked(self, df: pd.DataFrame, filename: str = "stacked_nutrition.png") -> str:
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
        required_columns = {'date', 'protein', 'carbs', 'fat', 'activity'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")
            
        # Constants
        x_numeric = np.arange(len(df['date']))
        width = 0.6
        
        # Calculate calories from macros
        protein_cals = df['protein'] * 4  # 4 calories per gram
        carbs_cals = df['carbs'] * 4      # 4 calories per gram
        fat_cals = df['fat'] * 9          # 9 calories per gram
        total_cals = protein_cals + carbs_cals + fat_cals
        
        # Colors - matching the macro report color scheme
        protein_color = ReportingConfig.COLORS['protein']  # Dark red (for protein, most important macro)
        carbs_color = ReportingConfig.COLORS['carbs']    # Black (for carbs)
        fat_color = ReportingConfig.COLORS['fat']      # Gray (for fat)
        
        # Bar colors - bright blue for strength days, gray for rest days
        strength_day_color = ReportingConfig.COLORS['sleep_need']  # Bright blue for strength days
        
        # Plot setup - taller chart for better spacing
        fig, ax = plt.subplots(figsize=(10, ReportingConfig.STYLING['chart_height']))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Create stacked bars with different colors based on activity type
        bars_protein = []
        bars_carbs = []
        bars_fat = []
        
        for i, (x_pos, prot, carb, f, act) in enumerate(zip(x_numeric, protein_cals, carbs_cals, fat_cals, df['activity'])):
            # Skip if no calories
            if prot + carb + f == 0:
                continue
                
            # Use blue for strength days, gray for rest days
            bar_color = strength_day_color if act == "Strength" else "#999999"
            
            # Create protein bar (bottom) - no border, higher zorder to be in front of grid
            p_bar = ax.bar(x_pos, prot, width, label='Protein' if i == 0 else "", 
                          color=protein_color, zorder=3)
            bars_protein.append(p_bar)
            
            # Create carbs bar (middle) - no border, higher zorder to be in front of grid
            c_bar = ax.bar(x_pos, carb, width, bottom=prot, 
                          label='Carbs' if i == 0 else "", 
                          color=carbs_color, zorder=3)
            bars_carbs.append(c_bar)
            
            # Create fat bar (top) - no border, higher zorder to be in front of grid
            f_bar = ax.bar(x_pos, f, width, bottom=prot+carb, 
                          label='Fat' if i == 0 else "", 
                          color=fat_color, zorder=3)
            bars_fat.append(f_bar)
        
        # Add calorie labels at the bottom of each bar (much higher up to avoid clipping)
        for i, cal in enumerate(total_cals):
            if cal > 0:  # Only add labels for non-zero values
                ax.annotate(f'{cal:.0f}',
                            xy=(x_numeric[i], 120),  # Position even higher above the x-axis
                            xytext=(0, 0),  # No offset
                            textcoords="offset points",
                            ha='center', va='center',
                            color='white', fontsize=9, fontweight='bold',
                            zorder=10)  # Ensure it's on top
        
        # Draw target lines with colors matching macronutrients
        strength_line_handles = []
        rest_line_handles = []
        
        for i, act in enumerate(df['activity']):
            y = self.target_strength if act == "Strength" else self.target_rest
            line_style = '-' if act == "Strength" else '--'
            # Use bright blue for both strength and rest targets
            line_color = strength_day_color  # Same bright blue for both
            
            # Make lines wider than the bar with very thin lines (1.0pt)
            line = ax.hlines(y, x_numeric[i] - width*0.7, x_numeric[i] + width*0.7, 
                      color=line_color, linewidth=1.5, linestyle=line_style, zorder=4)
            
            # Store handles for legend
            if act == "Strength" and not strength_line_handles:
                strength_line_handles.append(line)
            elif act == "Rest" and not rest_line_handles:
                rest_line_handles.append(line)
        
        # Axis config - start at 0 to make bars touch x-axis
        max_cal = max(total_cals.max() if not total_cals.empty else 0, self.target_strength)
        ax.set_ylim(0, max_cal + 300)  # No negative space so bars touch x-axis
        ax.set_xticks(x_numeric)
        
        # Create day of week labels directly
        day_labels = []
        for date_str in df['date']:
            try:
                # Try different date formats
                if '-' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    # Try MM-DD format
                    current_year = datetime.now().year
                    date_obj = datetime.strptime(f"{current_year}-{date_str}", '%Y-%m-%d')
                # Get abbreviated day name
                day_labels.append(date_obj.strftime('%a'))
            except ValueError:
                day_labels.append(date_str)
        
        ax.set_xticklabels(day_labels)
        
        # Minimal styling with no labels
        ax.set_xlabel("", color='#666666', fontsize=9)
        ax.set_ylabel("", color='#666666', fontsize=9)
        ax.tick_params(axis='both', colors='#666666', labelsize=8)
        
        # Configure spines/borders - consistent with recovery chart
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_color(ReportingConfig.COLORS['grid'])
        ax.spines['bottom'].set_color(ReportingConfig.COLORS['grid'])
        
        # Grid styling - both horizontal and vertical (behind the bars)
        ax.grid(True, linestyle=':', linewidth=0.7, alpha=ReportingConfig.STYLING['grid_opacity'], color=ReportingConfig.COLORS['grid'], zorder=0)
        
        # Add weight data if available
        weight_legend = []
        if 'weight' in df.columns and not df['weight'].isna().all():
                # Create secondary y-axis for weight
                ax2 = ax.twinx()
                
                # Filter out NaN values for weight
                weight_data = df[['date', 'weight']].copy()
                weight_data = weight_data.dropna(subset=['weight'])
                
                if not weight_data.empty:
                    # Get indices for the weight data points
                    weight_indices = []
                    weight_values = []
                    for i, date in enumerate(df['date']):
                        matching_rows = weight_data[weight_data['date'] == date]
                        if not matching_rows.empty:
                            weight_indices.append(i)
                            weight_values.append(matching_rows['weight'].values[0])
                    
                    if weight_indices and weight_values:
                        # Define colors for weight line and trend line
                        weight_color = ReportingConfig.COLORS['grid']  # very light grey for weight line
                        trend_color = ReportingConfig.COLORS['sleep_need']  # bright blue for trend line
                        
                        # Plot weight line with markers - use more transparency
                        weight_line = ax2.plot(np.array(weight_indices), weight_values, 'o-', 
                                               color=weight_color, linewidth=2, markersize=4, 
                                               alpha=0.3, label='Weight', zorder=6)
                        
                        # Removed numerical labels to make the chart cleaner
                        
                        # Configure secondary y-axis
                        min_weight = min(weight_values) - 5 if weight_values else 150
                        max_weight = max(weight_values) + 5 if weight_values else 200
                        ax2.set_ylim(min_weight, max_weight)
                        
                        # Use text color from constants for consistent styling
                        text_color = ReportingConfig.COLORS['text']  # Gray for text elements
                        border_color = ReportingConfig.COLORS['grid']  # Light gray for borders
                        
                        # Style the y-axis label and ticks with text color - use all caps like other metrics
                        ax2.set_ylabel('WEIGHT (lbs)', color=text_color, fontsize=9)
                        ax2.tick_params(axis='y', colors=text_color, labelsize=8)
                        
                        # Configure spines/borders for secondary axis - consistent with recovery chart
                        ax2.spines['top'].set_visible(False)
                        ax2.spines['left'].set_visible(False)
                        ax2.spines['right'].set_visible(True)
                        ax2.spines['bottom'].set_visible(False)
                        ax2.spines['right'].set_color(ReportingConfig.COLORS['grid'])
                        
                        # Add a dotted trend line using numpy's polyfit
                        if len(weight_indices) > 1:  # Need at least 2 points for a trend line
                            z = np.polyfit(weight_indices, weight_values, 1)
                            p = np.poly1d(z)
                            trend_x = np.array([min(weight_indices), max(weight_indices)])
                            trend_y = p(trend_x)
                            ax2.plot(trend_x, trend_y, '--', color=trend_color, linewidth=1.5, 
                                    alpha=0.9, zorder=5)
                        
                        # Add weight trend line to legend - use all caps like other metrics
                        weight_legend = [plt.Line2D([0], [0], color=trend_color, lw=2, linestyle='--',
                                                   markersize=0, label='WEIGHT TREND')]
        
        # Create combined legend with macros and targets
        macro_legend = [
            plt.Rectangle((0,0), 1, 1, color=protein_color, label='Protein'),
            plt.Rectangle((0,0), 1, 1, color=carbs_color, label='Carbs'),
            plt.Rectangle((0,0), 1, 1, color=fat_color, label='Fat')
        ]
        
        target_legend = [
            plt.Line2D([0], [0], color=strength_day_color, lw=2, linestyle='-', 
                      label=f'Strength ({self.target_strength} kcal)'),
            plt.Line2D([0], [0], color=strength_day_color, lw=2, linestyle='--', 
                      label=f'Rest ({self.target_rest} kcal)')
        ]
        
        # Add legends - macros on left, targets on right, weight in middle if available
        macro_leg = ax.legend(handles=macro_legend, loc='lower left', 
                              bbox_to_anchor=(0.0, -0.2), ncol=3, 
                              frameon=False, fontsize=9)
        ax.add_artist(macro_leg)
        
        # Add weight legend in the middle if available
        if weight_legend:
            weight_leg = ax.legend(handles=weight_legend, loc='lower center', 
                                  bbox_to_anchor=(0.5, -0.2), ncol=1, 
                                  frameon=False, fontsize=9)
            ax.add_artist(weight_leg)
        
        target_leg = ax.legend(handles=target_legend, loc='lower right', 
                               bbox_to_anchor=(1.0, -0.2), ncol=2, 
                               frameon=False, fontsize=9)
        
        # Style the legend text
        legends = [macro_leg, target_leg]
        if weight_legend:
            legends.append(weight_leg)
            
        for leg in legends:
            for text in leg.get_texts():
                text.set_color("#666666")
        
        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path




class MacroRatioChartGenerator(ChartGenerator):
    """Generates HTML/CSS visualization for macronutrient ratios."""
    
    def generate_html(self, protein_pct: float, carbs_pct: float, fat_pct: float) -> str:
        """
        Generate HTML for macronutrient ratio visualization.
        
        Args:
            protein_pct: Protein percentage (0-100)
            carbs_pct: Carbohydrate percentage (0-100)
            fat_pct: Fat percentage (0-100)
            
        Returns:
            HTML string for the visualization
        """
        # Visual progress bar with text inside bars
        html = ["<div class='progress-container'>"]
        
        # Round values to 1 decimal place for consistency
        protein_pct_rounded = round(protein_pct, 1)
        carbs_pct_rounded = round(carbs_pct, 1)
        fat_pct_rounded = round(fat_pct, 1)
        
        # Add text inside each bar section with macro names on same line as percentage
        html.append(f"  <div class='progress-protein' style='width: {protein_pct_rounded}%'>" + 
                   (f"<span class='macro-text'>Protein {protein_pct_rounded}%</span>" if protein_pct >= ReportingConfig.THRESHOLDS['macro_label_full'] else 
                    f"<span class='macro-text'>{protein_pct_rounded}%</span>" if protein_pct >= ReportingConfig.THRESHOLDS['macro_label_percent'] else "") + 
                   "</div>" +
                   f"<div class='progress-carbs' style='width: {carbs_pct_rounded}%'>" + 
                   (f"<span class='macro-text'>Carbs {carbs_pct_rounded}%</span>" if carbs_pct >= ReportingConfig.THRESHOLDS['macro_label_full'] else 
                    f"<span class='macro-text'>{carbs_pct_rounded}%</span>" if carbs_pct >= ReportingConfig.THRESHOLDS['macro_label_percent'] else "") + 
                   "</div>" +
                   f"<div class='progress-fat' style='width: {fat_pct_rounded}%'>" + 
                   (f"<span class='macro-text'>Fat {fat_pct_rounded}%</span>" if fat_pct >= ReportingConfig.THRESHOLDS['macro_label_full'] else 
                    f"<span class='macro-text'>{fat_pct_rounded}%</span>" if fat_pct >= ReportingConfig.THRESHOLDS['macro_label_percent'] else "") + 
                   "</div>")
        
        html.append("</div>")
        
        return "\n".join(html)
