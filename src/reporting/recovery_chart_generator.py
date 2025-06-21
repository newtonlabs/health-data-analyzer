import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple

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
        fig, ax1 = self._setup_chart_figure(figsize=(10, ReportingConfig.STYLING['chart_height']))
        
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
                        color=ReportingConfig.COLORS['text'], fontsize=ReportingConfig.STYLING['default_font_size'])
        
        # Add legend at the bottom left with rectangle patches to match nutrition chart
        recovery_legend = [
            plt.Rectangle((0,0), 1, 1, color=self.green_color, alpha=ReportingConfig.STYLING['bar_alpha'], label=f"High Recovery (≥{self.recovery_threshold_high})"),
            plt.Rectangle((0,0), 1, 1, color=self.yellow_color, alpha=ReportingConfig.STYLING['bar_alpha'], label=f"Moderate Recovery ({self.recovery_threshold_medium}-{self.recovery_threshold_high-1})"),
            plt.Rectangle((0,0), 1, 1, color=self.red_color, alpha=ReportingConfig.STYLING['bar_alpha'], label=f"Low Recovery (≤{self.recovery_threshold_low})")
        ]
        
        # Add legend at the bottom left with 3 columns for recovery levels
        recovery_leg = ax1.legend(handles=recovery_legend, loc='lower left', 
                                 bbox_to_anchor=(0.0, ReportingConfig.STYLING['legend_vertical_offset']), ncol=ReportingConfig.STYLING['legend_columns'], 
                                 frameon=False, fontsize=ReportingConfig.STYLING['legend_font_size'])
        
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
                                        marker='o', markersize=ReportingConfig.STYLING['default_marker_size'],
                                        label="Sleep Actual")
            
            # Use bright blue for sleep need line to match nutrition chart target lines
            sleep_need_line, = ax2.plot(x_numeric, df['sleep_need'], 
                                      color=ReportingConfig.COLORS['sleep_need'], linestyle='-', linewidth=ReportingConfig.STYLING['line_thickness'], 
                                      marker='s', markersize=ReportingConfig.STYLING['default_marker_size'],
                                      label="Sleep Need")
            
            # Set up secondary axis for sleep hours
            max_sleep = max(df['sleep_need'].max(), df['sleep_actual'].max())
            
            self._style_axes(
                ax=ax2,
                y_lim=(0, max_sleep * 1.2),
                y_label='Hours',
                tick_label_color=ReportingConfig.COLORS['text'],
                axis_label_color=ReportingConfig.COLORS['text'],
                font_size=ReportingConfig.STYLING['default_font_size'],
                tick_font_size=ReportingConfig.STYLING['tick_font_size'],
                spines_to_hide=['top', 'left', 'bottom'],
                spines_to_color={'right': ReportingConfig.COLORS['grid']},
                secondary_ax=ax2 # Pass ax2 as secondary_ax to style its ticks
            )
            
            # Add legend at the bottom right, similar to nutrition chart
            sleep_legend = [
                plt.Line2D([0], [0], color=ReportingConfig.COLORS['sleep_need'], lw=ReportingConfig.STYLING['default_line_width'], linestyle='-', marker='s', markersize=ReportingConfig.STYLING['default_marker_size'],
                          label="Sleep Need"),
                plt.Line2D([0], [0], color=ReportingConfig.COLORS['sleep_actual'], lw=ReportingConfig.STYLING['default_line_width'], linestyle='--', marker='o', markersize=ReportingConfig.STYLING['default_marker_size'],
                          label="Sleep Actual")
            ]
            
            # Add legend at the bottom right
            sleep_leg = ax2.legend(handles=sleep_legend, loc='lower right', 
                                 bbox_to_anchor=(1.0, ReportingConfig.STYLING['legend_vertical_offset']), ncol=2, 
                                 frameon=False, fontsize=ReportingConfig.STYLING['default_font_size'])
            
            # Style the legend text
            for text in sleep_leg.get_texts():
                text.set_color(ReportingConfig.COLORS['text'])
                
            # Make sure the sleep legend is added after the recovery legend
            ax2.add_artist(sleep_leg)
        
        # Set up primary axis styling
        day_labels = DateUtils.get_day_of_week_labels(df['date'].tolist())

        self._style_axes(
            ax=ax1,
            x_labels=day_labels,
            x_ticks=x_numeric,
            y_lim=(0, 100),
            y_label='Recovery',
            x_label='',
            tick_label_color=ReportingConfig.COLORS['text'],
            axis_label_color=ReportingConfig.COLORS['text'],
            font_size=ReportingConfig.STYLING['default_font_size'],
            tick_font_size=ReportingConfig.STYLING['tick_font_size'],
            grid_line_width=ReportingConfig.STYLING['grid_line_width'],
            grid_opacity=ReportingConfig.STYLING['grid_opacity'],
            spines_to_hide=['top', 'right'],
            spines_to_color={'left': ReportingConfig.COLORS['grid'], 'bottom': ReportingConfig.COLORS['grid']}
        )
        
        return self._save_chart(fig, filename, extra_artists=(recovery_leg, sleep_leg) if has_sleep_data else (recovery_leg,))
