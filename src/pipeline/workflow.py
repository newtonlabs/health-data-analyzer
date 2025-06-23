"""Workflow for orchestrating health data processing."""

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

from src.analysis.processor import Processor
from src.analysis.aggregator import Aggregator
from src.sources.clients.hevy import HevyClient
from src.sources.clients.onedrive import OneDriveClient
from src.sources.clients.oura import OuraClient
from src.sources.token_manager import TokenManager
from src.sources.clients.whoop import WhoopClient
from src.sources.clients.withings import WithingsClient
from src.reporting.pdf_converter import PDFConverter
from src.reporting.report_generator import ReportGenerator
from src.utils.date_utils import DateUtils
from src.utils.logging_utils import HealthLogger
from src.utils.progress_indicators import ProgressIndicator


class Workflow:
    """Main workflow for health data processing."""

    def __init__(self, skip_auth: bool = False):
        """Initialize workflow components.

        Args:
            skip_auth: If True, skip authentication with external services
        """
        # Initialize logger
        self.logger = HealthLogger(__name__)

        # Initialize clients
        self.whoop = WhoopClient()
        self.oura = OuraClient()
        self.withings = WithingsClient()
        self.hevy = HevyClient()
        self.storage = OneDriveClient()

        # Initialize data processing components
        self.processor = Processor()
        self.aggregator = Aggregator(self.processor)
        self.report_gen = ReportGenerator(self.aggregator)
        self.converter = PDFConverter()

        # Skip authentication if requested
        self.skip_auth = skip_auth
        if not skip_auth:
            self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with all services."""
        # Authenticate with OneDrive
        self.storage.authenticate()
        
        # Authenticate with Oura
        if not self.oura.is_authenticated():
            self.logger.logger.error("Failed to authenticate with Oura")
            sys.exit(1)
            
        # Authenticate with Whoop
        if not self.whoop.is_authenticated():
            if not self.whoop.authenticate():
                auth_code = input(
                    "Please enter the authorization code from the redirected URL: "
                )
                try:
                    self.whoop.get_token(auth_code, self.whoop.state)
                    self.logger.logger.info("Whoop authentication successful!")
                except Exception as e:
                    self.logger.logger.error(f"Failed to authenticate with Whoop: {e}")
                    sys.exit(1)
                    
        # Authenticate with Withings
        if not self.withings.is_authenticated():
            if not self.withings.authenticate():
                auth_code = input(
                    "Please enter the authorization code from the redirected URL: "
                )
                try:
                    self.withings.get_token(auth_code, self.withings.state)
                    self.logger.logger.info("Withings authentication successful!")
                except Exception as e:
                    self.logger.logger.error(f"Failed to authenticate with Withings: {e}")
                    sys.exit(1)
                    
        # Authenticate with Hevy
        self.hevy.authenticate()

    def run(
        self,
        fetch: bool = False,
        pdf: bool = False,
        upload: bool = False,
        days: int = 7,
    ) -> None:
        """Run the health data workflow.

        Args:
            fetch: Whether to fetch new data
            pdf: Whether to generate a PDF report
            upload: Whether to upload the report to OneDrive
            days: Number of days to include in the report
        """
        # Calculate date range for new data fetching
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)

        # Format dates for display
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        self.logger.logger.info(f"Date range: {start_str} to {end_str}")

        # Create output filename based on the current date if fetching new data
        if fetch:
            report_date = end_date.strftime("%Y-%m-%d")
            md_filename = f"{report_date}-weekly-status.md"
            pdf_filename = f"{report_date}-weekly-status.pdf"
        else:
            # If not fetching new data, find the most recent report file
            data_dir = "data"
            report_files = [f for f in os.listdir(data_dir) if f.endswith("-weekly-status.md")]
            
            if not report_files:
                self.logger.logger.error("No report files found in data directory")
                return
                
            # Sort by modification time (most recent first)
            report_files.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
            md_filename = report_files[0]
            pdf_filename = md_filename.replace(".md", ".pdf")
            
        md_path = os.path.join("data", md_filename)
        pdf_path = os.path.join("data", pdf_filename)

        # Fetch and process data
        if fetch:
            self._fetch_data(start_date, end_date)
            self._generate_report(md_path)

        # Generate PDF
        if pdf:
            self.create_pdf(md_path, pdf_path)

        # Upload to OneDrive
        if upload and not self.skip_auth:
            self._upload_to_onedrive(pdf_path)

    def _fetch_data(self, start_date: datetime, end_date: datetime) -> None:
        """Fetch and process data from all sources.

        Args:
            start_date: Start date for data fetching
            end_date: End date for data fetching
        """
        if self.skip_auth:
            self.logger.logger.warning("Skipping data fetching (auth disabled)")
            return

        ProgressIndicator.section_header("Data Collection")

        # Fetch Oura data
        ProgressIndicator.step_start("Fetching Oura data from API")
        oura_data = self.oura.get_data(start_date, end_date)
        self.processor.oura_data = self.processor.process_oura_data(oura_data)
        ProgressIndicator.step_complete()

        # Fetch Whoop data
        ProgressIndicator.step_start("Fetching Whoop data from API")
        whoop_data = self.whoop.get_data(start_date, end_date)
        self.processor.whoop_data = self.processor.process_whoop_data(whoop_data)
        ProgressIndicator.step_complete()

        # Fetch Withings data
        ProgressIndicator.step_start("Fetching Withings weight data from API")
        withings_data = self.withings.get_data(start_date, end_date)
        self.processor.withings_data = self.processor.process_withings_data(
            withings_data, start_date, end_date
        )
        ProgressIndicator.step_complete()

        # Fetch Hevy data
        ProgressIndicator.step_start("Fetching Hevy workout data from API")
        hevy_data = self.hevy.get_workouts(start_date, end_date)
        workout_df, exercise_df = self.processor.process_hevy_data(hevy_data, end_date)
        self.processor.hevy_data = {"workouts": workout_df, "exercises": exercise_df}
        ProgressIndicator.step_complete()

        # Load nutrition data from file
        ProgressIndicator.step_start("Fetching nutrition data from file")
        ProgressIndicator.step_complete()

        # Transform data
        ProgressIndicator.step_start("Transforming and normalizing the data")
        ProgressIndicator.step_complete()

    def _generate_report(self, output_path: str) -> None:
        """Generate markdown report.

        Args:
            output_path: Path to save the report
        """
        ProgressIndicator.step_start("Converting the data into a markdown report")

        # Generate the report
        self.report_gen.generate_report(output_path)

        ProgressIndicator.step_complete()
        
        ProgressIndicator.section_header("Report Generation Complete")
        ProgressIndicator.step_complete(f"Markdown report saved to {output_path}")
        ProgressIndicator.bullet_item("Please open with your editor and make adjustments as needed")
        ProgressIndicator.bullet_item("Run with --pdf to see the final output and --upload to create a OneDrive link")

    def create_pdf(self, md_path: str, pdf_path: str) -> None:
        """Convert markdown report to PDF.

        Args:
            md_path: Path to markdown report
            pdf_path: Path to save PDF
        """
        ProgressIndicator.section_header("PDF Conversion")
        ProgressIndicator.step_start("Creating PDF from markdown report")

        # Convert to PDF
        self.converter.markdown_to_pdf(md_path, pdf_path)

        ProgressIndicator.step_complete(f"PDF saved to {pdf_path}")

    def _upload_to_onedrive(self, file_path: str) -> None:
        """Upload file to OneDrive.

        Args:
            file_path: Path to file to upload
        """
        ProgressIndicator.section_header("OneDrive Upload")
        ProgressIndicator.step_start(f"Uploading {os.path.basename(file_path)}")

        # Upload to OneDrive
        result = self.storage.upload_file(file_path)

        if result and "webUrl" in result:
            ProgressIndicator.step_complete()
            ProgressIndicator.step_complete(f"OneDrive link: {result['webUrl']}")
        else:
            ProgressIndicator.step_error("Failed to upload to OneDrive")
