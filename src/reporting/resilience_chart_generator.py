"""Resilience chart generator module."""
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .chart_generator import ChartGenerator
from .reporting_config import ReportingConfig
from src.analysis.analyzer_config import AnalyzerConfig

class ResilienceChartGenerator(ChartGenerator):
    """
    Generates a resilience chart image from a DataFrame containing resilience data.
    Output is saved as a PNG in data/charts/.
    """
    
    def __init__(self, charts_dir: Optional[str] = None):
        """
        Initialize resilience chart generator with output directory.
        
        Args:
            charts_dir: Directory to save chart images
        """
        super().__init__(charts_dir)
        
        # Get resilience bands from analyzer_config
        # Use lowercase keys for internal logic but uppercase for display
        self.resilience_bands = {}
        for level, score in AnalyzerConfig.RESILIENCE_LEVEL_SCORES.items():
            # Only include the main levels, skip legacy mappings
            if level in ['exceptional', 'strong', 'solid', 'adequate', 'limited']:
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
        if not {'date', 'resilience_score'}.issubset(df.columns):
            raise ValueError("DataFrame must contain 'date' and 'resilience_score' columns")

        # Plot setup - half the height of recovery chart but same width
        fig, ax = plt.subplots(figsize=(10, ReportingConfig.STYLING['chart_height'] / 2))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Adjust margins to match recovery chart
        plt.subplots_adjust(right=0.82, left=0.12)  # Match recovery chart margins
        
        # Get the dates and format them consistently with the recovery chart
        # Format as MM-DD (DAY) like "06-12 (Thu)"
        day_labels = []
        for date_str in df['date']:
            try:
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%m-%d']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        # Format as MM-DD only
                        day_labels.append(dt.strftime('%m-%d'))
                        break
                    except ValueError:
                        continue
                else:
                    # If no format works, use the date string as is
                    day_labels.append(date_str)
            except Exception:
                # Fallback if any error occurs
                day_labels.append(date_str)
        
        # Set up x-axis values
        x_numeric = np.arange(len(df['date']))
        
        # Plot the line in a medium gray
        ax.plot(x_numeric, df['resilience_score'], 
               color=ReportingConfig.COLORS['text'], 
               marker='o', markersize=4,
               linewidth=ReportingConfig.STYLING['line_thickness'],
               zorder=3)

        # Add horizontal band lines and labels
        for label, score in self.resilience_bands.items():
            # Blue line for 'STRONG', others in dark gray
            color = ReportingConfig.COLORS['resilience_strong'] if label == 'STRONG' else ReportingConfig.COLORS['grid']
            # Solid line for the baseline (LIMITED = 0), dashed for others
            linestyle = '-' if score == 0 else '--'
            # Line thickness and opacity
            linewidth = 1.2 if label == 'STRONG' else 0.8
            alpha = 1.0 if label == 'STRONG' else ReportingConfig.STYLING['grid_opacity']
            
            ax.axhline(score, 
                      color=color, 
                      linestyle=linestyle, 
                      linewidth=linewidth,
                      alpha=alpha,
                      zorder=1)
            ax.text(-0.75, score, label, 
                   va='center', ha='right', 
                   fontsize=8, 
                   color=color,
                   fontweight='bold')

        # Set up axes
        ax.set_ylim(0, 100)
        ax.set_xlim(-0.5, len(df['date']) - 0.5)
        
        # Create a twin axis on the right for score values
        ax2 = ax.twinx()
        ax2.set_ylim(0, 100)  # Score scale from 0-100
        
        # Set up score ticks at resilience band thresholds (equal zones)
        score_ticks = [0, 20, 40, 60, 80]
        ax2.set_yticks(score_ticks)
        ax2.set_yticklabels(['' for _ in score_ticks])  # Use blank strings for labels
        
        # Add 'Score' label to right axis
        ax2.set_ylabel('Score', fontsize=9, color=ReportingConfig.COLORS['text'], labelpad=10)
        
        # Style the right y-axis
        ax2.tick_params(axis='y', colors=ReportingConfig.COLORS['text'], length=3)
        ax2.spines['right'].set_visible(True)
        ax2.spines['right'].set_color(ReportingConfig.COLORS['grid'])
        
        # Hide main y-axis completely
        ax.yaxis.set_visible(False)
        
        # Set x-axis ticks and labels
        ax.set_xticks(x_numeric)
        ax.set_xticklabels(day_labels, color=ReportingConfig.COLORS['text'], fontsize=9)

        # Add grid for x-axis only
        ax.grid(axis='x', 
               color='#EDEDED', 
               linestyle='-', 
               linewidth=0.5,
               zorder=0)
        
        # Style the spines (borders) to match recovery chart
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(True)
        ax.spines['right'].set_visible(True)
        
        ax.spines['left'].set_color(ReportingConfig.COLORS['grid'])
        ax.spines['right'].set_color(ReportingConfig.COLORS['grid'])
        ax.spines['bottom'].set_color('#A9A9A9')  # Slightly darker for bottom border
        
        # Style the right axis spine to match recovery chart
        ax2.spines['top'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['right'].set_visible(True)
        ax2.spines['right'].set_color(ReportingConfig.COLORS['grid'])

        # Save the chart with the same settings as recovery chart
        output_path = os.path.join(self.charts_dir, filename)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
