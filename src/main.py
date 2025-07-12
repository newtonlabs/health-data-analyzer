"""Lightweight health data pipeline CLI."""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.pipeline.orchestrator import HealthDataOrchestrator
from src.reporting.pdf_converter import PDFConverter
from src.utils.progress_indicators import ProgressIndicator, Colors

def fetch_data(days: int = 8) -> None:
    """Fetch health data and generate report.
    
    Args:
        days: Number of days to fetch data for
    """
    ProgressIndicator.section_header("Health Data Pipeline")
    
    try:
        # Initialize orchestrator
        ProgressIndicator.step_start("Initializing pipeline...")
        orchestrator = HealthDataOrchestrator()
        ProgressIndicator.step_complete("Pipeline initialized")
        
        # Run pipeline
        ProgressIndicator.step_start(f"Fetching {days} days of health data...")
        result = orchestrator.run_pipeline(
            days=days,
            services=['whoop', 'oura', 'withings', 'hevy', 'nutrition'],
            enable_csv=True,
            enable_report=True
        )
        ProgressIndicator.step_complete(f"Pipeline completed in {result.total_duration:.2f}s")
        
        # Show results
        ProgressIndicator.step_complete(f"Stages completed: {result.stages_completed}/{result.total_stages}")
        ProgressIndicator.step_complete(f"Services processed: {len(result.services_processed)}")
        
        # Find generated report
        reports_dir = Path("data/05_reports")
        if reports_dir.exists():
            md_files = list(reports_dir.glob("health_report_*.md"))
            if md_files:
                latest_report = max(md_files, key=lambda f: f.stat().st_mtime)
                ProgressIndicator.step_complete(f"Report generated: {latest_report.name}")
            else:
                ProgressIndicator.step_warning("No report files found")
        
    except Exception as e:
        ProgressIndicator.step_error(f"Pipeline failed: {e}")
        sys.exit(1)


def convert_to_pdf() -> None:
    """Convert the latest markdown report to PDF."""
    ProgressIndicator.section_header("PDF Generation")
    
    try:
        # Find latest report
        ProgressIndicator.step_start("Looking for latest report...")
        reports_dir = Path("data/05_reports")
        
        if not reports_dir.exists():
            ProgressIndicator.step_error("Reports directory not found. Run 'fetch' first.")
            sys.exit(1)
        
        md_files = list(reports_dir.glob("health_report_*.md"))
        if not md_files:
            ProgressIndicator.step_error("No markdown reports found. Run 'fetch' first.")
            sys.exit(1)
        
        latest_report = max(md_files, key=lambda f: f.stat().st_mtime)
        ProgressIndicator.step_complete(f"Found report: {latest_report.name}")
        
        # Convert to PDF
        ProgressIndicator.step_start("Converting to PDF...")
        pdf_converter = PDFConverter()
        pdf_path = pdf_converter.markdown_to_pdf(
            str(latest_report), 
            str(latest_report).replace('.md', '.pdf')
        )
        
        # Get file size
        pdf_file = Path(pdf_path)
        file_size = pdf_file.stat().st_size
        size_kb = file_size / 1024
        
        ProgressIndicator.step_complete(f"PDF generated: {pdf_file.name} ({size_kb:,.0f} KB)")
        
    except Exception as e:
        ProgressIndicator.step_error(f"PDF generation failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the health data pipeline CLI."""
    parser = argparse.ArgumentParser(
        description="Lightweight Health Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python src/main.py --fetch          # Fetch 8 days of data and generate report
  python src/main.py --fetch --days 3 # Fetch 3 days of data
  python src/main.py --pdf            # Convert latest report to PDF
  python src/main.py --fetch --pdf    # Fetch data and convert to PDF"""
    )
    
    # Add flag arguments
    parser.add_argument(
        '--fetch', 
        action='store_true', 
        help='Fetch health data and generate report'
    )
    parser.add_argument(
        '--pdf', 
        action='store_true', 
        help='Convert latest markdown report to PDF'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=8, 
        help='Number of days to fetch (default: 8, only used with --fetch)'
    )
    
    args = parser.parse_args()
    
    # Show help if no flags provided
    if not args.fetch and not args.pdf:
        parser.print_help()
        return
    
    # Execute commands
    if args.fetch:
        fetch_data(args.days)
    
    if args.pdf:
        convert_to_pdf()


if __name__ == "__main__":
    main()
