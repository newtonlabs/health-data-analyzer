"""Report generation stage for the health data pipeline."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .base_stage import PipelineStage, PipelineContext, StageResult, StageStatus
from src.pipeline.legacy_shim import MemoryBasedLegacyShim
from src.reporting.report_generator import ReportGenerator


class ReportStage(PipelineStage):
    """Stage 5: Report Generation using legacy reporting system with memory-based shim."""
    
    def __init__(self):
        """Initialize the report generation stage."""
        super().__init__("report")
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the report generation stage.
        
        This stage takes the aggregated data from the pipeline and generates
        a legacy-style report using the memory-based shim to avoid CSV I/O.
        
        Args:
            context: Pipeline context containing aggregated data
            
        Returns:
            StageResult with generated report content
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("🔄 Starting report generation stage...")
            
            # Check if we have aggregated data
            if not context.aggregated_data:
                self.logger.warning("No aggregated data available for report generation")
                return StageResult(
                    stage_name=self.stage_name,
                    status=StageStatus.SKIPPED,
                    error="No aggregated data available",
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Create memory-based shim and report generator
            shim = MemoryBasedLegacyShim(context.aggregated_data)
            report_gen = ReportGenerator(shim)  # Pass shim as analyzer
            
            # Set up date range for report (last 7 days)
            end_date = datetime.combine(context.end_date, datetime.min.time())
            start_date = end_date - timedelta(days=7)
            
            self.logger.info(f"📅 Generating report for {start_date.date()} to {end_date.date()}")
            
            # Generate the report (ReportGenerator will call shim methods)
            report_content = report_gen.generate_weekly_status(start_date, end_date)
            
            if not report_content:
                self.logger.warning("Report generation returned empty content")
                return StageResult(
                    stage_name=self.stage_name,
                    status=StageStatus.FAILED,
                    error="Report generation returned empty content",
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Store report content in result
            result_data = {
                'report_content': report_content,
                'report_length': len(report_content),
                'date_range': f"{start_date.date()} to {end_date.date()}"
            }
            
            # Always save report to file
            report_file = f"data/05_reports/health_report_{context.end_date.strftime('%Y-%m-%d')}.md"
            file_paths = {}
            try:
                import os
                os.makedirs(os.path.dirname(report_file), exist_ok=True)
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                file_paths['report'] = report_file
                self.logger.info(f"📄 Report saved to: {report_file}")
            except Exception as e:
                self.logger.warning(f"Failed to save report to file: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"✅ Report generation completed in {duration:.2f}s")
            self.logger.info(f"📊 Report length: {len(report_content)} characters")
            
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.SUCCESS,
                data=result_data,
                file_paths=file_paths,
                metrics={
                    'report_length': len(report_content),
                    'aggregated_data_types': len(context.aggregated_data),
                    'date_range_days': (context.end_date - context.start_date).days + 1
                },
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Report generation failed: {str(e)}"
            self.logger.error(error_msg)
            
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error=error_msg,
                duration_seconds=duration
            )
