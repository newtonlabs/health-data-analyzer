"""Utility for converting markdown to PDF."""
import os
import base64
from pathlib import Path
from datetime import datetime, timedelta
from markdown import markdown
from weasyprint import HTML

from .reporting_config import ReportingConfig
from .html_templates import get_report_template

class PDFConverter:
    """PDF converter class for converting markdown to PDF."""
    
    def __init__(self):
        """Initialize the PDF converter."""
        # Set up paths
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.assets_dir = os.path.join(self.project_root, 'assets')
    
    def markdown_to_pdf(
        self,
        markdown_file: str,
        output_file: str
    ) -> str:
        # Read markdown content
        with open(markdown_file, 'r') as f:
            markdown_content = f.read()
        
        # No need to extract title anymore as it will be handled by the HTML template
        # Just pass the report dates to the template
        
        # Get the report dates from the filename (format: YYYY-MM-DD-weekly-status.md)
        report_date_str = os.path.basename(markdown_file).split('-weekly-status')[0]
        
        # Calculate the start date (7 days before the report date)
        try:
            report_end_date = datetime.strptime(report_date_str, '%Y-%m-%d')
            report_start_date = report_end_date - timedelta(days=6)
            report_start = report_start_date.strftime('%m-%d')
            report_end = report_end_date.strftime('%m-%d')
        except:
            # Fallback if we can't parse the date
            report_start = ''
            report_end = ''
        
        # The title will be set in the HTML template
        title = ''
        
        # Convert markdown to HTML
        html_content = markdown(
            markdown_content,
            extensions=[
                'tables',
                'fenced_code',
                'nl2br',
                'sane_lists'
            ]
        )
        
        # Read and encode logo
        logo_path = os.path.join(self.assets_dir, 'rb-logo.webp')
        logo_data = ""
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
        
        logo_html = f'<img src="data:image/webp;base64,{logo_data}" alt="Logo">' if logo_data else ''
        
        # Get color values from ReportingConfig
        protein_color = ReportingConfig.COLORS['protein']
        carbs_color = ReportingConfig.COLORS['carbs']
        fat_color = ReportingConfig.COLORS['fat']
        text_color = ReportingConfig.COLORS['text']
        heading_color = ReportingConfig.COLORS['sleep_actual']  # Using the dark red color
        
        # Get recovery color values
        recovery_high_color = ReportingConfig.COLORS['recovery_high']
        recovery_medium_color = ReportingConfig.COLORS['recovery_medium']
        recovery_low_color = ReportingConfig.COLORS['recovery_low']
        
        # Get the HTML template and format it with our variables
        template = get_report_template()
        formatted_html = template.format(
            logo_html=logo_html,
            report_start=report_start,
            report_end=report_end,
            html_content=html_content,
            protein_color=protein_color,
            carbs_color=carbs_color,
            fat_color=fat_color,
            text_color=text_color,
            heading_color=heading_color,
            recovery_high_color=recovery_high_color,
            recovery_medium_color=recovery_medium_color,
            recovery_low_color=recovery_low_color
        )
        
        # Set base_url to the directory containing the markdown file
        # This ensures relative image paths are resolved correctly
        markdown_dir = os.path.dirname(os.path.abspath(markdown_file))
        html = HTML(string=formatted_html, base_url=markdown_dir)
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF - CSS is already embedded in the HTML
        html.write_pdf(output_file)
        
        return output_file
    
    def convert(self, markdown_file: str, output_file: str) -> str:
        """Convert markdown file to PDF (alias for markdown_to_pdf).
        
        Args:
            markdown_file: Path to markdown file
            output_file: Path to output PDF file
            
        Returns:
            Path to generated PDF file
        """
        return self.markdown_to_pdf(markdown_file, output_file)
