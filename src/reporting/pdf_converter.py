"""Utility for converting markdown to PDF."""

import base64
import os
from datetime import datetime, timedelta
from pathlib import Path

from markdown import markdown
from weasyprint import HTML

from src.app_config import AppConfig

from .html_templates import get_report_template


class PDFConverter:
    """PDF converter class for converting markdown to PDF."""

    def __init__(self):
        """Initialize the PDF converter."""
        # Set up paths
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.assets_dir = os.path.join(self.project_root, "assets")

    def markdown_to_pdf(self, markdown_file: str, output_file: str) -> str:
        # Read markdown content
        with open(markdown_file) as f:
            markdown_content = f.read()

        # No need to extract title anymore as it will be handled by the HTML template
        # Just pass the report dates to the template

        # Get the report dates from the filename (format: health_report_YYYY-MM-DD.md)
        filename = os.path.basename(markdown_file)
        
        # Extract date from health_report_YYYY-MM-DD.md format - fail fast if not correct format
        if not (filename.startswith('health_report_') and filename.endswith('.md')):
            raise ValueError(f"Expected filename format 'health_report_YYYY-MM-DD.md', got: {filename}")
        
        # Extract YYYY-MM-DD from health_report_YYYY-MM-DD.md
        date_part = filename[len('health_report_'):-len('.md')]
        report_end_date = datetime.strptime(date_part, "%Y-%m-%d")
        
        # Calculate the start date (7 days before the report date)
        report_start_date = report_end_date - timedelta(days=6)
        report_start = report_start_date.strftime("%m-%d")
        report_end = report_end_date.strftime("%m-%d")

        # The title will be set in the HTML template
        title = ""

        # Convert markdown to HTML
        html_content = markdown(
            markdown_content,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        )

        # Read and encode logo
        logo_path = os.path.join(self.assets_dir, "rb-logo.webp")
        logo_data = ""
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode("utf-8")

        logo_html = (
            f'<img src="data:image/webp;base64,{logo_data}" alt="Logo">'
            if logo_data
            else ""
        )

        # Get color values from AppConfig
        protein_color = AppConfig.REPORTING_COLORS["protein"]
        carbs_color = AppConfig.REPORTING_COLORS["carbs"]
        fat_color = AppConfig.REPORTING_COLORS["fat"]
        text_color = AppConfig.REPORTING_COLORS["text"]
        heading_color = AppConfig.REPORTING_COLORS[
            "sleep_actual"
        ]  # Using the dark red color

        # Recovery colors for badges
        recovery_high_color = AppConfig.REPORTING_COLORS["recovery_high"]
        recovery_medium_color = AppConfig.REPORTING_COLORS["recovery_medium"]
        recovery_low_color = AppConfig.REPORTING_COLORS["recovery_low"]

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
            recovery_low_color=recovery_low_color,
        )

        # Set base_url to reports directory since charts are now co-located
        # Both charts and markdown are in data/05_reports/ structure
        markdown_dir = os.path.dirname(os.path.abspath(markdown_file))
        html = HTML(string=formatted_html, base_url=markdown_dir)

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate PDF - CSS is already embedded in the HTML
        html.write_pdf(output_file)

        return output_file
