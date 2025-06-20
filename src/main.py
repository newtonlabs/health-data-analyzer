"""Main script to collect and combine health data from multiple sources."""
# Suppress all warnings
import warnings
warnings.simplefilter('ignore')

import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
import sys
sys.path.insert(0, project_root)

from src.pipeline import HealthPipeline
from src.utils.logging_utils import set_debug_mode

# Load environment variables
load_dotenv()

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Health Data Pipeline')
    parser.add_argument('--fetch', action='store_true', help='Fetch new data and generate report')
    parser.add_argument('--pdf', action='store_true', help='Convert report to PDF')
    parser.add_argument('--upload', action='store_true', help='Upload PDF to OneDrive')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with verbose logging')
    
    args = parser.parse_args()
    
    # Default to help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Configure logging based on debug flag
    set_debug_mode(args.debug)
    
    # Skip authentication if only PDF conversion is requested
    skip_auth = args.pdf and not (args.fetch or args.upload)
    
    # Run pipeline
    pipeline = HealthPipeline(skip_auth=skip_auth)
    pipeline.run(args)

if __name__ == "__main__":
    main()
