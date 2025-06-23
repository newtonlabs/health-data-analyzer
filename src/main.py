"""Main script to collect and combine health data from multiple sources."""

# Suppress all warnings
import warnings
warnings.simplefilter("ignore")

# Standard library imports
import argparse
import logging
import sys
from pathlib import Path

# Third-party imports
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.pipeline import Workflow
from src.utils.logging_utils import configure_logging
from src.utils.progress_indicators import Colors, ProgressIndicator

# Load environment variables
load_dotenv()


def get_version() -> str:
    """Get the application version from version.txt file.

    Returns:
        The version string from version.txt, or '0.0.0' if file not found
    """
    try:
        version_file = Path(__file__).parent.parent / "version.txt"
        with open(version_file) as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"


def display_welcome_banner() -> None:
    """Display a welcome banner with application information."""
    app_name = "Health Data Analyzer"
    version = get_version()
    banner = f"""
{Colors.BLUE}{Colors.BOLD}{app_name} v{version}{Colors.RESET}
{'=' * (len(app_name) + len(version) + 3)}
"""
    ProgressIndicator.bullet_item(banner)


def main() -> None:
    """Main entry point."""
    # Display welcome banner
    display_welcome_banner()

    parser = argparse.ArgumentParser(description="Health Data Pipeline")
    parser.add_argument(
        "--fetch", action="store_true", help="Fetch new data and generate report"
    )
    parser.add_argument("--pdf", action="store_true", help="Convert report to PDF")
    parser.add_argument("--upload", action="store_true", help="Upload PDF to OneDrive")
    # Debug mode removed in favor of LOG_LEVEL environment variable

    args = parser.parse_args()

    # Default to help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Configure logging based on LOG_LEVEL environment variable
    configure_logging()

    # Skip authentication if only PDF conversion is requested
    skip_auth = args.pdf and not (args.fetch or args.upload)

    # Run pipeline with progress indicators
    try:
        workflow = Workflow(skip_auth=skip_auth)
        workflow.run(args)
        # Show success message at the end
        if args.fetch or args.pdf or args.upload:
            ProgressIndicator.print_message(
                f"\n{Colors.GREEN}Process completed successfully!{Colors.RESET}"
            )
    except KeyboardInterrupt:
        ProgressIndicator.bullet_item(
            f"{Colors.YELLOW}Process interrupted by user.{Colors.RESET}"
        )
    except Exception as e:
        ProgressIndicator.bullet_item(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        # Always raise exception for debugging
        raise


if __name__ == "__main__":
    main()
