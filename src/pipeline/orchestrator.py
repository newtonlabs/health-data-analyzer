"""Main pipeline orchestrator for the health data processing system."""

import time
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from src.pipeline.stages import (
    PipelineContext, StageResult, StageStatus,
    FetchStage, ExtractStage, TransformStage, AggregateStage
)
from src.utils.logging_utils import HealthLogger


class PipelineResult:
    """Result of a complete pipeline execution."""
    
    def __init__(self, context: PipelineContext, total_duration: float):
        """Initialize pipeline result.
        
        Args:
            context: Final pipeline context
            total_duration: Total execution time in seconds
        """
        self.context = context
        self.total_duration = total_duration
        self.success = all(
            result.status in [StageStatus.SUCCESS, StageStatus.PARTIAL] 
            for result in context.stage_results.values()
        )
    
    @property
    def stages_completed(self) -> int:
        """Number of stages that completed successfully."""
        return len([
            r for r in self.context.stage_results.values() 
            if r.status in [StageStatus.SUCCESS, StageStatus.PARTIAL]
        ])
    
    @property
    def total_stages(self) -> int:
        """Total number of stages executed."""
        return len(self.context.stage_results)
    
    @property
    def services_processed(self) -> Dict[str, Any]:
        """Get summary of services processed."""
        services = {}
        for service in self.context.services:
            service_data = {}
            
            # Check if service has data in each stage
            if service in self.context.raw_data:
                service_data['raw_data'] = True
            if service in self.context.extracted_data:
                service_data['extracted_data'] = True
            if service in self.context.transformed_data:
                service_data['transformed_data'] = True
                
            services[service] = service_data
        
        return services
    
    @property
    def file_paths(self) -> Dict[str, str]:
        """Get all generated file paths."""
        return self.context.file_paths


class HealthDataOrchestrator:
    """Main orchestrator for the 4-stage health data pipeline."""
    
    def __init__(self):
        """Initialize the pipeline orchestrator."""
        self.logger = HealthLogger("HealthDataOrchestrator")
        
        # Initialize pipeline stages
        self.stages = {
            'fetch': FetchStage(),
            'extract': ExtractStage(), 
            'transform': TransformStage(),
            'aggregate': AggregateStage()
        }
    
    def run_pipeline(self, days: int, services: List[str] = None, 
                    enable_csv: bool = True, debug_mode: bool = False) -> PipelineResult:
        """Run the complete 4-stage health data pipeline.
        
        Args:
            days: Number of days to process
            services: List of services to process (None for all)
            enable_csv: Whether to generate CSV files
            debug_mode: Enable debug logging
            
        Returns:
            PipelineResult with execution results
        """
        start_time = time.time()
        
        # Default services if none specified
        if services is None:
            services = ['whoop', 'oura', 'withings', 'hevy', 'nutrition']
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Create pipeline context
        context = PipelineContext(
            start_date=start_date,
            end_date=end_date,
            services=services,
            enable_csv=enable_csv,
            debug_mode=debug_mode
        )
        
        self.logger.info(f"🚀 Starting 4-stage pipeline for {days} days")
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🔧 Services: {', '.join(services)}")
        self.logger.info(f"📁 CSV generation: {'enabled' if enable_csv else 'disabled'}")
        
        # Execute pipeline stages in order
        stage_order = ['fetch', 'extract', 'transform', 'aggregate']
        
        for stage_name in stage_order:
            try:
                self.logger.info(f"🔄 Executing {stage_name} stage...")
                stage = self.stages[stage_name]
                
                stage_start = time.time()
                result = stage.execute(context)
                result.duration_seconds = time.time() - stage_start
                
                context.add_stage_result(result)
                
                if result.status == StageStatus.SUCCESS:
                    self.logger.info(f"✅ {stage_name} stage completed successfully")
                elif result.status == StageStatus.PARTIAL:
                    self.logger.warning(f"⚠️ {stage_name} stage completed with warnings: {result.error}")
                else:
                    self.logger.error(f"❌ {stage_name} stage failed: {result.error}")
                    # Continue with remaining stages even if one fails
                    
            except Exception as e:
                error_msg = f"Unexpected error in {stage_name} stage: {str(e)}"
                self.logger.error(error_msg)
                
                error_result = StageResult(
                    stage_name=stage_name,
                    status=StageStatus.FAILED,
                    error=error_msg
                )
                context.add_stage_result(error_result)
        
        total_duration = time.time() - start_time
        result = PipelineResult(context, total_duration)
        
        # Log final summary
        self._log_pipeline_summary(result)
        
        return result
    
    def run_stage(self, stage_name: str, context: PipelineContext) -> StageResult:
        """Run an individual pipeline stage.
        
        Args:
            stage_name: Name of the stage to run
            context: Pipeline context
            
        Returns:
            StageResult from stage execution
        """
        if stage_name not in self.stages:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        self.logger.info(f"🔄 Running {stage_name} stage...")
        
        stage = self.stages[stage_name]
        result = stage.execute(context)
        
        if result.status == StageStatus.SUCCESS:
            self.logger.info(f"✅ {stage_name} stage completed successfully")
        else:
            self.logger.error(f"❌ {stage_name} stage failed: {result.error}")
        
        return result
    
    def _log_pipeline_summary(self, result: PipelineResult) -> None:
        """Log a summary of the pipeline execution."""
        self.logger.info("🎯 PIPELINE EXECUTION SUMMARY")
        self.logger.info("=" * 40)
        
        # Overall status
        status_icon = "🎉" if result.success else "⚠️"
        self.logger.info(f"{status_icon} Overall Status: {'SUCCESS' if result.success else 'PARTIAL/FAILED'}")
        self.logger.info(f"⏱️ Total Duration: {result.total_duration:.2f} seconds")
        self.logger.info(f"📊 Stages Completed: {result.stages_completed}/{result.total_stages}")
        
        # Stage-by-stage results
        self.logger.info("\n📋 Stage Results:")
        for stage_name, stage_result in result.context.stage_results.items():
            status_icon = {
                StageStatus.SUCCESS: "✅",
                StageStatus.PARTIAL: "⚠️", 
                StageStatus.FAILED: "❌",
                StageStatus.SKIPPED: "⏭️"
            }.get(stage_result.status, "❓")
            
            duration_info = f" ({stage_result.duration_seconds:.2f}s)" if stage_result.duration_seconds > 0 else ""
            self.logger.info(f"   {status_icon} {stage_name.title()}: {stage_result.status.value}{duration_info}")
            
            if stage_result.error:
                self.logger.info(f"      Error: {stage_result.error}")
        
        # Services processed
        services_processed = result.services_processed
        self.logger.info(f"\n🔧 Services Processed: {len(services_processed)}")
        for service, service_data in services_processed.items():
            stages_completed = len([k for k, v in service_data.items() if v])
            self.logger.info(f"   📊 {service.title()}: {stages_completed}/3 stages")
        
        # Files generated
        if result.context.enable_csv and result.file_paths:
            self.logger.info(f"\n📁 Files Generated: {len(result.file_paths)}")
            for file_type, file_path in result.file_paths.items():
                self.logger.info(f"   📄 {file_type}: {file_path}")
        
        self.logger.info("=" * 40)
