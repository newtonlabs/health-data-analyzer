"""Configuration for reporting components."""
from typing import Dict, List

class ReportingConfig:
    """Configuration for reporting components."""
    
    # Chart colors
    COLORS = {
        # Recovery chart colors
        'recovery_high': '#2ecc71',    # Green for high recovery (≥70)
        'recovery_medium': '#f1c40f',  # Yellow for moderate recovery (50-69)
        'recovery_low': '#e74c3c',     # Red for low recovery scores (<50)
        
        # Sleep line colors
        'sleep_need': '#1E88E5',       # Blue for sleep need line
        'sleep_actual': '#7B1F1F',     # Dark red for sleep actual line
        
        # Resilience chart colors
        'resilience_strong': '#007BFF', # Blue for strong resilience target line
        
        # Macro ratio colors
        'protein': '#7B1F1F',          # Dark red for protein
        'carbs': '#333333',            # Black for carbs
        'fat': '#999999',              # Gray for fat
        
        # Text and UI colors
        'text': '#666666',             # Gray for text elements
        'grid': '#cccccc',             # Light gray for grid lines
    }
    
    # Chart thresholds
    THRESHOLDS = {
        # Recovery thresholds
        'recovery_high': 66,           # High recovery threshold (≥66)
        'recovery_medium': 34,         # Medium recovery threshold (34-65)
        'recovery_low': 33,            # Low recovery threshold (≤33)
        
        # Macro ratio label thresholds
        'macro_label_full': 15,        # Show full label if segment ≥15%
        'macro_label_percent': 8,      # Show percentage only if segment between 8-15%
    }
    
    # CSS has been moved to html_templates.py
    
    # Chart styling
    STYLING = {
        'bar_alpha': 0.7,              # Transparency for bars
        'line_thickness': 1.5,         # Line thickness for sleep lines
        'chart_height': 3.5,           # Standard chart height for recovery and nutrition charts
        'chart_height_compact': 2.8,   # Compact chart height for minimalist design
        'grid_opacity': 0.5,           # Grid line opacity
    }
    
    # Caloric targets by activity type
    CALORIC_TARGETS = {
        'strength': 1800,  # Target calories for strength training days
        'rest': 1800       # Target calories for rest days
    }

