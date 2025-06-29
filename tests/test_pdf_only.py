#!/usr/bin/env python3
"""
Standalone script to generate PDF from existing markdown report.
Usage: python tests/test_pdf_only.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.reporting.pdf_converter import PDFConverter


def main():
    """Generate PDF from existing markdown report."""
    
    # Define paths
    reports_dir = Path("data/05_reports")
    markdown_file = reports_dir / "health_report_2025-06-29.md"
    pdf_file = reports_dir / "health_report_2025-06-29.pdf"
    
    # Check if markdown file exists
    if not markdown_file.exists():
        print(f"❌ Markdown file not found: {markdown_file}")
        print("Run the full pipeline first to generate the markdown report.")
        return 1
    
    print(f"📄 Converting {markdown_file.name} to PDF...")
    
    try:
        # Initialize PDF converter
        converter = PDFConverter()
        
        # Convert markdown to PDF
        converter.markdown_to_pdf(str(markdown_file), str(pdf_file))
        
        # Check if PDF was created successfully
        if pdf_file.exists():
            size = pdf_file.stat().st_size
            print(f"✅ PDF generated successfully: {pdf_file.name} ({size:,} bytes)")
            return 0
        else:
            print("❌ PDF generation failed - file not created")
            return 1
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
