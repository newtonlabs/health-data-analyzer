import os
from typing import Optional

class ChartGenerator:
    """Base class for chart generators."""
    
    def __init__(self, charts_dir: Optional[str] = None):
        """Initialize chart generator with output directory."""
        self.charts_dir = charts_dir or os.path.join("data", "charts")
        os.makedirs(self.charts_dir, exist_ok=True)
