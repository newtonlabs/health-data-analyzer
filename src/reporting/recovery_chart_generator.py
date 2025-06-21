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
from src.utils.date_utils import DateUtils
from .chart_generator import ChartGenerator

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
        day_labels = DateUtils.get_day_of_week_labels(df['date'].tolist())
        
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
