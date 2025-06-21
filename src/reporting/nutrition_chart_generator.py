import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .reporting_config import ReportingConfig
from src.utils.date_utils import DateUtils
from .chart_generator import ChartGenerator

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
                
            # Create protein bar (bottom) - no border, higher zorder to be in front of grid
            p_bar = ax.bar(x_pos, prot, width, label='Protein' if i == 0 else "", 
                          color=protein_color, alpha=1.0, zorder=3)
            bars_protein.append(p_bar)
            
            # Create carbs bar (middle) - no border, higher zorder to be in front of grid
            c_bar = ax.bar(x_pos, carb, width, bottom=prot, 
                          label='Carbs' if i == 0 else "", 
                          color=carbs_color, alpha=1.0, zorder=3)
            bars_carbs.append(c_bar)
            
            # Create fat bar (top) - no border, higher zorder to be in front of grid
            f_bar = ax.bar(x_pos, f, width, bottom=prot+carb, 
                          label='Fat' if i == 0 else "", 
                          color=fat_color, alpha=1.0, zorder=3)
            bars_fat.append(f_bar)
        
        # Add calorie labels at the bottom of each bar (much higher up to avoid clipping)
        for i, cal in enumerate(total_cals):
            if cal > 0:  # Only add labels for non-zero values
                ax.annotate(f'{cal:.0f}',
                            xy=(x_numeric[i], 120),  # Position even higher above the x-axis
                            xytext=(0, 0),  # No offset
                            textcoords="offset points",
                            ha='center', va='center',
                            color='white', fontsize=9, fontweight='bold',\
                            zorder=10)  # Ensure it's on top
        
        # Draw target lines with colors matching macronutrients
        strength_line_handles = []
        rest_line_handles = []
        
        for i, act in enumerate(df['activity']):
            y = self.target_strength if act == "Strength" else self.target_rest
            line_style = '-' if act == "Strength" else '--'
            # Use bright blue for both strength and rest targets
            line_color = strength_day_color  # Same bright blue for both
            
            # Calculate start and end points for the target line
            x_start = x_numeric[i] - width*0.7
            x_end = x_numeric[i] + width*0.7
            
            # Draw the horizontal line
            line = ax.hlines(y, x_start, x_end, 
                      color=line_color, linewidth=1.5, linestyle=line_style, zorder=4)
            
            # Add markers at each end of the line
            ax.plot([x_start, x_end], [y, y], 'o', color=line_color, 
                   markersize=4, zorder=5)
            
            # Store handles for legend
            if act == "Strength" and not strength_line_handles:
                strength_line_handles.append(line)
            elif act == "Rest" and not rest_line_handles:
                rest_line_handles.append(line)
        
        # Axis config - start at 0 to make bars touch x-axis
        max_cal = max(total_cals.max() if not total_cals.empty else 0, self.target_strength)
        ax.set_ylim(0, max_cal + 300)  # No negative space so bars touch x-axis
        ax.set_xticks(x_numeric)
        
        day_labels = DateUtils.get_day_of_week_labels(df['date'].tolist())
        
        ax.set_xticklabels(day_labels)
        
        # Minimal styling with no labels
        ax.set_xlabel("", color='#666666', fontsize=9)
        ax.set_ylabel("Calories Consumed", color=ReportingConfig.COLORS['text'], fontsize=9)
        ax.tick_params(axis='both', colors='#666666', labelsize=8)
        
        # Configure spines/borders - consistent with recovery chart
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_color(ReportingConfig.COLORS['grid'])
        ax.spines['bottom'].set_color(ReportingConfig.COLORS['grid'])
        
        # Grid styling - both horizontal and vertical (behind the bars)
        ax.grid(True, linestyle=':', linewidth=0.7, alpha=ReportingConfig.STYLING['grid_opacity'], color=ReportingConfig.COLORS['grid'])

        # Create legend for macros
        macro_legend = [
            plt.Rectangle((0,0), 1, 1, color=protein_color, alpha=1.0, label='Protein'),
            plt.Rectangle((0,0), 1, 1, color=carbs_color, alpha=1.0, label='Carbs'),
            plt.Rectangle((0,0), 1, 1, color=fat_color, alpha=1.0, label='Fat')
        ]
        
        # Create legend for activity targets
        target_legend = [
            plt.Line2D([0], [0], color=strength_day_color, lw=1.5, linestyle='-', marker='o', markersize=4, label=f'Strength Target ({self.target_strength} cal)'),
            plt.Line2D([0], [0], color=strength_day_color, lw=1.5, linestyle='--', marker='o', markersize=4, label=f'Rest Target ({self.target_rest} cal)')
        ]

        # Initialize combined line legends with target legends
        combined_line_legends = list(target_legend)

        # Add weight data if available and create its legend
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
                        ax2.plot(np.array(weight_indices), weight_values, 'o-', 
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
                        
                        # Style the y-axis label and ticks with text color - use title case
                        ax2.set_ylabel('Weight (lbs)', color=text_color, fontsize=9)
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
                        
                        # Add weight trend line to legend - use title case
                        weight_legend = [plt.Line2D([0], [0], color=trend_color, lw=2, linestyle='--', 
                                                   marker='o', markersize=4, label='Weight Trend')] 
                        
                        combined_line_legends.extend(weight_legend)
        
        # Create and place macro legend (left)
        macro_leg = ax.legend(handles=macro_legend, loc='lower left', bbox_to_anchor=(0.0, -0.2), ncol=3, frameon=False, fontsize=9)
        
        # Create and place combined line legend (right)
        line_leg = ax.legend(handles=combined_line_legends, loc='lower right', bbox_to_anchor=(1.0, -0.2), ncol=len(combined_line_legends), frameon=False, fontsize=9)
        
        # Add legends as artists to the figure
        ax.add_artist(macro_leg)
        ax.add_artist(line_leg)

        # Style the legend text
        for text in macro_leg.get_texts():
            text.set_color(ReportingConfig.COLORS['text'])
        for text in line_leg.get_texts():
            text.set_color(ReportingConfig.COLORS['text'])
        
        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', bbox_extra_artists=(macro_leg, line_leg))
        plt.close()
        return output_path