"""New health data pipeline using refactored API services and extractors."""

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Optional

from src.analysis.aggregator import Aggregator
from src.analysis.processor import Processor
from src.reporting.pdf_converter import PDFConverter
from src.reporting.report_generator import ReportGenerator

# Import new services and extractors
from src.api.services import (
    WhoopService,
    OuraService, 
    WithingsService,
    HevyService,
    OneDriveService
)
from src.processing.extractors import (
    WhoopExtractor,
    OuraExtractor,
    WithingsExtractor,
    HevyExtractor
)

from src.utils.date_utils import DateUtils
from src.utils.logging_utils import HealthLogger
from src.utils.progress_indicators import ProgressIndicator


class NewWorkflow:
    """New pipeline using refactored API services and extractors."""

    def __init__(self, skip_auth: bool = False):
        """Initialize pipeline components with new architecture.

        Args:
            skip_auth: If True, skip authentication with external services
        """
        # Initialize logger
        self.logger = HealthLogger(__name__)

        # Initialize new services (pure API communication)
        self.whoop_service = WhoopService()
        self.oura_service = OuraService()
        self.withings_service = WithingsService()
        self.hevy_service = HevyService()
        self.onedrive_service = OneDriveService()

        # Initialize new extractors (pure data processing)
        self.whoop_extractor = WhoopExtractor()
        self.oura_extractor = OuraExtractor()
        self.withings_extractor = WithingsExtractor()
        self.hevy_extractor = HevyExtractor()

        # Initialize existing data processing components (unchanged)
        self.processor = Processor()
        self.aggregator = Aggregator(self.processor)
        self.report_gen = ReportGenerator(self.aggregator)
        self.converter = PDFConverter()

        # Authenticate with services if needed
        if not skip_auth:
            self._authenticate()

    def _authenticate(self):
        """Authenticate with all external services."""
        self.logger.info("Authenticating with external services...")

        # Check authentication status for each service
        services = [
            ("Whoop", self.whoop_service),
            ("Oura", self.oura_service),
            ("Withings", self.withings_service),
            ("Hevy", self.hevy_service),
            ("OneDrive", self.onedrive_service)
        ]

        for service_name, service in services:
            try:
                if not service.is_authenticated():
                    self.logger.warning(f"{service_name} not authenticated - will prompt during data fetch")
                else:
                    self.logger.info(f"✅ {service_name} authenticated")
            except Exception as e:
                self.logger.warning(f"Error checking {service_name} authentication: {e}")

    def fetch_all_data(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Fetch data from all sources using new services.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary containing raw data from all sources
        """
        self.logger.info(f"Fetching data from {start_date.date()} to {end_date.date()}")

        # Calculate fetch dates
        fetch_start = start_date
        fetch_end = end_date

        # Fetch Oura data
        ProgressIndicator.step_start("Fetching Oura data from API")
        try:
            oura_raw = {
                "activity": self.oura_service.get_activity_data(fetch_start, fetch_end),
                "resilience": self.oura_service.get_resilience_data(fetch_start, fetch_end),
            }
            self.logger.info("✅ Oura data fetched successfully")
        except Exception as e:
            self.logger.error(f"Failed to fetch Oura data: {e}")
            oura_raw = {"activity": {"data": []}, "resilience": {"data": []}}
        ProgressIndicator.step_complete()

        # Fetch Whoop data
        ProgressIndicator.step_start("Fetching Whoop data from API")
        try:
            whoop_raw = {
                "workouts": self.whoop_service.get_workouts_data(fetch_start, fetch_end),
                "recovery": self.whoop_service.get_recovery_data(fetch_start, fetch_end),
                "sleep": self.whoop_service.get_sleep_data(fetch_start, fetch_end),
            }
            self.logger.info("✅ Whoop data fetched successfully")
        except Exception as e:
            self.logger.error(f"Failed to fetch Whoop data: {e}")
            whoop_raw = {"workouts": {"data": []}, "recovery": {"data": []}, "sleep": {"data": []}}
        ProgressIndicator.step_complete()

        # Fetch Withings data
        ProgressIndicator.step_start("Fetching Withings weight data from API")
        try:
            # For Withings, always fetch the last 14 days including today
            now = datetime.now()
            withings_fetch_end = now.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            withings_fetch_start = (now - timedelta(days=13)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            withings_raw = {
                "weight": self.withings_service.get_weight_data(
                    withings_fetch_start, withings_fetch_end
                )
            }
            self.logger.info("✅ Withings data fetched successfully")
        except Exception as e:
            self.logger.error(f"Failed to fetch Withings data: {e}")
            withings_raw = {"weight": {"data": []}}
        ProgressIndicator.step_complete()

        # Fetch Hevy data
        ProgressIndicator.step_start("Fetching Hevy workout data from API")
        try:
            hevy_raw = self.hevy_service.get_workouts_data()
            self.logger.info("✅ Hevy data fetched successfully")
        except Exception as e:
            self.logger.error(f"Failed to fetch Hevy data: {e}")
            hevy_raw = {"workouts": []}
        ProgressIndicator.step_complete()

        return {
            "oura": oura_raw,
            "whoop": whoop_raw,
            "withings": withings_raw,
            "hevy": hevy_raw,
        }

    def extract_all_data(self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Extract and process data using new extractors.

        Args:
            raw_data: Raw data from all sources
            start_date: Start date for processing
            end_date: End date for processing

        Returns:
            Dictionary containing extracted and processed data
        """
        self.logger.info("Extracting and processing data using new extractors")

        extracted_data = {}

        # Extract Whoop data
        if "whoop" in raw_data:
            try:
                whoop_extracted = self.whoop_extractor.extract_all_data(
                    raw_data["whoop"], start_date, end_date
                )
                extracted_data["whoop"] = whoop_extracted
                self.logger.info("✅ Whoop data extracted successfully")
            except Exception as e:
                self.logger.error(f"Failed to extract Whoop data: {e}")

        # Extract Oura data
        if "oura" in raw_data:
            try:
                oura_extracted = self.oura_extractor.extract_all_data(
                    raw_data["oura"], start_date, end_date
                )
                extracted_data["oura"] = oura_extracted
                self.logger.info("✅ Oura data extracted successfully")
            except Exception as e:
                self.logger.error(f"Failed to extract Oura data: {e}")

        # Extract Withings data
        if "withings" in raw_data:
            try:
                withings_extracted = self.withings_extractor.extract_all_data(
                    raw_data["withings"], end_date
                )
                extracted_data["withings"] = withings_extracted
                self.logger.info("✅ Withings data extracted successfully")
            except Exception as e:
                self.logger.error(f"Failed to extract Withings data: {e}")

        # Extract Hevy data
        if "hevy" in raw_data:
            try:
                hevy_extracted = self.hevy_extractor.extract_all_data(
                    raw_data["hevy"], end_date
                )
                extracted_data["hevy"] = hevy_extracted
                self.logger.info("✅ Hevy data extracted successfully")
            except Exception as e:
                self.logger.error(f"Failed to extract Hevy data: {e}")

        return extracted_data

    def generate_report(
        self, raw_data: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> str:
        """Generate weekly status report using existing report generation.

        Args:
            raw_data: Raw data from all sources
            start_date: Start date for the report
            end_date: End date for the report

        Returns:
            Path to the generated report file
        """
        self.logger.info("Generating weekly status report")

        # Process data using existing processor (maintains compatibility)
        self.processor.process_all_data(
            whoop_raw=raw_data.get("whoop"),
            oura_raw=raw_data.get("oura"),
            withings_raw=raw_data.get("withings"),
            hevy_raw=raw_data.get("hevy"),
            start_date=start_date,
            end_date=end_date,
        )

        # Generate report using existing report generator
        report_path = self.report_gen.generate_weekly_status(start_date, end_date)
        self.logger.info(f"Report generated: {report_path}")

        return report_path

    def upload_to_onedrive(self, file_path: str, folder_name: str = None) -> str:
        """Upload file to OneDrive using new service.

        Args:
            file_path: Path to file to upload
            folder_name: Optional folder name in OneDrive

        Returns:
            OneDrive URL of uploaded file
        """
        self.logger.info(f"Uploading {file_path} to OneDrive")

        try:
            url = self.onedrive_service.upload_file(file_path, folder_name)
            self.logger.info(f"✅ File uploaded successfully: {url}")
            return url
        except Exception as e:
            self.logger.error(f"Failed to upload to OneDrive: {e}")
            raise

    def run_full_pipeline(
        self, 
        start_date: datetime, 
        end_date: datetime,
        upload_to_onedrive: bool = False,
        generate_pdf: bool = False
    ) -> dict[str, str]:
        """Run the complete pipeline with new architecture.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            upload_to_onedrive: Whether to upload results to OneDrive
            generate_pdf: Whether to generate PDF version

        Returns:
            Dictionary with paths/URLs of generated files
        """
        self.logger.info("🚀 Starting new pipeline execution")

        results = {}

        try:
            # Step 1: Fetch data using new services
            raw_data = self.fetch_all_data(start_date, end_date)

            # Step 2: Extract data using new extractors (optional - for future use)
            extracted_data = self.extract_all_data(raw_data, start_date, end_date)
            self.logger.info(f"Extracted data types: {list(extracted_data.keys())}")

            # Step 3: Generate report (using existing processor for compatibility)
            report_path = self.generate_report(raw_data, start_date, end_date)
            results["report_path"] = report_path

            # Step 4: Generate PDF if requested
            if generate_pdf:
                pdf_path = self.converter.convert_to_pdf(report_path)
                results["pdf_path"] = pdf_path
                self.logger.info(f"PDF generated: {pdf_path}")

            # Step 5: Upload to OneDrive if requested
            if upload_to_onedrive:
                folder_name = "Health Reports"
                
                # Upload markdown report
                report_url = self.upload_to_onedrive(report_path, folder_name)
                results["report_url"] = report_url

                # Upload PDF if generated
                if generate_pdf and "pdf_path" in results:
                    pdf_url = self.upload_to_onedrive(results["pdf_path"], folder_name)
                    results["pdf_url"] = pdf_url

            self.logger.info("🎉 New pipeline execution completed successfully")
            return results

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            raise


def main():
    """CLI entry point for new pipeline."""
    parser = argparse.ArgumentParser(description="New Health Data Pipeline")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--upload", action="store_true", help="Upload to OneDrive")
    parser.add_argument("--pdf", action="store_true", help="Generate PDF")
    parser.add_argument("--skip-auth", action="store_true", help="Skip authentication")

    args = parser.parse_args()

    # Calculate date range
    if args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        # Default to last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

    # Initialize and run pipeline
    workflow = NewWorkflow(skip_auth=args.skip_auth)
    results = workflow.run_full_pipeline(
        start_date=start_date,
        end_date=end_date,
        upload_to_onedrive=args.upload,
        generate_pdf=args.pdf
    )

    print("\n🎉 Pipeline Results:")
    for key, value in results.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
