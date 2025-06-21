"""Health data pipeline for collecting and processing health data."""
import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.data_sources.oura_client import OuraClient
from src.data_sources.whoop_client import WhoopClient
from src.data_sources.withings_client import WithingsClient
from src.analysis.health_data_processor import HealthDataProcessor
from src.analysis.metrics_aggregator import MetricsAggregator
from src.reporting.report_generator import ReportGenerator
from src.storage.onedrive_client import OneDriveClient
from src.reporting.pdf_converter import PDFConverter
from src.utils.logging_utils import HealthLogger, DEBUG_MODE
from src.utils.date_utils import DateUtils
from src.utils.progress_indicators import ProgressIndicator

class HealthPipeline:
    """Main pipeline for health data processing."""
    
    def __init__(self, skip_auth: bool = False):
        """Initialize pipeline components.
        
        Args:
            skip_auth: If True, skip authentication with external services
        """
        # Initialize logger
        self.logger = HealthLogger(__name__)
        
        # Initialize clients
        if not skip_auth:
            self.whoop = WhoopClient()
            self.oura = OuraClient()
            self.withings = WithingsClient()
            self.storage = OneDriveClient()
        
        # Initialize data processing components
        self.processor = HealthDataProcessor()
        self.aggregator = MetricsAggregator(self.processor)
        self.report_gen = ReportGenerator(self.aggregator)
        self.converter = PDFConverter()
        
        # Authenticate with services if needed
        if not skip_auth:
            self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with all services."""
        # Authenticate with Oura
        if not self.oura.is_authenticated():
            self.logger.log_skipped_date(None, "Failed to authenticate with Oura")
            sys.exit(1)
        
        # Authenticate with Whoop
        if not self.whoop.is_authenticated():
            if not self.whoop.authenticate():
                self.logger.log_skipped_date(None, "Failed to authenticate with Whoop")
                sys.exit(1)
                
        # Authenticate with Withings
        if not self.withings.is_authenticated():
            if not self.withings.authenticate():
                self.logger.log_skipped_date(None, "Failed to authenticate with Withings")
                sys.exit(1)
        
        # Authenticate with OneDrive
        if not self.storage.authenticate():
            self.logger.log_skipped_date(None, "Failed to authenticate with OneDrive")
            sys.exit(1)
    
    def fetch_api_data(self, fetch_start: datetime, fetch_end: datetime) -> Dict[str, Any]:
        """Fetch data from Oura, Whoop, and Withings APIs.
        
        Args:
            fetch_start: Start date for data fetch
            fetch_end: End date for data fetch
            
        Returns:
            Dictionary with raw API data
        """
        self.logger.debug(f"Fetching data date range: {fetch_start.date()} to {fetch_end.date()}")
        # Fetch data from APIs
        if not DEBUG_MODE:
            ProgressIndicator.step_start("Fetching Oura data from API")
        oura_raw = {
            'activity': self.oura.get_activity_data(fetch_start, fetch_end),
            'resilience': self.oura.get_resilience_data(fetch_start, fetch_end)
        }
        if not DEBUG_MODE:
            ProgressIndicator.step_complete()
        
        if not DEBUG_MODE:
            ProgressIndicator.step_start("Fetching Whoop data from API")
        whoop_raw = {
            'workouts': self.whoop.get_workouts(fetch_start, fetch_end),
            'recovery': self.whoop.get_recovery_data(fetch_start, fetch_end),
            'sleep': self.whoop.get_sleep(fetch_start, fetch_end)
        }
        if not DEBUG_MODE:
            ProgressIndicator.step_complete()
        
        if not DEBUG_MODE:
            ProgressIndicator.step_start("Fetching Withings weight data from API")
        # For Withings, always fetch the last 14 days including today
        from datetime import datetime, timedelta
        now = datetime.now()
        withings_fetch_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        withings_fetch_start = (now - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0)
        withings_raw = {
            'weight': self.withings.get_weight_data(withings_fetch_start, withings_fetch_end)
        }
        if not DEBUG_MODE:
            ProgressIndicator.step_complete()
            
        self.logger.debug("Withings API data fetched successfully")
        if DEBUG_MODE:
            import json
            self.logger.debug(
                "===== WITHINGS API RESPONSE =====\n" +
                json.dumps(withings_raw, indent=2) +
                "\n===== END WITHINGS API RESPONSE ====="
            )
        
        return {
            'oura': oura_raw,
            'whoop': whoop_raw,
            'withings': withings_raw
        }
    
    def generate_report(self, raw_data: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
        """Generate weekly status report.
        
        Args:
            raw_data: Raw API data
            start_date: Start date for report period
            end_date: End date for report period
            
        Returns:
            Path to generated report file
        """
        
        # Process raw data
        if not DEBUG_MODE:
            ProgressIndicator.step_start("Transforming and normalizing the data")
            
        # Process Oura data
        self.processor.oura_data = self.processor.process_oura_data(raw_data['oura'], start_date, end_date)
        
        # Process Whoop data
        self.processor.whoop_data = self.processor.process_whoop_data(raw_data['whoop'])
        
        # Process Withings data
        if 'withings' in raw_data:
            self.processor.withings_data = self.processor.process_withings_data(raw_data['withings'], start_date, end_date)
            
            # Log weight data in debug mode
            if DEBUG_MODE and self.processor.withings_data and 'weight' in self.processor.withings_data:
                weight_df = self.processor.withings_data['weight']
                self.logger.debug(f"\n===== DataFrame: Withings Weight Data =====\nShape: {weight_df.shape[0]} rows × {weight_df.shape[1]} columns\nColumns: {', '.join(weight_df.columns)}\n\n{weight_df.to_string()}\n====================================\n")
        
        if not DEBUG_MODE:
            ProgressIndicator.step_complete()
        
        # Print processed DataFrames in debug mode
        if DEBUG_MODE:
            self.logger.debug("\n===== PROCESSED DATA SUMMARY =====")
            
            # Print Oura DataFrames
            if self.processor.oura_data is not None:
                if isinstance(self.processor.oura_data, dict):
                    self.logger.debug(f"Oura data contains {len(self.processor.oura_data)} DataFrames")
                    for name, df in self.processor.oura_data.items():
                        self.logger.debug_dataframe(df, f"Oura {name}")
                elif isinstance(self.processor.oura_data, pd.DataFrame):
                    # If it's a single DataFrame, print it directly
                    self.logger.debug_dataframe(self.processor.oura_data, "Oura activity")
                else:
                    # Don't print any message about the type
                    pass
            else:
                self.logger.debug("No Oura data available")
            
            # Print Whoop DataFrames
            if self.processor.whoop_data is not None:
                if isinstance(self.processor.whoop_data, dict):
                    self.logger.debug(f"Whoop data contains {len(self.processor.whoop_data)} DataFrames")
                    for name, df in self.processor.whoop_data.items():
                        self.logger.debug_dataframe(df, f"Whoop {name}")
                else:
                    self.logger.debug(f"Whoop data is not a dictionary: {type(self.processor.whoop_data)}")
            else:
                self.logger.debug("No Whoop data available")
                
            self.logger.debug("===== END DATA SUMMARY =====")
        
        # Generate report
        if not DEBUG_MODE:
            ProgressIndicator.step_start("Converting the data into a markdown report")
        report = self.report_gen.generate_weekly_status(start_date, end_date)
        if not DEBUG_MODE:
            ProgressIndicator.step_complete()
        
        # Save report to file
        report_file = os.path.join('data', f'{end_date.strftime("%Y-%m-%d")}-weekly-status.md')
        with open(report_file, 'w') as f:
            f.write(report)
        self.logger.log_data_counts('report file', 1)
        
        if not DEBUG_MODE:
            ProgressIndicator.section_header("Report Generation Complete")
            ProgressIndicator.step_complete(f"Markdown report saved to {report_file}")
            ProgressIndicator.bullet_item("Please open with your editor and make adjustments as needed")
            ProgressIndicator.bullet_item("Run with --pdf to see the final output and --upload to create a OneDrive link")
            
        return report_file
    
    def create_pdf(self, markdown_file: str) -> str:
        """Convert markdown report to PDF.
        
        Args:
            markdown_file: Path to markdown file
            
        Returns:
            Path to generated PDF file
        """
        
        if not DEBUG_MODE:
            ProgressIndicator.step_start("Creating PDF from markdown report")
            
        pdf_file = markdown_file.replace('.md', '.pdf')
        self.converter.markdown_to_pdf(markdown_file, pdf_file)
        self.logger.log_data_counts('pdf file', 1)
        
        if not DEBUG_MODE:
            ProgressIndicator.step_complete(f"PDF saved to {pdf_file}")
            
        return pdf_file
    
    def upload_to_onedrive(self, file_paths: List[str], end_date: datetime) -> Optional[str]:
        """Upload files to OneDrive and create sharing links.
        
        Args:
            file_paths: List of files to upload
            end_date: End date for folder name
            
        Returns:
            URL of uploaded file if successful, None otherwise
        """
        
        if not DEBUG_MODE:
            ProgressIndicator.section_header("OneDrive Upload")
            
        # Create folder name with timestamp
        folder_name = f"Health Data/{end_date.strftime('%Y-%m-%d')}"
        
        # Upload files
        success_count = 0
        pdf_url = None
        
        for file_path in file_paths:
            try:
                if not DEBUG_MODE:
                    ProgressIndicator.step_start(f"Uploading {os.path.basename(file_path)}")
                    
                pdf_url = self.storage.upload_file(file_path, folder_name)
                self.logger.log_data_counts('uploaded file', 1)
                success_count += 1
                
                if not DEBUG_MODE:
                    ProgressIndicator.step_complete()
            except Exception as e:
                if not DEBUG_MODE:
                    ProgressIndicator.step_error(f"Failed: {str(e)}")
                self.logger.log_skipped_date(end_date, f"Failed to upload {os.path.basename(file_path)}: {str(e)}")
        
        if not DEBUG_MODE:
            if success_count > 0 and pdf_url:
                # Show the OneDrive link in the same section
                ProgressIndicator.step_complete(f"OneDrive link: {pdf_url}")
            else:
                ProgressIndicator.step_warning("No files were uploaded to OneDrive.")
                
        return pdf_url if success_count > 0 else None
    
    def run(self, args: argparse.Namespace) -> None:
        """Run the pipeline.
        
        Args:
            args: Command line arguments
        """
        # Get date ranges once
        report_start, report_end, fetch_start, fetch_end = DateUtils.get_date_ranges()
        self.logger.debug(f"Date ranges: report_start={report_start}, report_end={report_end}, fetch_start={fetch_start}, fetch_end={fetch_end}")
        
        # Get data and generate report
        if args.fetch:
            if not DEBUG_MODE:
                ProgressIndicator.section_header("Data Collection")
            # Fetch and process data
            raw_data = self.fetch_api_data(fetch_start, fetch_end)
            self.processor.process_raw_data(
                oura_raw=raw_data['oura'], 
                whoop_raw=raw_data['whoop'], 
                withings_raw=raw_data['withings'],
                start_date=report_start, 
                end_date=report_end
            )
            
            # Generate report
            report_file = self.generate_report(raw_data, report_start, report_end)
        
        # Convert to PDF
        if args.pdf:
            if not DEBUG_MODE:
                ProgressIndicator.section_header("PDF Conversion")
            # Get markdown file path
            report_file = DateUtils.get_report_path(report_end)
            if not os.path.exists(report_file):
                ProgressIndicator.step_error(f"Report file not found: {report_file}")
                self.logger.log_skipped_date(None, f"Report file not found: {report_file}")
                sys.exit(1)
            pdf_file = self.create_pdf(report_file)
        
        # Upload files
        if args.upload:
            # Get PDF file path
            pdf_file = DateUtils.get_report_path(report_end, extension='.pdf')
            if not os.path.exists(pdf_file):
                self.logger.log_skipped_date(None, "PDF file not found. Run with --pdf first.")
                sys.exit(1)
            
            # Upload and create sharing link
            pdf_url = self.upload_to_onedrive([pdf_file], report_end)
            if pdf_url:
                ProgressIndicator.section_header("Ready to Share")
                print("Hi Coach!")
                print(f"See this week's progress report: {pdf_url}")

